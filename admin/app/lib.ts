export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://pratico-admin-api.onrender.com';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(init.headers as any),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  return { res, data };
}
