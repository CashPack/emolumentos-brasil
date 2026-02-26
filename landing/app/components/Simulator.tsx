'use client';

import { useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://pratico-admin-api.onrender.com';

const UFS = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PE','PR','PI','RJ','RN','RS','RO','RR','SC','SE','SP','TO'
];

export default function Simulator() {
  const [uf, setUf] = useState('SP');
  const [value, setValue] = useState('500000');
  const [result, setResult] = useState<any>(null);
  const [status, setStatus] = useState('');

  async function calc() {
    setStatus('Calculando...');
    setResult(null);
    const property_value = Number(value.replace(/\./g,'').replace(',','.'));
    const res = await fetch(`${API_BASE}/calc/deed-economy?uf=${encodeURIComponent(uf)}&property_value=${encodeURIComponent(property_value)}`);
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Erro: ${JSON.stringify(data)}`);
      return;
    }
    setResult(data);
    setStatus('OK');
  }

  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>Valor do imóvel (R$)</label>
        <input value={value} onChange={e => setValue(e.target.value)} placeholder="500000" />
      </div>
      <div style={{ display: 'grid', gap: 6 }}>
        <label>UF do imóvel</label>
        <select value={uf} onChange={e => setUf(e.target.value)}>
          {UFS.map(x => <option key={x} value={x}>{x}</option>)}
        </select>
      </div>
      <button onClick={calc} style={{ padding: '10px 14px', borderRadius: 10, background: '#0f172a', color: 'white', border: 0, fontWeight: 600 }}>
        Calcular economia
      </button>
      <div style={{ fontSize: 14, color: '#475569' }}>{status}</div>

      {result && (
        <div style={{ marginTop: 10, padding: 12, borderRadius: 12, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            Economia de até R$ {Number(result.economia).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ marginTop: 6, fontSize: 13, color: '#475569' }}>
            UF informada ({result.input.uf}): R$ {Number(result.local.emolumento).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            <br />
            Melhor UF ({result.best.uf}): R$ {Number(result.best.emolumento).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </div>
        </div>
      )}
    </div>
  );
}
