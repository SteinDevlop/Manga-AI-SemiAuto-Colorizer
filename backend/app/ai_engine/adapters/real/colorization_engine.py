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
import math
import os
import sys
import time
from datetime import datetime
from typing import Dict, Tuple

import cv2
import numpy as np
import torch

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
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
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

DEFAULT_CHECKPOINT_REL = os.path.join(
    "artifacts", "checkpoints", "sumi_unet_cpu_v1", "best.pt"
)
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
    device: torch.device,
) -> np.ndarray:
    inp_gray = _read_gray(image_path)
    h, w = inp_gray.shape
    inp_f = (inp_gray.astype(np.float32) / 255.0)

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
                t = (
                    torch.from_numpy(tile)
                    .unsqueeze(0)
                    .unsqueeze(0)
                    .to(device)
                )
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


class RealColorizationEngine(ColorizationEngine):
    """Real implementation backed by the local SUMI U-Net checkpoint."""

    MODEL_NAME: str = "sumi_unet_cpu"
    MODEL_PATH: str = _resolve_checkpoint()

    def __init__(self) -> None:
        self._model: SmallUNet | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self._device = torch.device("cpu") if _HEAVY_DEPS_AVAILABLE else None  # type: ignore
        self._tile_size = 256
        self._overlap = 32
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the local U-Net checkpoint. Returns True/False."""
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
        logger.info("Modelo de colorización cargado: %s", self.MODEL_PATH)
        return True

    def _load_real_model(self) -> None:
        checkpoint_path = _resolve_checkpoint()
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(
                f"Checkpoint not found at {checkpoint_path}. "
                "Train the model first (scripts/train_unet.py) or set "
                "SUMI_COLORIZATION_CHECKPOINT."
            )
        ckpt = torch.load(checkpoint_path, map_location=self._device)
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
        if not self._loaded or self._model is None:
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
    ) -> Dict:
        """Run tiled U-Net inference on ``image_path`` and persist the result.

        ``mask_references`` and ``palette`` are accepted for protocol
        compatibility; the current U-Net is unconditional (learns directly
        from line art -> human color) and does not condition on masks.
        """
        try:
            self._ensure_loaded()
            del mask_references, palette  # unconditional model in v1

            logger.info(
                "Iniciando inferencia de colorización: %s (tile: %dx%d, overlap: %d)",
                image_path,
                self._tile_size,
                self._overlap,
            )
            t0 = time.time()
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
                "checkpoint": self.MODEL_PATH,
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
                "version_modelo": self.MODEL_NAME,
                "parametros": {
                    "checkpoint": self.MODEL_PATH,
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
