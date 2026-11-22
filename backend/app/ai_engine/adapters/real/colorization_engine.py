"""Real colorization engine adapter backed by the local SUMI U-Net (F08).

Implements the ``ColorizationEngine`` protocol. Loads a trained U-Net
checkpoint from disk (CPU only) and runs tiled inference with overlap
blending. When the checkpoint is unavailable it records the error and
every subsequent :meth:`colorize` call raises :class:`ModelUnavailableError`
with a clear message -- no silent fallback to mock behavior.

The checkpoint path is resolved from the ``SUMI_COLORIZATION_CHECKPOINT``
environment variable, falling back to
``artifacts/checkpoints/sumi_unet_cpu_v1/best.pt`` relative to the repo
root. Results are written to ``artifacts/results/`` (metadata only -- no
binary images in PostgreSQL).
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Optional


def _find_repo_root(start: str) -> str:
    """Sube directorios hasta encontrar el marcador del repo (.git)."""
    cur = os.path.abspath(start)
    for _ in range(10):
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        nxt = os.path.dirname(cur)
        if nxt == cur:
            break
        cur = nxt
    # Fallback: asumir 6 niveles arriba desde este archivo.
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
        )
    )


REPO_ROOT = _find_repo_root(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Las dependencias pesadas se importan de forma opcional para que el
# módulo se pueda cargar en entornos donde no estén disponibles
# (por ejemplo, el contenedor Docker sin el código ML completo).
try:
    import cv2  # noqa: F401
    import numpy as np  # noqa: F401
    import torch  # noqa: F401

    _HEAVY_DEPS_AVAILABLE = True
except Exception:  # pragma: no cover - optional heavy deps
    _HEAVY_DEPS_AVAILABLE = False
    torch = None  # type: ignore

try:
    import onnxruntime as ort  # noqa: F401

    _ORT_AVAILABLE = True
except Exception:  # pragma: no cover - optional heavy dep
    _ORT_AVAILABLE = False
    ort = None  # type: ignore

from app.core.logging import get_logger

logger = get_logger(__name__)

try:  # pragma: no cover - optional ML code
    ml_path = os.path.join(REPO_ROOT, "ml")
    sys.path.insert(0, ml_path)
    from models.unet.unet import SmallUNet  # noqa: F401

    _ML_MODEL_AVAILABLE = True
    logger.info("ML model code cargado desde: %s", ml_path)
except Exception as exc:  # pragma: no cover - optional ML code
    SmallUNet = None  # type: ignore
    _ML_MODEL_AVAILABLE = False
    logger.error(
        "No se pudo importar ml/models/unet/unet.py desde %s: %s",
        os.path.join(REPO_ROOT, "ml"),
        exc,
    )

from app.ai_engine.adapters.real import ModelUnavailableError  # noqa: E402
from app.ai_engine.contracts import ColorizationEngine  # noqa: E402

DEFAULT_CHECKPOINT_REL = os.path.join("artifacts", "checkpoints", "sumi_unet_cpu_v1", "best.pt")
DEFAULT_RESULTS_DIR = os.path.join("artifacts", "results")


def _resolve_checkpoint() -> str:
    env = os.environ.get("SUMI_COLORIZATION_CHECKPOINT")
    if env:
        return env
    return os.path.join(REPO_ROOT, DEFAULT_CHECKPOINT_REL)


def _resolve_results_dir() -> str:
    env = os.environ.get("SUMI_COLORIZATION_RESULTS_DIR")
    if env:
        return env
    return os.path.join(REPO_ROOT, DEFAULT_RESULTS_DIR)


def _resolve_image_path(image_path: str) -> str:
    """Resuelve una ruta de imagen, probando la ruta dada y luego bajo STORAGE_ROOT."""
    if os.path.exists(image_path):
        return image_path
    storage_root = os.environ.get("STORAGE_ROOT", "data")
    candidate = os.path.join(storage_root, image_path)
    if os.path.exists(candidate):
        return candidate
    # También intentar bajo REPO_ROOT por si acaso
    candidate2 = os.path.join(REPO_ROOT, image_path)
    if os.path.exists(candidate2):
        return candidate2
    return image_path


def _read_gray(image_path: str) -> np.ndarray:
    resolved = _resolve_image_path(image_path)
    img = cv2.imread(resolved, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"No se pudo leer la imagen: {image_path} (resuelta: {resolved})")
    return img


def _blend_window(tile_size: int, overlap: int) -> np.ndarray:
    w = np.ones((tile_size, tile_size), dtype=np.float32)
    if overlap > 0:
        ramp = np.linspace(0.0, 1.0, overlap)
        w[:, :overlap] *= ramp[None, :]
        w[:, -overlap:] *= ramp[::-1][None, :]
        w[:overlap, :] *= ramp[:, None]
        w[-overlap:, :] *= ramp[::-1][:, None]
    return w


def _predict_full(
    model: SmallUNet,
    image_path: str,
    tile_size: int,
    overlap: int,
    device: "torch.device",
) -> np.ndarray:
    inp_gray = _read_gray(image_path)
    h, w = inp_gray.shape
    inp_f = inp_gray.astype(np.float32) / 255.0

    out_acc = np.zeros((h, w, 3), dtype=np.float32)
    w_acc = np.zeros((h, w, 3), dtype=np.float32)
    win = _blend_window(tile_size, overlap)
    win3 = np.stack([win, win, win], axis=-1)

    step = tile_size - overlap
    ys = list(range(0, max(1, h - tile_size + 1), step))
    if not ys or ys[-1] + tile_size < h:
        ys.append(max(0, h - tile_size))
    xs = list(range(0, max(1, w - tile_size + 1), step))
    if not xs or xs[-1] + tile_size < w:
        xs.append(max(0, w - tile_size))

    with torch.no_grad():
        for y in ys:
            for x in xs:
                tile = inp_f[y : y + tile_size, x : x + tile_size]
                th, tw = tile.shape
                if th < tile_size or tw < tile_size:
                    padded = np.zeros((tile_size, tile_size), dtype=np.float32)
                    padded[:th, :tw] = tile
                    tile = padded
                t = torch.from_numpy(tile).unsqueeze(0).unsqueeze(0).to(device)
                pred = model(t)
                pred_np = pred.squeeze(0).permute(1, 2, 0).cpu().numpy()
                if th < tile_size or tw < tile_size:
                    pred_np = pred_np[:th, :tw, :]
                    win_crop = win[:th, :tw]
                    win3_crop = np.stack([win_crop, win_crop, win_crop], axis=-1)
                else:
                    win3_crop = win3
                out_acc[y : y + th, x : x + tw, :] += pred_np * win3_crop
                w_acc[y : y + th, x : x + tw, :] += win3_crop

    w_acc = np.clip(w_acc, 1e-6, None)
    out = np.clip(out_acc / w_acc, 0.0, 1.0)
    return (out * 255.0).round().astype(np.uint8)


def _build_onnx_input(
    gray_img: np.ndarray | None = None,
    hint_channels: list[np.ndarray] | None = None,
    sam_level0: Optional[np.ndarray] = None,
    sam_level1: Optional[np.ndarray] = None,
    wd14_embedding: Optional[np.ndarray] = None,
    image_path: str | None = None,
    input_names: list[str] | None = None,
) -> Dict[str, np.ndarray]:
    """Construye el diccionario de inputs que espera el modelo ONNX.

    Soporta dos tipos de modelos ONNX:

    1. v6_generator (4 inputs separados):
       - "L_bw": tensor (1, 1, height, width)
       - "sam_level0": tensor (1, 256, sam_h0, sam_w0)
       - "sam_level1": tensor (1, 256, sam_h1, sam_w1)
       - "wd14_embedding": tensor (1, 1024)

    2. sketch_and_hints (1 input de 5 canales):
       - "sketch_and_hints": tensor (1, 5, height, width)
         canal 0 = sketch, canales 1-2 = SAM levels, canales 3-4 = WD14

    Si no se proporcionan SAM/WD14, se rellenan con ceros para evitar
    el error "Required inputs ... are missing from input feed" de ONNX runtime.

    Si ``gray_img`` es None, se lee la imagen desde ``image_path`` usando
    :func:`_read_gray`. Se requiere al menos uno de los dos.

    ``input_names``, cuando se proporciona, restringe los outputs a solo
    los nombres que el modelo espera realmente (inspeccionados de la sesión
    ONNX). Cuando es None, se construyen ambos tipos para retrocompatibilidad.

    Retorna un diccionario mapping nombre del input -> array numpy.
    """
    if gray_img is None:
        if image_path is None:
            raise ValueError("Se requiere gray_img o image_path para construir los inputs ONNX")
        gray_img = _read_gray(image_path)

    h, w = gray_img.shape
    sketch = gray_img.astype(np.float32) / 255.0  # (h, w)

    # Determinar qué tipo de modelo es basado en input_names
    input_names_set = set(input_names or [])
    is_sketch_hints = "sketch_and_hints" in input_names_set
    is_v6_generator = any(
        n in input_names_set for n in ("L_bw", "sam_level0", "sam_level1", "wd14_embedding")
    )

    # Si no se especificó input_names, asumir v6_generator (comportamiento por defecto)
    if not input_names_set:
        is_v6_generator = True

    inputs: Dict[str, np.ndarray] = {}

    if is_sketch_hints and not is_v6_generator:
        # Modelo sketch_and_hints: tensor (1, 5, h, w)
        channels = np.zeros((5, h, w), dtype=np.float32)
        channels[0] = sketch

        if sam_level0 is not None:
            sam0 = cv2.resize(sam_level0, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            if sam0.max() > 1.0:
                sam0 = sam0 / 255.0
            channels[1] = sam0

        if sam_level1 is not None:
            sam1 = cv2.resize(sam_level1, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            if sam1.max() > 1.0:
                sam1 = sam1 / 255.0
            channels[2] = sam1

        if wd14_embedding is not None:
            wd14 = np.asarray(wd14_embedding, dtype=np.float32).flatten()
            if wd14.size >= 2:
                channels[3] = (
                    wd14[: h * w].reshape(h, w)
                    if wd14.size >= h * w
                    else np.resize(wd14[:2], (h, w))
                )
                channels[4] = wd14[1:2] if wd14.size > 1 else np.zeros((h, w), dtype=np.float32)
            elif wd14.size == 1:
                channels[3] = np.full((h, w), wd14[0], dtype=np.float32)
                channels[4] = np.zeros((h, w), dtype=np.float32)

        inputs["sketch_and_hints"] = np.expand_dims(channels, axis=0)  # (1, 5, h, w)

    else:
        # Modelo v6_generator: 4 inputs separados
        # L_bw: (1, 1, h, w)
        l_bw = np.expand_dims(np.expand_dims(sketch, axis=0), axis=0)  # (1, 1, h, w)

        # sam_level0: (1, 256, h, w) o ceros si no se proporciona
        if sam_level0 is not None:
            sam0 = cv2.resize(sam_level0, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            if sam0.max() > 1.0:
                sam0 = sam0 / 255.0
            sam0 = np.expand_dims(np.expand_dims(sam0, axis=0), axis=0)
            sam0 = np.repeat(sam0, 256, axis=1)  # (1, 256, h, w)
        else:
            sam0 = np.zeros((1, 256, h, w), dtype=np.float32)

        # sam_level1: (1, 256, h, w) o ceros si no se proporciona
        if sam_level1 is not None:
            sam1 = cv2.resize(sam_level1, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            if sam1.max() > 1.0:
                sam1 = sam1 / 255.0
            sam1 = np.expand_dims(np.expand_dims(sam1, axis=0), axis=0)
            sam1 = np.repeat(sam1, 256, axis=1)  # (1, 256, h, w)
        else:
            sam1 = np.zeros((1, 256, h, w), dtype=np.float32)

        # wd14_embedding: (1, 1024) o ceros si no se proporciona
        if wd14_embedding is not None:
            wd14 = np.asarray(wd14_embedding, dtype=np.float32).flatten()
            if wd14.size != 1024:
                wd14_adj = np.zeros(1024, dtype=np.float32)
                n = min(wd14.size, 1024)
                wd14_adj[:n] = wd14[:n]
                wd14 = wd14_adj
            wd14 = wd14.reshape(1, 1024)  # (1, 1024)
        else:
            wd14 = np.zeros((1, 1024), dtype=np.float32)

        inputs = {
            "L_bw": l_bw,
            "sam_level0": sam0,
            "sam_level1": sam1,
            "wd14_embedding": wd14,
        }

    return inputs


def _predict_full_onnx(
    session: ort.InferenceSession,  # type: ignore[name-defined]
    image_path: str,
    tile_size: int,
    overlap: int,
    inputs: Dict[str, np.ndarray],
) -> np.ndarray:
    """Run ONNX inference on ``image_path``.

    Soporta dos tipos de modelos ONNX:

    1. v6_generator (4 inputs separados): L_bw, sam_level0, sam_level1, wd14_embedding
    2. sketch_and_hints (1 input de 5 canales): sketch_and_hints

    Para evitar errores de concatenación interna en el modelo U-Net
    (dimensiones incompatibles en skip connections), las dimensiones
    espaciales se ajustan a múltiplos de 32 con padding antes de la
    inferencia, y el output se recorta al tamaño original.

    Los inputs SAM y WD14 son globales (no se tilean). Se ejecuta una
    sola pasada sobre la imagen completa.
    """
    inp_gray = _read_gray(image_path)
    h, w = inp_gray.shape

    # Determinar tipo de modelo basado en las claves de inputs
    input_names = list(inputs.keys())
    any(n in input_names for n in ("L_bw", "sam_level0", "sam_level1", "wd14_embedding"))

    # Ajustar dimensiones a múltiplos de 32 para evitar errores de concat interna
    # en skip connections del U-Net (dimensiones incompatibles tras downsampling)
    mult = 32
    padded_h = ((h + mult - 1) // mult) * mult
    padded_w = ((w + mult - 1) // mult) * mult

    needs_padding = padded_h != h or padded_w != w

    if needs_padding:
        run_inputs: Dict[str, np.ndarray] = {}
        for name, arr in inputs.items():
            if arr.ndim == 4 and arr.shape[2] == h and arr.shape[3] == w:
                # Input espacial (1, C, h, w) — aplicar padding
                padded = np.zeros((1, arr.shape[1], padded_h, padded_w), dtype=np.float32)
                padded[:, :, :h, :w] = arr
                run_inputs[name] = padded
            elif arr.ndim == 4 and arr.shape[1] == h and arr.shape[2] == w:
                # Input espacial (1, h, w, C) — aplicar padding
                padded = np.zeros((1, padded_h, padded_w, arr.shape[3]), dtype=np.float32)
                padded[:, :h, :w, :] = arr
                run_inputs[name] = padded
            else:
                # Input no espacial (ej. wd14_embedding (1, 1024)) — dejar como está
                run_inputs[name] = arr
    else:
        run_inputs = inputs

    # Ejecutar inferencia en una sola pasada con todos los inputs
    pred = session.run(None, run_inputs)[0]

    # Procesar output: (1, 3, h, w) -> (h, w, 3)
    if pred.ndim == 4:
        pred_np = pred.squeeze(0).transpose(1, 2, 0)  # (3, h, w) -> (h, w, 3)
    elif pred.ndim == 3:
        pred_np = pred.transpose(1, 2, 0) if pred.shape[2] == 3 else pred
    else:
        pred_np = pred

    # Recortar al tamaño original si hubo padding
    if needs_padding:
        pred_np = pred_np[:h, :w, :]

    # Asegurar rango [0, 255]
    out = np.clip(pred_np, 0.0, 1.0)
    return (out * 255.0).round().astype(np.uint8)


class RealColorizationEngine(ColorizationEngine):
    """Real implementation backed by the local SUMI U-Net checkpoint (.pt) or ONNX model (.onnx)."""

    MODEL_NAME: str = "sumi_unet_cpu"
    MODEL_PATH: str = _resolve_checkpoint()

    def __init__(
        self,
        checkpoint_path: str | None = None,
        model_version: str | None = None,
        model_format: str | None = None,
    ) -> None:
        self._checkpoint_path = checkpoint_path or _resolve_checkpoint()
        self._model_version = model_version
        self._model_format = model_format or self._detect_format(self._checkpoint_path)
        self._model: SmallUNet | None = None
        self._onnx_session: ort.InferenceSession | None = None  # type: ignore[attr-defined]
        self._load_error: str | None = None
        self._loaded: bool = False
        self._device = torch.device("cpu") if _HEAVY_DEPS_AVAILABLE else None  # type: ignore
        self._tile_size = 256
        self._overlap = 32
        self.load_model()

    @staticmethod
    def _detect_format(path: str) -> str:
        """Detect model format from file extension."""
        return "onnx" if path.lower().endswith(".onnx") else "pt"

    def load_model(self) -> bool:
        """Attempt to load the local model checkpoint (.pt) or ONNX model (.onnx). Returns True/False."""
        if self._model_format == "onnx":
            return self._load_onnx_model()
        if not _HEAVY_DEPS_AVAILABLE:
            self._loaded = False
            self._model = None
            self._load_error = (
                "Heavy dependencies (torch, numpy, opencv) are not available "
                "in this environment. The real colorization engine cannot run."
            )
            logger.error(self._load_error)
            return False
        if not _ML_MODEL_AVAILABLE or SmallUNet is None:
            self._loaded = False
            self._model = None
            self._load_error = (
                "ML model code (ml/models/unet/unet.py) is not available "
                "in this environment. The real colorization engine cannot run."
            )
            logger.error(self._load_error)
            return False
        try:
            self._load_real_model()
        except Exception as exc:  # noqa: BLE001
            self._loaded = False
            self._model = None
            self._load_error = f"{type(exc).__name__}: {exc}"
            logger.error("Error cargando modelo de colorización: %s", exc)
            return False
        self._loaded = True
        logger.info("Modelo de colorización cargado: %s", self._checkpoint_path)
        return True

    def _load_onnx_model(self) -> bool:
        """Load an ONNX model using onnxruntime."""
        if not _ORT_AVAILABLE or ort is None:
            self._loaded = False
            self._onnx_session = None
            self._load_error = (
                "onnxruntime is not available in this environment. "
                "The ONNX colorization engine cannot run."
            )
            logger.error(self._load_error)
            return False
        if not os.path.exists(self._checkpoint_path):
            self._loaded = False
            self._onnx_session = None
            self._load_error = (
                f"ONNX model not found at {self._checkpoint_path}. "
                "Register a valid ONNX model first."
            )
            logger.error(self._load_error)
            return False
        try:
            self._onnx_session = ort.InferenceSession(
                self._checkpoint_path,
                providers=["CPUExecutionProvider"],
            )
            self._loaded = True
            self._load_error = None
            logger.info("Modelo ONNX de colorización cargado: %s", self._checkpoint_path)
            return True
        except Exception as exc:  # noqa: BLE001
            self._loaded = False
            self._onnx_session = None
            self._load_error = f"{type(exc).__name__}: {exc}"
            logger.error("Error cargando modelo ONNX de colorización: %s", exc)
            return False

    def _load_real_model(self) -> None:
        checkpoint_path = self._checkpoint_path
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(
                f"Checkpoint not found at {checkpoint_path}. "
                "Train the model first (scripts/train_unet.py) or set "
                "SUMI_COLORIZATION_CHECKPOINT."
            )
        ckpt = torch.load(checkpoint_path, map_location=self._device, weights_only=True)
        cfg = ckpt.get("config", {})
        model_cfg = cfg.get("model", {})
        model = SmallUNet(
            in_channels=model_cfg.get("input_channels", 1),
            out_channels=model_cfg.get("target_channels", 3),
            base_channels=model_cfg.get("base_channels", 32),
            depth=model_cfg.get("depth", 4),
            output_activation=model_cfg.get("output_activation", "sigmoid"),
        ).to(self._device)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()
        self._model = model

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )
        if self._model_format == "onnx" and self._onnx_session is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "onnx session not loaded",
            )
        if self._model_format == "pt" and self._model is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )

    def colorize(
        self,
        *,
        image_path: str,
        mask_references: list[str],
        palette: dict,
        sam_level0: Optional[np.ndarray] = None,
        sam_level1: Optional[np.ndarray] = None,
        wd14_embedding: Optional[np.ndarray] = None,
    ) -> Dict:
        """Run tiled U-Net inference on ``image_path`` and persist the result.

        For PyTorch (.pt) models this is unconditional (learns directly from
        line art). For ONNX (.onnx) models, the following optional inputs
        are used to build the 5-channel sketch_and_hints input:
        - ``sam_level0``: output del encoder SAM nivel 0
        - ``sam_level1``: output del encoder SAM nivel 1
        - ``wd14_embedding``: embedding del modelo WD14

        Cuando estos inputs son None, el engine los rellena con ceros,
        evitando el error "Required inputs ... are missing from input feed".

        Args:
            image_path: Path to the input image (line art/grayscale).
            mask_references: List of mask reference paths (used for hint channels).
            palette: Color palette parameters (JSON-serializable).
            sam_level0: Output del encoder SAM nivel 0 (opcional).
            sam_level1: Output del encoder SAM nivel 1 (opcional).
            wd14_embedding: Embedding WD14 (opcional).

        Returns:
            Dict con ruta_resultado, version_modelo y parametros.
        """
        try:
            self._ensure_loaded()

            # Construir diccionario de inputs para el modelo ONNX
            # Inspeccionar los inputs del modelo para saber qué tipo es
            # (v6_generator: 4 inputs separados, sketch_and_hints: 1 input de 5 canales)
            onnx_input_names = [inp.name for inp in self._onnx_session.get_inputs()]
            onnx_inputs = _build_onnx_input(
                gray_img=None,
                image_path=image_path,
                hint_channels=mask_references,
                sam_level0=sam_level0,
                sam_level1=sam_level1,
                wd14_embedding=wd14_embedding,
                input_names=onnx_input_names,
            )

            logger.info(
                "Iniciando inferencia de colorización: %s (formato: %s, inputs: %s)",
                image_path,
                self._model_format,
                list(onnx_inputs.keys()),
            )
            t0 = time.time()

            if self._model_format == "onnx":
                out_rgb = _predict_full_onnx(
                    self._onnx_session,
                    image_path,
                    self._tile_size,
                    self._overlap,
                    inputs=onnx_inputs,
                )
            else:
                # Para modelos PyTorch, los inputs opcionales no se usan
                out_rgb = _predict_full(
                    self._model,
                    image_path,
                    self._tile_size,
                    self._overlap,
                    self._device,
                )
            infer_s = time.time() - t0

            os.makedirs(_resolve_results_dir(), exist_ok=True)
            base = os.path.splitext(os.path.basename(image_path))[0]
            out_name = f"{base}_{self.MODEL_NAME}_colorizado.png"
            out_path = os.path.join(_resolve_results_dir(), out_name)
            cv2.imwrite(out_path, cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR))

            meta_path = out_path.rsplit(".", 1)[0] + ".meta.json"
            metadata = {
                "input_path": image_path,
                "output_path": out_path,
                "model": self.MODEL_NAME,
                "checkpoint": self._checkpoint_path,
                "tile_size": self._tile_size,
                "overlap": self._overlap,
                "inference_seconds": round(infer_s, 4),
                "width": int(out_rgb.shape[1]),
                "height": int(out_rgb.shape[0]),
                "timestamp": datetime.now().isoformat(),
            }
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(metadata, fh, ensure_ascii=False, indent=2)

            logger.info(
                "Colorización completada: %s (%.2fs, %dx%d)",
                out_path,
                infer_s,
                out_rgb.shape[1],
                out_rgb.shape[0],
            )
            return {
                "ruta_resultado": out_path,
                "version_modelo": self._model_version or self.MODEL_NAME,
                "parametros": {
                    "checkpoint": self._checkpoint_path,
                    "tile_size": self._tile_size,
                    "overlap": self._overlap,
                    "device": str(self._device),
                    "inference_seconds": round(infer_s, 4),
                },
            }
        except ModelUnavailableError:
            raise
        except Exception as exc:  # pragma: no cover - inference failure path
            logger.exception("Error en inferencia de colorización para %s: %s", image_path, exc)
            raise
