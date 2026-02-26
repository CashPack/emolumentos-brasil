"""Leitor da planilha Pratico_Emolumentos_v5.xlsx (sem dependências externas).

Fonte oficial (2026): Pratico_Emolumentos_v5.xlsx
Foco: Escritura pública COM valor econômico (tabela por faixas: De/Até/Emolumento).

Implementação: abre o .xlsx como ZIP e lê os XMLs internos (OpenXML).
"""

from __future__ import annotations

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_OFFICE_REL_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


@dataclass(frozen=True)
class FaixaEscritura:
    de: float
    ate: float
    emolumento: float


class PlanilhaEmolumentosV5:
    def __init__(self, xlsx_path: str):
        self.xlsx_path = xlsx_path
        if not os.path.exists(xlsx_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {xlsx_path}")

    @staticmethod
    def _cell_col(ref: str) -> str:
        return "".join(ch for ch in ref if ch.isalpha())

    @staticmethod
    def _to_float(v) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if s == "":
            return None
        # tolera separadores comuns
        s = s.replace("R$", "").replace(" ", "")
        # se vier com vírgula decimal, converte
        if s.count(",") == 1 and s.count(".") == 0:
            s = s.replace(",", ".")
        # remove milhares (ex: 1.234,56 ou 1,234.56)
        s = re.sub(r"(?<=\d)[.,](?=\d{3}(\D|$))", "", s)
        try:
            return float(s)
        except ValueError:
            return None

    def _load_shared_strings(self, z: zipfile.ZipFile) -> List[str]:
        if "xl/sharedStrings.xml" not in z.namelist():
            return []
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        out: List[str] = []
        for si in root.findall("m:si", _NS):
            texts = [t.text or "" for t in si.findall(".//m:t", _NS)]
            out.append("".join(texts))
        return out

    def _workbook_sheet_map(self, z: zipfile.ZipFile) -> Dict[str, str]:
        """Mapeia nome da aba -> caminho do XML da worksheet (ex: xl/worksheets/sheet29.xml)."""
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

    def _cell_value(self, c: ET.Element, shared: List[str]):
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

    def _iter_rows(self, z: zipfile.ZipFile, sheet_xml_path: str, shared: List[str]) -> Iterable[Tuple[int, Dict[str, object]]]:
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
                col = self._cell_col(ref)
                val = self._cell_value(c, shared)
                if val not in (None, ""):
                    d[col] = val
            if d:
                yield r_i, d

    def _find_table_header_row(self, rows: List[Tuple[int, Dict[str, object]]]) -> Optional[Tuple[int, str, str, str]]:
        """Procura a linha de header com 'De (R$)', 'Até (R$)', 'Emolumento (R$)'.

        Retorna: (row_number, col_de, col_ate, col_emolumento)
        """
        def norm(x) -> str:
            return re.sub(r"\s+", " ", str(x)).strip().lower()

        for r, d in rows:
            # cria mapa texto normalizado -> coluna
            inv = {norm(v): col for col, v in d.items()}
            col_de = inv.get("de (r$)")
            col_ate = inv.get("até (r$)") or inv.get("ate (r$)")
            col_emo = inv.get("emolumento (r$)")
            if col_de and col_ate and col_emo:
                return r, col_de, col_ate, col_emo
        return None

    @lru_cache(maxsize=64)
    def carregar_faixas_escritura(self, uf: str) -> List[FaixaEscritura]:
        uf = uf.upper().strip()
        with zipfile.ZipFile(self.xlsx_path) as z:
            shared = self._load_shared_strings(z)
            sheet_map = self._workbook_sheet_map(z)
            sheet_xml = sheet_map.get(uf)
            if not sheet_xml:
                raise KeyError(f"Aba não encontrada para UF={uf}. Abas disponíveis: {sorted(sheet_map.keys())}")

            rows = list(self._iter_rows(z, sheet_xml, shared))
            header = self._find_table_header_row(rows)
            if not header:
                raise ValueError(f"Não encontrei cabeçalho de tabela (De/Até/Emolumento) na aba {uf}")

            header_row, col_de, col_ate, col_emo = header
            faixas: List[FaixaEscritura] = []

            # lê linhas após o header
            for r, d in rows:
                if r <= header_row:
                    continue
                de = self._to_float(d.get(col_de))
                ate = self._to_float(d.get(col_ate))
                emo = self._to_float(d.get(col_emo))
                if de is None and ate is None and emo is None:
                    continue
                # para evitar capturar rodapés/textos, exige pelo menos ate+emo
                if ate is None or emo is None:
                    continue
                if de is None:
                    de = 0.0
                faixas.append(FaixaEscritura(de=de, ate=ate, emolumento=emo))

            if not faixas:
                raise ValueError(f"Tabela de faixas vazia na aba {uf}")

            # ordena e retorna
            faixas.sort(key=lambda x: (x.de, x.ate))
            return faixas

    def calcular_escritura_por_valor(self, uf: str, valor: float) -> Dict[str, object]:
        uf = uf.upper().strip()
        if valor is None or float(valor) < 0:
            return {"erro": "Valor inválido"}
        valor = float(valor)

        faixas = self.carregar_faixas_escritura(uf)
        for f in faixas:
            if f.de <= valor <= f.ate:
                return {
                    "uf": uf,
                    "valor": valor,
                    "emolumento": round(f.emolumento, 2),
                    "faixa": {"de": f.de, "ate": f.ate},
                    "fonte": os.path.basename(self.xlsx_path),
                }
        # se não achou, tenta última faixa (ex.: Até 999999999)
        last = faixas[-1]
        if valor > last.ate:
            return {
                "uf": uf,
                "valor": valor,
                "emolumento": round(last.emolumento, 2),
                "faixa": {"de": last.de, "ate": last.ate},
                "fonte": os.path.basename(self.xlsx_path),
                "observacao": "Valor acima do teto da planilha; usando última faixa.",
            }
        return {"erro": "Nenhuma faixa encontrada para o valor informado"}
