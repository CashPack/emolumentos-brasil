'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

type Table = {
  id: string;
  uf: string;
  year: number;
  status: string;
  created_at: string;
};

export default function Emoluments() {
  const [tables, setTables] = useState<Table[]>([]);
  const [status, setStatus] = useState('');

  async function load() {
    setStatus('Carregando...');
    const token = localStorage.getItem('token');
    if (!token) {
      setStatus('Você precisa fazer login primeiro.');
      return;
    }
    const base = process.env.NEXT_PUBLIC_API_BASE || 'https://pratico-admin-api.onrender.com';
    const res = await fetch(`${base}/emoluments/tables?status=active`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    setTables(data);
    setStatus(`OK: ${data.length} tabelas`);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main>
      <h1>Emolumentos (tabelas ativas)</h1>
      <button onClick={load}>Recarregar</button>
      <p>{status}</p>
      <table border={1} cellPadding={6} style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>UF</th><th>Ano</th><th>Status</th><th>ID</th>
          </tr>
        </thead>
        <tbody>
          {tables.map(t => (
            <tr key={t.id}>
              <td>{t.uf}</td>
              <td>{t.year}</td>
              <td>{t.status}</td>
              <td style={{ fontFamily: 'monospace' }}>
                <Link href={`/emoluments/${t.id}`} style={{ textDecoration: 'underline' }}>
                  {t.id}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
