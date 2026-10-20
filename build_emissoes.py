# -*- coding: utf-8 -*-
"""Converte a planilha de faturamento (aba 'Resumo') em emissoes_mensal.json, lido pelo
build_dashboard.py na secao "Emissoes x Chamados" da Reuniao Mensal.

Uso:  python build_emissoes.py "caminho/faturamento_AAAA-MM_a_AAAA-MM.xlsx"

Por mes guarda os totais de CT-e, NFS-e, Sistemico e GNRE (MDF-e fica de fora, como na analise da
reuniao) e a lista de clientes (CNPJ matriz) que emitiram algo no mes — so' como hash curto, pra
contar clientes distintos por trimestre/YTD sem expor nomes ou CNPJs no HTML publicado.
"""
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "emissoes_mensal.json")


def main(xlsx):
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    rows = wb["Resumo"].iter_rows(values_only=True)
    hdr = list(next(rows))
    ix = {h: i for i, h in enumerate(hdr)}
    meses = defaultdict(lambda: {"cte": 0, "nfse": 0, "sistemico": 0, "gnre": 0})
    por_cliente = defaultdict(lambda: defaultdict(int))  # mes -> cnpj -> total
    for r in rows:
        mes = r[ix["mes"]].strftime("%Y-%m")
        cte, nfse = r[ix["Total CT-e"]] or 0, r[ix["Total NFS-e"]] or 0
        sist, gnre = r[ix["Sistemico"]] or 0, r[ix["Total GNRE"]] or 0
        m = meses[mes]
        m["cte"] += cte; m["nfse"] += nfse; m["sistemico"] += sist; m["gnre"] += gnre
        por_cliente[mes][str(r[ix["CNPJ Matriz"]])] += cte + nfse + sist + gnre
    # CIOT emitidos por mes: numero informado a mao (nao vem da planilha; nao existia em 2025) — ciot_mensal.json
    try:
        with open(os.path.join(BASE_DIR, "ciot_mensal.json"), encoding="utf-8") as f:
            ciot = json.load(f)
    except (FileNotFoundError, ValueError):
        ciot = {}
    out = {"fonte": os.path.basename(xlsx), "geradoEm": datetime.now().strftime("%Y-%m-%d"), "meses": {}}
    for mes in sorted(meses):
        clientes = sorted(hashlib.sha1(c.encode()).hexdigest()[:8] for c, t in por_cliente[mes].items() if t > 0)
        out["meses"][mes] = {**meses[mes], "ciot": ciot.get(mes, 0), "clientes": clientes}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"salvo {OUT}: {len(out['meses'])} meses ({min(out['meses'])} a {max(out['meses'])})")


if __name__ == "__main__":
    main(sys.argv[1])
