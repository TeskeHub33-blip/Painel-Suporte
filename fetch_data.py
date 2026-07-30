# -*- coding: utf-8 -*-
"""Busca os dados do Movidesk usados pelo build_dashboard.py.

Le o token da variavel de ambiente MOVIDESK_TOKEN (nunca hardcoded), pra poder
rodar tanto localmente quanto no GitHub Actions (via repository secret).
"""
import json
import os
from datetime import datetime, timedelta

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://api.movidesk.com/public/v1/tickets"
TOKEN = os.environ["MOVIDESK_TOKEN"]

MONTH_SELECT = "id,protocol,category,urgency,resolvedIn,slaSolutionDate,status,origin,createdDate,resolvedInFirstCall,actionCount,subject,ownerTeam,reopenedIn,tags"
MONTH_EXPAND = "owner($select=businessName),clients,statusHistories"


def fetch(params):
    params = dict(params)
    params["token"] = TOKEN
    resp = requests.get(BASE_URL, params=params, timeout=90)
    resp.raise_for_status()
    return resp.json()


def save(filename, data):
    with open(os.path.join(BASE_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def add_months(dt, delta):
    total = dt.month - 1 + delta
    year = dt.year + total // 12
    month = total % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def month_window(year, month):
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    mid = start + timedelta(days=10)
    return start, mid, end


def fetch_month(year, month):
    start, mid, end = month_window(year, month)

    def fetch_window(a, b):
        return fetch({
            "$select": MONTH_SELECT,
            "$expand": MONTH_EXPAND,
            "$filter": f"resolvedIn ge {a.strftime('%Y-%m-%d')}T00:00:00Z and resolvedIn lt {b.strftime('%Y-%m-%d')}T00:00:00Z",
            "$top": 1000,
        })

    return fetch_window(start, mid) + fetch_window(mid, end)


def main():
    now_utc = datetime.utcnow()
    today_str = now_utc.strftime("%Y-%m-%d")

    # 1. Chamados abertos (com clients/organizacao, reopenedIn, e a 1a acao/descricao do chamado —
    # usada para detectar "carga parada" tambem pelo texto da descricao, nao so pelo assunto)
    open_tickets = fetch({
        "$select": "id,protocol,subject,category,urgency,status,ownerTeam,createdDate,lastUpdate,tags,slaSolutionDate,reopenedIn",
        "$expand": "owner($select=businessName),clients,statusHistories,actions($select=description,type,origin;$top=1)",
        "$filter": "status ne 'Fechado' and status ne 'Cancelado' and status ne 'Resolvido'",
        "$top": 500,
    })
    save("tickets_full.json", open_tickets)

    # 2. Resolvidos hoje
    resolved_today = fetch({
        "$select": "id,protocol,subject,category,status,resolvedIn,resolvedInFirstCall,actionCount,createdDate,origin,ownerTeam",
        "$expand": "owner($select=businessName)",
        "$filter": f"resolvedIn ge {today_str}T00:00:00Z",
        "$top": 200,
    })
    save("resolved_today.json", resolved_today)

    # 3. Resolvidos nos ultimos 3 meses (sempre busca os 3 do zero — nao ha cache entre runs no GitHub Actions)
    resolved_months = {}
    for offset in range(3):
        target = add_months(now_utc, -offset)
        data = fetch_month(target.year, target.month)
        resolved_months[offset] = data
        save(f"resolved_month_{offset}.json", data)

    # 4. Acoes/notas dos chamados tecnicos (Bug/Melhoria/Servicos) resolvidos no mes corrente — usadas
    # pra achar, no log do DevOps/Azure, o comentario que marca quando a task foi para validacao ou
    # ficou em impedimento (o Movidesk nao tem um status proprio pra isso, e uma info que vem via nota).
    target = now_utc
    start, mid, end = month_window(target.year, target.month)

    def fetch_actions_window(a, b):
        return fetch({
            "$select": "id,protocol",
            "$expand": "actions($select=description,createdDate,type)",
            "$filter": (
                f"resolvedIn ge {a.strftime('%Y-%m-%d')}T00:00:00Z and resolvedIn lt {b.strftime('%Y-%m-%d')}T00:00:00Z"
                " and ownerTeam eq 'Suporte'"
                " and (category eq 'Bug' or category eq 'Melhoria' or category eq 'Serviços')"
            ),
            "$top": 1000,
        })

    bug_actions = fetch_actions_window(start, mid) + fetch_actions_window(mid, end)
    save("resolved_month_0_actions.json", bug_actions)

    # 5. Acoes/notas completas dos chamados candidatos a expurgo retroativo de SLA por indisponibilidade
    # de orgao governamental (SEFAZ/ANTT/prefeitura/GNRE) — o Movidesk so criou o status dedicado
    # 'Aguardando Sefaz/ANTT' recentemente, entao pra chamados de antes disso a unica forma de saber e
    # lendo o log/comentario do chamado. Restrito, a pedido, a chamados atendidos (resolvidos) em 2026
    # que estouraram o SLA, mais todos os chamados que ainda estao abertos — nao busca acao de TODOS os
    # chamados resolvidos (custo de payload alto demais), so dos candidatos reais a essa exclusao.
    def fetch_actions_for_ids(ids, chunk_size=20):
        ids = sorted(set(ids))
        out = []
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            filt = " or ".join(f"id eq {tid}" for tid in chunk)
            out += fetch({
                "$select": "id,protocol",
                "$expand": "actions($select=description,createdDate,type)",
                "$filter": filt,
                "$top": chunk_size,
            })
        return out

    gov_check_ids = set()
    for offset, data in resolved_months.items():
        for r in data:
            if (r.get('ownerTeam') == 'Suporte' and r.get('resolvedIn') and r.get('slaSolutionDate')
                    and r['resolvedIn'] > r['slaSolutionDate']
                    and (r.get('resolvedIn') or '').startswith('2026')):
                gov_check_ids.add(r['id'])
    for t in open_tickets:
        if t.get('id') is not None:
            gov_check_ids.add(t['id'])

    gov_actions = fetch_actions_for_ids(gov_check_ids)
    save("gov_check_actions.json", gov_actions)


if __name__ == "__main__":
    main()
