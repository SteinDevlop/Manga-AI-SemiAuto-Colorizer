import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, signIn } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || "/dashboard";
  if (user) return <Navigate to={from} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(null); setBusy(true);
    try { await signIn(email.trim(), password); }
    catch (err) { setError(err instanceof Error ? err.message : "No fue posible iniciar sesión."); }
    finally { setBusy(false); }
  };

  return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--paper, #f4f1e9)" }}>
    <form onSubmit={submit} style={{ width: "min(420px, 100%)", padding: 32, background: "var(--surface, white)", border: "1px solid var(--border, #ddd)", borderRadius: 12 }}>
      <div className="eyebrow">STAR COLORIZING · STUDIO</div>
      <h1 className="h1" style={{ marginTop: 10 }}>Iniciar sesión</h1>
      <p style={{ color: "var(--ink-muted)", marginBottom: 24 }}>Accede a tus proyectos y trabajos de colorización.</p>
      <label htmlFor="login-email">Correo electrónico</label>
      <input id="login-email" type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} style={{ width: "100%", margin: "8px 0 18px", padding: 12 }} />
      <label htmlFor="login-password">Contraseña</label>
      <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} style={{ width: "100%", margin: "8px 0 18px", padding: 12 }} />
      {error && <p role="alert" style={{ color: "#c0392b" }}>{error}</p>}
      <button className="btn btn-vermilion" type="submit" disabled={busy} style={{ width: "100%" }}>{busy ? "Ingresando…" : "Ingresar"}</button>
    </form>
  </main>;
}
