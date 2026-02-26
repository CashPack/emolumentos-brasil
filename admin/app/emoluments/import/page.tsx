'use client';

import Link from 'next/link';
import { useState } from 'react';
import { API_BASE, getToken } from '../../lib';

export default function ImportV5() {
  const [file, setFile] = useState<File | null>(null);
  const [year, setYear] = useState('2026');
  const [status, setStatus] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token) {
      setStatus('Faça login primeiro.');
      return;
    }
    if (!file) {
      setStatus('Selecione um arquivo .xlsx');
      return;
    }

    setStatus('Importando...');
    const fd = new FormData();
    fd.append('file', file);

    const res = await fetch(`${API_BASE}/emoluments/import/v5?year=${encodeURIComponent(year)}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });

    const text = await res.text();
    let data: any = text;
    try { data = text ? JSON.parse(text) : null; } catch {}

    if (!res.ok) {
      setStatus(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    setStatus(`OK: ${JSON.stringify(data)}`);
  }

  return (
    <main>
      <p><Link href="/emoluments">← Voltar</Link></p>
      <h1>Importar planilha v5</h1>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 520 }}>
        <label>
          Ano
          <input value={year} onChange={(e) => setYear(e.target.value)} />
        </label>
        <label>
          Arquivo .xlsx
          <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </label>
        <button type="submit">Importar</button>
      </form>
      <p style={{ whiteSpace: 'pre-wrap' }}>{status}</p>
    </main>
  );
}
