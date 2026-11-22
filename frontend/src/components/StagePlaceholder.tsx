/* Placeholder de etapa de proyecto (Fase 5).
 *
 * Se renderiza dentro de ProjectLayout para la etapa actual del proyecto.
 * La Fase 7 reemplaza cada etapa por su pantalla real (Upload, Analysis,
 * Character, Mask, Approve, Colorize, Export). Mientras tanto, este
 * placeholder permite navegar el stepper y avanzar/retroceder etapas.
 */
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { STAGE_ORDER } from "./ProjectLayout";

const stageLabel = (s: string) => {
  const labels: Record<string, string> = {
    upload: "Subida",
    analysis: "Análisis",
    character: "Personajes",
    mask: "Máscara",
    approve: "Aprobación",
    colorize: "Colorizar",
    export: "Exportar",
  };
  return labels[s] || s;
};

type StagePlaceholderProps = {
  stage: string;
  isCurrent: boolean;
  onComplete: () => void;
};

export function StagePlaceholder({ stage, isCurrent, onComplete }: StagePlaceholderProps) {
  const navigate = useNavigate();
  const idx = STAGE_ORDER.indexOf(stage);
  const isLast = idx === STAGE_ORDER.length - 1;

  const handleAdvance = () => {
    if (isLast) {
      navigate("/projects");
      return;
    }
    onComplete();
  };

  return (
    <section style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 24, background: "var(--surface)" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 12 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", fontWeight: 600 }}>{idx + 1}. {stageLabel(stage)}</span>
        {isCurrent ? (
          <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>Etapa actual</span>
        ) : (
          <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>Etapa previa (retrocediste)</span>
        )}
      </div>
      <p style={{ color: "var(--ink-muted)", marginBottom: 18, maxWidth: 600 }}>
        Contenido de la etapa <strong>{stageLabel(stage)}</strong>. Aquí se implementará la interfaz propia de cada etapa en la Fase 7.
      </p>
      {isCurrent && !isLast ? (
        <button
          type="button"
          className="btn btn-vermilion"
          onClick={handleAdvance}
        >
          Marcar {stageLabel(stage)} como completada y avanzar
        </button>
      ) : isCurrent && isLast ? (
        <button type="button" className="btn btn-vermilion" onClick={handleAdvance} disabled>
          Proyecto completado
        </button>
      ) : (
        <p style={{ color: "var(--ink-muted)", fontSize: "0.85rem" }}>
          Usa el stepper de arriba para retroceder a esta etapa, o avanza desde la etapa actual.
        </p>
      )}
    </section>
  );
}
