import Link from 'next/link';

export default function Home() {
  return (
    <main>
      <h1>Pratico Admin</h1>
      <ul>
        <li><Link href="/login">Login</Link></li>
        <li><Link href="/emoluments">Emolumentos</Link></li>
      </ul>
    </main>
  );
}
