from __future__ import annotations

import os
from typing import Any

import httpx


def _getenv(name: str, default: str | None = None) -> str:
    v = os.environ.get(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def normalize_e164_br(phone: str) -> str:
    """Best-effort normalize to +55XXXXXXXXXXX (Brazil). Keeps leading + if present."""
    p = (phone or "").strip()
    if not p:
        return p
    # remove spaces, parentheses, hyphens
    for ch in (" ", "(", ")", "-", "."):
        p = p.replace(ch, "")
    # if starts with 55 without +, add +
    if p.startswith("55") and not p.startswith("+"):
        p = "+" + p
    # if starts with 0, drop
    if p.startswith("0"):
        p = p.lstrip("0")
    # if no + and looks like BR local (10-11 digits), prefix +55
    digits = "".join([c for c in p if c.isdigit()])
    if not p.startswith("+") and len(digits) in (10, 11):
        p = "+55" + digits
    return p


async def send_template(*, to: str, template: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Send a WhatsApp template via RMChat.

    NOTE: RMChat API details may differ. Configure via env:
      - RMCHAT_API_BASE (e.g. https://api.rmchat.com.br)
      - RMCHAT_API_TOKEN (Bearer token)
      - RMCHAT_SEND_TEMPLATE_PATH (default: /messages/template)

    Expected payload shape (placeholder):
      {"to": "+55...", "template": "name", "variables": {...}}

    If RMChat uses a different schema, adjust here.
    """
    base = _getenv("RMCHAT_API_BASE")
    token = _getenv("RMCHAT_API_TOKEN")
    path = os.environ.get("RMCHAT_SEND_TEMPLATE_PATH", "/messages/template")

    url = base.rstrip("/") + "/" + path.lstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": normalize_e164_br(to),
        "template": template,
        "variables": variables,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(url, json=payload, headers=headers)
        # Let caller decide behavior; include body for debug
        try:
            data = res.json()
        except Exception:
            data = {"raw": res.text}
        if res.status_code >= 400:
            raise RuntimeError(f"rmchat_send_failed status={res.status_code} body={data}")
        return data
