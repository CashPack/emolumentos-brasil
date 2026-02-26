"""Parser da Pratico_Emolumentos_v5.xlsx (v5) sem dependências externas.

Extrai faixas de escritura com valor econômico por UF.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_OFFICE_REL_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


@dataclass(frozen=True)
class Bracket:
    range_from: float
    range_to: float
    amount: float


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cell_col(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    s = s.replace("R$", "").replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    s = re.sub(r"(?<=\d)[.,](?=\d{3}(\D|$))", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _load_shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out: List[str] = []
    for si in root.findall("m:si", _NS):
        texts = [t.text or "" for t in si.findall(".//m:t", _NS)]
        out.append("".join(texts))
    return out


def _workbook_sheet_map(z: zipfile.ZipFile) -> Dict[str, str]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {
        r.get("Id"): r.get("Target")
        for r in rels.findall(f"{_REL_NS}Relationship")
    }
    name_to_file: Dict[str, str] = {}
    sheets = wb.find("m:sheets", _NS)
    if sheets is None:
        return name_to_file
    for s in sheets.findall("m:sheet", _NS):
        name = s.get("name")
        rid = s.get(_OFFICE_REL_ATTR)
        if not name or not rid:
            continue
        target = rid_to_target.get(rid)
        if not target:
            continue
        name_to_file[name] = "xl/" + target
    return name_to_file


def _cell_value(c: ET.Element, shared: List[str]):
    t = c.get("t")
    v = c.find("m:v", _NS)
    if v is None or v.text is None:
        return None
    val = v.text
    if t == "s":
        try:
            return shared[int(val)]
        except Exception:
            return None
    return val


def _iter_rows(z: zipfile.ZipFile, sheet_xml_path: str, shared: List[str]) -> Iterable[Tuple[int, Dict[str, object]]]:
    root = ET.fromstring(z.read(sheet_xml_path))
    sheet_data = root.find("m:sheetData", _NS)
    if sheet_data is None:
        return
    for row in sheet_data.findall("m:row", _NS):
        r = row.get("r")
        if not r:
            continue
        r_i = int(r)
        d: Dict[str, object] = {}
        for c in row.findall("m:c", _NS):
            ref = c.get("r")
            if not ref:
                continue
            col = _cell_col(ref)
            val = _cell_value(c, shared)
            if val not in (None, ""):
                d[col] = val
        if d:
            yield r_i, d


def _find_header_row(rows: List[Tuple[int, Dict[str, object]]]) -> Optional[Tuple[int, str, str, str]]:
    def norm(x) -> str:
        return re.sub(r"\s+", " ", str(x)).strip().lower()

    for r, d in rows:
        inv = {norm(v): col for col, v in d.items()}
        col_de = inv.get("de (r$)")
        col_ate = inv.get("até (r$)") or inv.get("ate (r$)")
        col_emo = inv.get("emolumento (r$)")
        if col_de and col_ate and col_emo:
            return r, col_de, col_ate, col_emo
    return None


def parse_v5_xlsx(xlsx_bytes: bytes) -> tuple[str, Dict[str, List[Bracket]]]:
    """Retorna (hash, {UF: [Bracket...]})"""
    file_hash = sha256_bytes(xlsx_bytes)
    by_uf: Dict[str, List[Bracket]] = {}

    with zipfile.ZipFile(io := __import__("io").BytesIO(xlsx_bytes)) as z:
        shared = _load_shared_strings(z)
        sheet_map = _workbook_sheet_map(z)

        # UFs válidas são abas com 2 letras
        for name, sheet_xml in sheet_map.items():
            if not re.fullmatch(r"[A-Z]{2}", name):
                continue
            rows = list(_iter_rows(z, sheet_xml, shared))
            header = _find_header_row(rows)
            if not header:
                continue
            header_row, col_de, col_ate, col_emo = header
            brackets: List[Bracket] = []
            for r, d in rows:
                if r <= header_row:
                    continue
                de = _to_float(d.get(col_de))
                ate = _to_float(d.get(col_ate))
                amt = _to_float(d.get(col_emo))
                if ate is None or amt is None:
                    continue
                if de is None:
                    de = 0.0
                brackets.append(Bracket(range_from=de, range_to=ate, amount=amt))
            if brackets:
                brackets.sort(key=lambda b: (b.range_from, b.range_to))
                by_uf[name] = brackets

    return file_hash, by_uf
