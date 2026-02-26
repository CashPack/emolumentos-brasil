'use client';

import { useState } from 'react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<string>('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('Entrando...');
    const base = process.env.NEXT_PUBLIC_API_BASE || 'https://pratico-admin-api.onrender.com';
    const res = await fetch(`${base}/auth/login-json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    localStorage.setItem('token', data.access_token);
    setStatus('OK! Token salvo no navegador.');
  }

  return (
    <main>
      <h1>Login</h1>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 420 }}>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Senha
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%' }} />
        </label>
        <button type="submit">Entrar</button>
      </form>
      <p>{status}</p>
    </main>
  );
}
