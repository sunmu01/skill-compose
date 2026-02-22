/**
 * [INPUT]: 依赖 api.ts 的 BACKEND_API_BASE 推断逻辑
 * [OUTPUT]: 对外提供 getToken, setToken, clearToken, login, logout, isAuthenticated
 * [POS]: lib/ 的认证 token 管理器，被 auth-guard.tsx 和 api.ts 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

const TOKEN_KEY = 'skills_auth_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function login(password: string): Promise<boolean> {
  // 运行时推断 API 地址（与 api.ts 的 getApiBaseUrl 逻辑一致）
  const base = typeof window !== 'undefined'
    ? `${window.location.origin}/api/v1`
    : 'http://localhost:62610/api/v1';

  try {
    const res = await fetch(`${base}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    if (!res.ok) return false;

    const data = await res.json();
    setToken(data.token);
    return true;
  } catch {
    return false;
  }
}

export function logout(): void {
  clearToken();
  window.location.href = '/login';
}
