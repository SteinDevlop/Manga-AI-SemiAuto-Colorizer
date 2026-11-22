import { render } from "@testing-library/react";
import { describe, it, vi, expect } from "vitest";
import App from "../App";
import { AppProvider } from "../context/AppContext";
import fx from "./fx.json";

function mock(url: string) {
  const u = String(url).split("?")[0].replace("http://localhost:8000/api/v1", ""); let body: any = {};
  if (u === "/projects") body = fx.projects;
  else if (u.startsWith("/projects/")) body = fx.project;
  else if (u === "/metrics") body = fx.metrics;
  else if (u === "/colorizations") body = fx.colorizations;
  else if (u === "/models") body = fx.models;
  else if (u.startsWith("/analysis/")) body = fx.analysis;
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
}
describe("smoke-real", () => {
  const P = fx.pid;
  for (const path of ["/", "/dashboard", "/projects", `/projects/${P}`, `/projects/${P}/upload`, `/projects/${P}/analysis`, `/projects/${P}/character`, `/projects/${P}/approve`, `/projects/${P}/colorize`, `/projects/${P}/export`, "/results", "/jobs", "/models", "/settings"]) {
    it(path, async () => {
      vi.stubGlobal("fetch", vi.fn(mock));
      window.history.pushState({}, "", path);
      const errs: string[] = [];
      const spy = vi.spyOn(console, "error").mockImplementation((...a) => { errs.push(a.map(String).join(" ").slice(0, 400)); });
      const { container, unmount } = render(<AppProvider><App /></AppProvider>);
      await new Promise((r) => setTimeout(r, 400));
      spy.mockRestore();
      const real = errs.filter((e) => !e.includes("act("));
      console.log("PATH", path.replace(P, "ID"), "LEN", (container.textContent ?? "").length, real.length ? "ERR " + real[0] : "ok");
      unmount();
    });
  }
});
