'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://pratico-admin-api.onrender.com';

export default function LeadForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [profile, setProfile] = useState('broker');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('Enviando...');

    const res = await fetch(`${API_BASE}/public/leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, profile, message, consent: true }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    setStatus('Recebido! Vamos te chamar no WhatsApp.');
    setName(''); setEmail(''); setPhone(''); setMessage('');
  }

  return (
    <form onSubmit={submit} style={{ display: 'grid', gap: 10, maxWidth: 640 }}>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>Nome</label>
        <input value={name} onChange={e => setName(e.target.value)} required />
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>WhatsApp</label>
        <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="(22) 99730-3566" />
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>Email</label>
        <input value={email} onChange={e => setEmail(e.target.value)} type="email" />
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>Perfil</label>
        <select value={profile} onChange={e => setProfile(e.target.value)}>
          <option value="broker">Corretor</option>
          <option value="buyer">Comprador</option>
          <option value="seller">Vendedor</option>
          <option value="other">Outro</option>
        </select>
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>Mensagem (opcional)</label>
        <textarea value={message} onChange={e => setMessage(e.target.value)} rows={4} />
      </div>
      <button type="submit" style={{ padding: '10px 14px', borderRadius: 10, background: '#0f172a', color: 'white', border: 0, fontWeight: 600 }}>
        Quero falar com a PRÁTICO
      </button>
      <div style={{ fontSize: 14, color: '#475569' }}>{status}</div>
    </form>
  );
}
