/** Sesión del frontend. El token se conserva solo durante la sesión del navegador. */
const TOKEN_KEY = "sumi_access_token";

export const authToken = {
  get: () => (typeof sessionStorage === "undefined" ? null : sessionStorage.getItem(TOKEN_KEY)),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};
