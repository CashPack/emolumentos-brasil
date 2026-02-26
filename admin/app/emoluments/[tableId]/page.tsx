'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch } from '../../lib';

type Bracket = {
  id: string;
  range_from: number;
  range_to: number;
  amount: number;
  active: boolean;
};

type Table = {
  id: string;
  uf: string;
  year: number;
  status: string;
  created_at: string;
  source_name?: string | null;
};

export default function TableDetail({ params }: { params: { tableId: string } }) {
  const tableId = params.tableId;
  const [table, setTable] = useState<Table | null>(null);
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [status, setStatus] = useState('');

  async function load() {
    setStatus('Carregando...');

    const t = await apiFetch('/emoluments/tables');
    if (!t.res.ok) {
      setStatus(`Erro tabelas: ${JSON.stringify(t.data)}`);
      return;
    }
    const found = (t.data as Table[]).find(x => x.id === tableId) || null;
    setTable(found);

    const b = await apiFetch(`/emoluments/tables/${tableId}/brackets`);
    if (!b.res.ok) {
      setStatus(`Erro faixas: ${JSON.stringify(b.data)}`);
      return;
    }
    setBrackets(b.data);
    setStatus('OK');
  }

  useEffect(() => {
    load();
  }, [tableId]);

  return (
    <main>
      <p><Link href="/emoluments">← Voltar</Link></p>
      <h1>Faixas da tabela</h1>
      {table ? (
        <div style={{ marginBottom: 12 }}>
          <div><b>UF:</b> {table.uf} | <b>Ano:</b> {table.year} | <b>Status:</b> {table.status}</div>
          <div><b>ID:</b> <span style={{ fontFamily: 'monospace' }}>{table.id}</span></div>
        </div>
      ) : (
        <p><b>ID:</b> <span style={{ fontFamily: 'monospace' }}>{tableId}</span></p>
      )}

      <p style={{ fontSize: 12, opacity: 0.8 }}>
        Clique em “Editar”, ajuste os valores e salve. (MVP: não valida sobreposição de faixas ainda.)
      </p>

      <p>{status}</p>

      <table border={1} cellPadding={6} style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>De</th><th>Até</th><th>Emolumento</th><th>Ativa</th><th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {brackets.map(b => (
            <BracketRow key={b.id} b={b} onSaved={load} />
          ))}
        </tbody>
      </table>
    </main>
  );
}

function BracketRow({ b, onSaved }: { b: Bracket; onSaved: () => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [rangeFrom, setRangeFrom] = useState(String(b.range_from));
  const [rangeTo, setRangeTo] = useState(String(b.range_to));
  const [amount, setAmount] = useState(String(b.amount));
  const [active, setActive] = useState(Boolean(b.active));
  const [msg, setMsg] = useState('');

  async function save() {
    setMsg('Salvando...');
    const payload = {
      range_from: Number(rangeFrom),
      range_to: Number(rangeTo),
      amount: Number(amount),
      active,
    };
    const { res, data } = await apiFetch(`/emoluments/brackets/${b.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setMsg(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    setMsg('OK');
    setEditing(false);
    await onSaved();
  }

  return (
    <tr>
      <td>{editing ? <input value={rangeFrom} onChange={e => setRangeFrom(e.target.value)} /> : b.range_from}</td>
      <td>{editing ? <input value={rangeTo} onChange={e => setRangeTo(e.target.value)} /> : b.range_to}</td>
      <td>{editing ? <input value={amount} onChange={e => setAmount(e.target.value)} /> : b.amount}</td>
      <td>{editing ? <input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} /> : String(b.active)}</td>
      <td>
        {editing ? (
          <>
            <button onClick={save}>Salvar</button>{' '}
            <button onClick={() => setEditing(false)}>Cancelar</button>
            <div style={{ fontSize: 12 }}>{msg}</div>
          </>
        ) : (
          <button onClick={() => setEditing(true)}>Editar</button>
        )}
      </td>
    </tr>
  );
}
