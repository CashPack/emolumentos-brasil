import Simulator from './components/Simulator';
import LeadForm from './components/LeadForm';

const WHATSAPP = 'https://wa.me/5522997303566';
const ADMIN_URL = 'https://emolumentos-brasil.vercel.app';

export default function Home() {
  return (
    <main>
      <header style={{ padding: '20px 16px', borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ maxWidth: 980, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <b>PRÁTICO DOCUMENTOS ON-LINE</b>
          <nav style={{ display: 'flex', gap: 14, fontSize: 14 }}>
            <a href="#simulador">Simulador</a>
            <a href="#como-funciona">Como funciona</a>
            <a href="#faq">FAQ</a>
            <a href={ADMIN_URL} target="_blank" rel="noreferrer">Login</a>
          </nav>
        </div>
      </header>

      <section style={{ padding: '56px 16px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto', display: 'grid', gap: 24 }}>
          <h1 style={{ fontSize: 44, lineHeight: 1.05, margin: 0 }}>
            Economize até 70% nos custos de escritura do seu imóvel
          </h1>
          <p style={{ fontSize: 18, maxWidth: 760, margin: 0, color: '#334155' }}>
            Com a PRÁTICO DOCUMENTOS ON-LINE, seu cliente paga menos e você ganha mais.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <a href="#simulador" style={btnPrimary}>Simular economia agora →</a>
            <a href={WHATSAPP} target="_blank" rel="noreferrer" style={btnSecondary}>Falar no WhatsApp</a>
          </div>

          <div id="simulador" style={card}>
            <h2 style={{ marginTop: 0 }}>Simulador rápido</h2>
            <Simulator />
          </div>
        </div>
      </section>

      <section style={{ padding: '0 16px 40px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          <div style={card}><b>Para corretores</b><p style={p}>Ganhe comissões extras automáticas sem complicação.</p></div>
          <div style={card}><b>Para compradores</b><p style={p}>Economia imediata + ITBI pago só no registro (STF Tema 1124).</p></div>
          <div style={card}><b>Para vendedores</b><p style={p}>Receba o valor do imóvel com segurança e agilidade.</p></div>
        </div>
      </section>

      <section id="como-funciona" style={{ padding: '24px 16px 40px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <h2>Como funciona</h2>
          <ol style={{ color: '#334155', lineHeight: 1.7 }}>
            <li>Envie os documentos pelo WhatsApp</li>
            <li>Receba a simulação de economia</li>
            <li>Comprador paga via PIX com split automático</li>
            <li>Acompanhe tudo pelo WhatsApp</li>
          </ol>
        </div>
      </section>

      <section style={{ padding: '0 16px 40px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <h2>Prova social</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
            <blockquote style={card}>“Com a PRÁTICO, meus clientes economizam em média R$ 10 mil por escritura. Virou meu principal diferencial de vendas!”<br/><br/><b>João Marcos</b> — Corretor parceiro – SP</blockquote>
            <blockquote style={card}>“A economia foi tão grande que meu cliente usou o dinheiro para mobiliar o apartamento novo. Indicação garantida!”<br/><br/><b>Renata Oliveira</b> — Corretora parceira – RJ</blockquote>
            <blockquote style={card}>“Além da minha comissão imobiliária, ainda ganho um extra por escritura com a PRÁTICO. Parceria que realmente vale a pena.”<br/><br/><b>Carlos Eduardo</b> — Corretor parceiro – DF</blockquote>
          </div>
        </div>
      </section>

      <section style={{ padding: '0 16px 60px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <h2>Cadastre-se / Fale com a gente</h2>
          <div style={card}>
            <LeadForm />
          </div>
          <p style={{ fontSize: 12, color: '#64748b' }}>
            Nota: informações gerais. Não constitui aconselhamento jurídico/tributário; a aplicação pode variar conforme o município e o caso concreto.
          </p>
        </div>
      </section>

      <section id="faq" style={{ padding: '0 16px 60px' }}>
        <div style={{ maxWidth: 980, margin: '0 auto' }}>
          <h2>FAQ</h2>
          <div style={{ display: 'grid', gap: 10 }}>
            <details style={card}><summary><b>Como funciona o split de pagamento?</b></summary><p style={p}>No MVP, descrevemos como fluxo operacional (PIX + divisão). A implementação financeira entra na etapa de pagamentos.</p></details>
            <details style={card}><summary><b>Preciso criar conta no Asaas?</b></summary><p style={p}>Não. Quando integrarmos pagamentos, a PRÁTICO opera o fluxo e você acompanha pelo WhatsApp/painel.</p></details>
            <details style={card}><summary><b>O ITBI realmente pode ser pago depois?</b></summary><p style={p}>Explicamos o entendimento do STF (Tema 1124) e orientamos validação caso a caso. Podemos incluir link para material explicativo.</p></details>
          </div>
        </div>
      </section>

      <footer style={{ padding: '20px 16px', borderTop: '1px solid #e2e8f0' }}>
        <div style={{ maxWidth: 980, margin: '0 auto', display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', fontSize: 14, color: '#475569' }}>
          <span>© {new Date().getFullYear()} PRÁTICO DOCUMENTOS ON-LINE LTDA</span>
          <span style={{ display: 'flex', gap: 12 }}>
            <a href={WHATSAPP} target="_blank" rel="noreferrer">WhatsApp</a>
            <a href={ADMIN_URL} target="_blank" rel="noreferrer">Painel</a>
          </span>
        </div>
      </footer>
    </main>
  );
}

const btnPrimary: React.CSSProperties = {
  background: '#0f172a',
  color: 'white',
  padding: '12px 16px',
  borderRadius: 10,
  textDecoration: 'none',
  fontWeight: 600,
};

const btnSecondary: React.CSSProperties = {
  background: 'white',
  color: '#0f172a',
  padding: '12px 16px',
  borderRadius: 10,
  textDecoration: 'none',
  fontWeight: 600,
  border: '1px solid #e2e8f0',
};

const card: React.CSSProperties = {
  background: 'white',
  border: '1px solid #e2e8f0',
  borderRadius: 14,
  padding: 16,
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
};

const p: React.CSSProperties = { marginBottom: 0, color: '#334155', lineHeight: 1.6 };
