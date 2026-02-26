"""API HTTP simples (sem dependências) para consultar emolumentos v5.

Endpoints:
- GET /health
- GET /escritura?uf=SP&valor=500000

Execução:
    python3 api_server.py

Obs: Usa apenas stdlib.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from calculadora_emolumentos_v5 import CalculadoraEmolumentosV5


XLSX_PATH = os.environ.get(
    "EMOLUMENTOS_XLSX",
    os.path.join(os.path.dirname(__file__), "legacy", "data", "Pratico_Emolumentos_v5.xlsx"),
)

calc = CalculadoraEmolumentosV5(XLSX_PATH)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            return self._send(200, {"ok": True})

        if u.path == "/escritura":
            q = parse_qs(u.query)
            uf = (q.get("uf") or [""])[0].strip().upper()
            valor_s = (q.get("valor") or [""])[0].strip()
            if not uf or not valor_s:
                return self._send(400, {"erro": "Parâmetros obrigatórios: uf, valor"})
            try:
                valor = float(valor_s)
            except ValueError:
                return self._send(400, {"erro": "valor deve ser numérico"})

            r = calc.calcular_escritura_valor(uf, valor)
            if "erro" in r:
                return self._send(400, r)
            return self._send(200, r)

        return self._send(404, {"erro": "Not found"})


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    # Observação: alguns ambientes (incl. este) exportam PORT já ocupado.
    # Então só respeitamos PORT se o usuário explicitamente setar EMOLUMENTOS_USE_PORT=1.
    port_env = os.environ.get("PORT")
    use_port = os.environ.get("EMOLUMENTOS_USE_PORT") == "1"
    if use_port and port_env:
        port = int(port_env)
        httpd = HTTPServer((host, port), Handler)
        print(f"API on http://{host}:{port} (xlsx={XLSX_PATH})")
        httpd.serve_forever()
        return

    # tenta portas comuns e escolhe a primeira livre
    for port in (8080, 8099, 18080, 18888, 0):
        try:
            httpd = HTTPServer((host, port), Handler)
            port_real = httpd.server_address[1]
            print(f"API on http://{host}:{port_real} (xlsx={XLSX_PATH})")
            httpd.serve_forever()
            return
        except OSError:
            continue

    raise RuntimeError("Não foi possível abrir uma porta para o servidor HTTP")


if __name__ == "__main__":
    main()
