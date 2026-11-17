/* Model Registry — listado, registro, activación/desactivación y gestión
 * de modelos. Conectado a la API real bajo /api/v1/models.
 *
 * Los modelos locales aceptan .pt / .onnx; los modelos por API requieren
 * prueba de conexión antes de guardarse. Las claves de API se muestran
 * enmascaradas y nunca se devuelven sin cifrar al frontend.
 */
import { useState, useEffect } from "react";
import { api } from "../api/client";

type Model = {
  id: string;
  nombre: string;
  tarea: string;
  version: string;
  source_type: string | null;
  formato: string | null;
  is_active: boolean;
  salud: string;
  descripcion: string | null;
  parametros: Record<string, any>;
  hash_pesos: string | null;
  licencia: string | null;
  is_default: boolean;
  created_at: string | null;
  updated_at: string | null;
  api_key: string | null; // enmascarada
};

type RegisterMode = "local_file" | "api";

const TASK_LABEL: Record<string, string> = {
  colorizacion: "Colorización",
  segmentacion: "Segmentación",
  analisis: "Análisis",
};

const taskLabel = (t: string) => TASK_LABEL[t] || t;

const maskKey = (k: string | null) => {
  if (!k) return "—";
  return k.length > 4 ? k.slice(0, 3) + "…" + k.slice(-4) : k;
};

export default function Models() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [registerMode, setRegisterMode] = useState<RegisterMode>("local_file");
  const [registering, setRegistering] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);
  const [toggleLoading, setToggleLoading] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  // Registro local_file
  const [regFile, setRegFile] = useState<File | null>(null);
  const [regNombre, setRegNombre] = useState("");
  const [regFamilia, setRegFamilia] = useState("");
  const [regVersion, setRegVersion] = useState("");
  const [regDesc, setRegDesc] = useState("");

  // Registro API
  const [regBaseUrl, setRegBaseUrl] = useState("");
  const [regAuth, setRegAuth] = useState("bearer");
  const [regApiKey, setRegApiKey] = useState("");
  const [regEndpoint, setRegEndpoint] = useState("/infer");
  const [regModelo, setRegModelo] = useState("");
  const [regTimeout, setRegTimeout] = useState("30");
  const [regRetries, setRegRetries] = useState("2");

  useEffect(() => {
    let cancelled = false;
    api.get<Model[]>("/models")
      .then((data) => {
        if (!cancelled) {
          setModels(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "No se pudieron cargar los modelos.");
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, []);

  const handleToggle = async (model: Model) => {
    setToggleLoading((prev) => new Set([...prev, model.id]));
    try {
      await api.patch(`/models/${model.id}/status`, {
        estado: model.is_active ? "deshabilitado" : "disponible",
      });
      setModels((ms) =>
        ms.map((m) =>
          m.id === model.id ? { ...m, is_active: !m.is_active } : m
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar el estado del modelo.");
    } finally {
      setToggleLoading((prev) => {
        const n = new Set(prev);
        n.delete(model.id);
        return n;
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("¿Eliminar este modelo? Esta acción no se puede deshacer.")) {
      return;
    }
    try {
      await api.delete(`/models/${id}`);
      setModels((ms) => ms.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo eliminar el modelo.");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError(null);
    setRegistering(true);
    const formData = new FormData();
    formData.append("source_type", registerMode);
    formData.append("nombre", regNombre.trim());
    formData.append("familia", regFamilia.trim());
    formData.append("version", regVersion.trim());
    if (regDesc) formData.append("descripcion", regDesc);

    if (registerMode === "local_file") {
      if (!regFile) {
        setRegError("Selecciona un archivo .pt o .onnx.");
        setRegistering(false);
        return;
      }
      formData.append("file", regFile);
    } else {
      if (!regBaseUrl) {
        setRegError("La URL base es obligatoria para modelos API.");
        setRegistering(false);
        return;
      }
      formData.append("base_url", regBaseUrl);
      formData.append("auth_method", regAuth);
      if (regApiKey) formData.append("api_key", regApiKey);
      formData.append("endpoint", regEndpoint);
      if (regModelo) formData.append("modelo", regModelo);
      formData.append("timeout", regTimeout);
      formData.append("retries", regRetries);
    }

    try {
      await api.post<{ ok?: boolean; detail?: string }>("/models", formData);
      window.location.reload();
    } catch (err) {
      setRegError(err instanceof Error ? err.message : "No se pudo registrar el modelo.");
    } finally {
      setRegistering(false);
    }
  };

  const handleEditSave = async (id: string) => {
    setEditing(null);
    try {
      await api.put(`/models/${id}`, { nombre: editName.trim(), descripcion: editDesc.trim() || undefined });
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo editar el modelo.");
    }
  };

  const handleTestConnection = async (id: string) => {
    try {
      const res = await api.post<{ ok: boolean; detail: string }>(`/models/${id}/test-connection`);
      setError(res.ok ? "Conexión exitosa." : "La prueba de conexión falló: " + res.detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "La prueba de conexión falló.");
    }
  };

  if (loading) {
    return (
      <section className="screen is-active" id="screen-models">
        <div className="page-head">
          <div>
            <span className="eyebrow">Model Registry</span>
            <h1 className="h1">Model <em>Registry</em></h1>
          </div>
        </div>
        <p style={{ color: "var(--ink-muted)" }}>Cargando modelos…</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="screen is-active" id="screen-models">
        <div className="page-head">
          <div>
            <span className="eyebrow">Model Registry</span>
            <h1 className="h1">Model <em>Registry</em></h1>
          </div>
        </div>
        <p style={{ color: "#c0392b" }}>{error}</p>
      </section>
    );
  }

  return (
    <section className="screen is-active" id="screen-models">
      <div className="page-head">
        <div>
          <span className="eyebrow">Model Registry</span>
          <h1 className="h1">Model <em>Registry</em></h1>
          <p style={{ color: "var(--ink-muted)", marginTop: 6 }}>
            Modelos disponibles para el pipeline. Los modelos activos pueden
            ser usados en las etapas de análisis, máscara y colorización.
          </p>
        </div>
        <button type="button" className="btn-vermilion" onClick={() => {
          setRegisterMode("local_file");
          setRegFile(null); setRegNombre(""); setRegFamilia(""); setRegVersion(""); setRegDesc("");
          setRegBaseUrl(""); setRegAuth("bearer"); setRegApiKey(""); setRegEndpoint("/infer"); setRegModelo(""); setRegTimeout("30"); setRegRetries("2");
          setRegError(null);
        }}>
          + Agregar modelo
        </button>
      </div>

      {regError && (
        <div className="alert alert-error" role="alert">{regError}</div>
      )}
      {error && <p style={{ color: "#c0392b", marginBottom: 12 }}>{error}</p>}

      {/* Registro */}
      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 18, background: "var(--surface)", marginBottom: 24 }}>
        <div style={{ fontWeight: 600, marginBottom: 10, fontSize: 0.9 }}>Registrar modelo</div>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button
            type="button"
            className={`btn ${registerMode === "local_file" ? "btn-vermilion" : "btn-outline"}`}
            onClick={() => setRegisterMode("local_file")}
          >
            Archivo local (.pt / .onnx)
          </button>
          <button
            type="button"
            className={`btn ${registerMode === "api" ? "btn-vermilion" : "btn-outline"}`}
            onClick={() => setRegisterMode("api")}
          >
            API externa
          </button>
        </div>
        <form onSubmit={handleRegister} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div style={{ gridColumn: "span 2" }}>
            <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Nombre del modelo</label>
            <input type="text" value={regNombre} onChange={(e) => setRegNombre(e.target.value)} placeholder="Ej. sumi_unet_cpu" required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
          </div>
          <div>
            <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Tarea (familia)</label>
            <input type="text" value={regFamilia} onChange={(e) => setRegFamilia(e.target.value)} placeholder="Ej. colorizacion" required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
          </div>
          <div>
            <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Versión</label>
            <input type="text" value={regVersion} onChange={(e) => setRegVersion(e.target.value)} placeholder="v1.0.0" required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Descripción</label>
            <input type="text" value={regDesc} onChange={(e) => setRegDesc(e.target.value)} placeholder="Opcional" style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
          </div>
          {registerMode === "local_file" && (
            <div style={{ gridColumn: "span 2" }}>
              <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Archivo (.pt / .onnx)</label>
              <input type="file" accept=".pt,.pth,.onnx" onChange={(e) => setRegFile(e.target.files?.[0] ?? null)} required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
              <p style={{ fontSize: 0.78, color: "var(--ink-muted)", marginTop: 4 }}>Los archivos .pt se cargan con weights_only=True para evitar ejecución de código vía pickle.</p>
            </div>
          )}
          {registerMode === "api" && (
            <>
              <div>
                <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>URL base</label>
                <input type="text" value={regBaseUrl} onChange={(e) => setRegBaseUrl(e.target.value)} placeholder="https://api.ejemplo.com" required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Clave de API</label>
                <input type="password" value={regApiKey} onChange={(e) => setRegApiKey(e.target.value)} placeholder="sk-…" style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
                <p style={{ fontSize: 0.78, color: "var(--ink-muted)", marginTop: 4 }}>Se almacena cifrada; solo se muestra enmascarada.</p>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Método de autenticación</label>
                <select value={regAuth} onChange={(e) => setRegAuth(e.target.value)} style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }}>
                  <option value="bearer">Bearer</option>
                  <option value="apikey">API Key</option>
                  <option value="none">Ninguna</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Endpoint</label>
                <input type="text" value={regEndpoint} onChange={(e) => setRegEndpoint(e.target.value)} placeholder="/infer" style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Modelo / endpoint</label>
                <input type="text" value={regModelo} onChange={(e) => setRegModelo(e.target.value)} placeholder="sumi_unet_v1" style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Timeout (s)</label>
                  <input type="number" value={regTimeout} onChange={(e) => setRegTimeout(e.target.value)} style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Reintentos</label>
                  <input type="number" value={regRetries} onChange={(e) => setRegRetries(e.target.value)} style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
                </div>
              </div>
            </>
          )}
          <div style={{ gridColumn: "span 2", display: "flex", gap: 8, marginTop: 8 }}>
            <button type="submit" className="btn-vermilion" disabled={registering}>
              {registering ? "Registrando…" : "Registrar modelo"}
            </button>
            <button type="button" className="btn btn-outline" onClick={() => {
              setRegisterMode("local_file");
              setRegFile(null); setRegNombre(""); setRegFamilia(""); setRegVersion(""); setRegDesc("");
              setRegBaseUrl(""); setRegAuth("bearer"); setRegApiKey(""); setRegEndpoint("/infer"); setRegModelo(""); setRegTimeout("30"); setRegRetries("2");
              setRegError(null);
            }}>Cancelar</button>
          </div>
        </form>
      </div>

      {/* Listado */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <span style={{ fontWeight: 600, fontSize: 0.9 }}>{models.length} modelo(s) registrado(s)</span>
      </div>
      {models.length === 0 && (
        <div className="panel-box" style={{ textAlign: "center", padding: "48px 24px" }}>
          <span className="eyebrow">Sin modelos</span>
          <h2 className="h1" style={{ marginBottom: 12 }}>No hay modelos registrados.</h2>
          <p style={{ color: "var(--ink-muted)", maxWidth: 440, margin: "0 auto 24px" }}>
            Registra al menos un modelo activo para usarlo en las etapas del pipeline.
          </p>
        </div>
      )}
      {models.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tarea</th>
              <th>Versión</th>
              <th>Tipo</th>
              <th>Formato</th>
              <th>Salud</th>
              <th>Activo</th>
              <th>Clave API</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.nombre}</td>
                <td style={{ fontSize: 0.82, color: "var(--ink-muted)" }}>{taskLabel(m.tarea)}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 0.82 }}>{m.version}</td>
                <td style={{ fontSize: 0.82, color: "var(--ink-muted)" }}>{m.source_type ?? "—"}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 0.82 }}>{m.formato ?? "—"}</td>
                <td>
                  <span className={`badge ${m.salud === "ok" ? "badge-done" : m.salud === "error" ? "badge-failed" : "badge-running"}`} style={{ fontSize: 0.75 }}>{m.salud}</span>
                </td>
                <td>
                  <button
                    type="button"
                    className={`btn btn-sm ${m.is_active ? "btn-outline" : "btn-vermilion"}`}
                    disabled={toggleLoading.has(m.id)}
                    onClick={() => handleToggle(m)}
                  >
                    {toggleLoading.has(m.id) ? "…" : m.is_active ? "Desactivar" : "Activar"}
                  </button>
                </td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 0.78, color: "var(--ink-muted)" }}>{maskKey(m.api_key)}</td>
                <td>
                  {m.is_active && (
                    <>
                      <button type="button" className="btn btn-outline btn-sm" onClick={() => handleTestConnection(m.id)} style={{ marginRight: 4 }}>{m.source_type === "api" ? "Probar" : "—"}</button>
                      <button type="button" className="btn btn-outline btn-sm" onClick={() => {
                        setEditing(m.id);
                        setEditName(m.nombre);
                        setEditDesc(m.descripcion ?? "");
                      }}>Editar</button>
                      <button type="button" className="btn btn-outline btn-sm" style={{ color: "#c0392b", borderColor: "#c0392b" }} onClick={() => handleDelete(m.id)}>Eliminar</button>
                    </>
                  )}
                  {!m.is_active && (
                    <span style={{ fontSize: 0.78, color: "var(--ink-muted)" }}>Inactivo</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Edición */}
      {editing && (
        <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 18, background: "var(--surface)", marginTop: 24 }}>
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Editar modelo</div>
          <form onSubmit={(e) => { e.preventDefault(); handleEditSave(editing!); }} style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 500 }}>
            <div>
              <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Nombre</label>
              <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)} required style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 0.82, fontWeight: 600, marginBottom: 4 }}>Descripción</label>
              <input type="text" value={editDesc} onChange={(e) => setEditDesc(e.target.value)} style={{ width: "100%", padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--surface)" }} />
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button type="submit" className="btn-vermilion">Guardar cambios</button>
              <button type="button" className="btn btn-outline" onClick={() => setEditing(null)}>Cancelar</button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
