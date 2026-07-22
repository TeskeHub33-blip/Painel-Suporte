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

    # 1. Chamados abertos (com clients/organizacao e reopenedIn, para o relatorio de clientes)
    open_tickets = fetch({
        "$select": "id,protocol,subject,category,urgency,status,ownerTeam,createdDate,lastUpdate,tags,slaSolutionDate,reopenedIn",
        "$expand": "owner($select=businessName),clients,statusHistories",
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
    for offset in range(3):
        target = add_months(now_utc, -offset)
        data = fetch_month(target.year, target.month)
        save(f"resolved_month_{offset}.json", data)


if __name__ == "__main__":
    main()
