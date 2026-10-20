# -*- coding: utf-8 -*-
"""Busca pontual: TODOS os chamados do Movidesk (qualquer equipe, qualquer data) que mencionam
"tabela de preco" em qualquer campo — assunto, justificativa, tags, campos adicionais e o texto de
qualquer acao (descricao do chamado, respostas, notas internas).

Roda no GitHub Actions (workflow "Buscar tabela de preco (pontual)"), com o token do segredo
MOVIDESK_TOKEN. Grava out/tabela_preco_raw.json (so' chamados com mencao + trechos). Nao grava nada
no repositorio: o workflow sobe o arquivo como artefato de curta duracao, porque o texto dos chamados
tem dado de cliente.

Estrategia: janelas MENSAIS por createdDate, nas duas rotas (/tickets e /tickets/past — a primeira so'
traz chamados atualizados recentemente, a segunda os antigos; uniao por id). Em cada janela o servidor
filtra por 'contains' (barato); depois o Python confere com regex e extrai onde/como aparece.
Limite da API: 10 req/min.
"""
import json
import os
import re
import sys
import time
from datetime import datetime

import requests

TOKEN = os.environ["MOVIDESK_TOKEN"]
BASE = "https://api.movidesk.com/public/v1"
ROTAS = {"tickets": BASE + "/tickets", "past": BASE + "/tickets/past"}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT_DIR, exist_ok=True)

# contains do OData: sem acento e sem a 1a letra, pra pegar Tabela/tabela/TABELA e preco/preço/precos
PADROES = ["abela de pre", "abelas de pre", "abela pre", "abelas pre"]
# conferencia final no Python (aceita "tabela de preço", "tabelas de preços", "tabela preco", "tabela do preço"...)
REGEX = re.compile(r"tabelas?\s+(?:de\s+|do\s+|da\s+|dos\s+|das\s+)?pre[cç]os?", re.I)

SELECT = ("id,protocol,subject,category,urgency,status,baseStatus,createdDate,resolvedIn,closedIn,ownerTeam,origin,"
          "tags,justification,serviceFirstLevel,serviceSecondLevel,serviceThirdLevel,actionCount")
EXPAND = ("owner($select=businessName),clients($expand=organization),"
          "actions($select=id,type,origin,createdDate,description,createdBy),customFieldValues($expand=items)")
EXPAND_SEM_CF = "owner($select=businessName),clients($expand=organization),actions($select=id,type,origin,createdDate,description,createdBy)"
PAGINA = 50
PAUSA = 6.5  # 10 req/min


def clausulas(com_campos_adicionais=True, com_tags=True):
    partes = []
    for p in PADROES:
        partes.append(f"contains(subject,'{p}')")
        partes.append(f"contains(justification,'{p}')")
        partes.append(f"actions/any(a: contains(a/description,'{p}'))")
        if com_tags:
            partes.append(f"tags/any(t: contains(t,'{p}'))")
        if com_campos_adicionais:
            partes.append(f"customFieldValues/any(c: contains(c/value,'{p}'))")
    return " or ".join(partes)


def get(url, params, tentativas=4):
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(url, params={**params, "token": TOKEN}, timeout=180)
            time.sleep(PAUSA)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 400:
                # filtro/expand invalido: quem chamou decide o fallback (nao adianta repetir)
                raise ValueError(f"400: {r.text[:200]}")
            ultimo = f"HTTP {r.status_code}: {r.text[:120]}"
        except requests.exceptions.RequestException as exc:
            ultimo = str(exc)
            time.sleep(PAUSA)
        time.sleep(5 * (i + 1))
    raise RuntimeError(ultimo)


def buscar_janela(rota, inicio, fim, variante):
    """variante: 0 = tudo; 1 = sem campos adicionais; 2 = sem campos adicionais e sem tags."""
    cf, tg = variante == 0, variante <= 1
    filtro = (f"createdDate ge {inicio:%Y-%m-%d}T00:00:00Z and createdDate lt {fim:%Y-%m-%d}T00:00:00Z"
              f" and ({clausulas(cf, tg)})")
    itens, skip = [], 0
    while skip < 5000:
        pagina = get(ROTAS[rota], {"$select": SELECT, "$expand": EXPAND if cf else EXPAND_SEM_CF, "$filter": filtro,
                                   "$orderby": "id asc", "$top": PAGINA, "$skip": skip})
        if not pagina:
            break
        itens += pagina
        skip += len(pagina)
    return itens


def primeiro_mes():
    """Mes do chamado mais antigo existente (nas duas rotas)."""
    datas = []
    for rota in ROTAS:
        try:
            r = get(ROTAS[rota], {"$select": "id,createdDate", "$orderby": "createdDate asc", "$top": 1})
            if r:
                datas.append(r[0]["createdDate"][:7])
        except Exception as exc:  # noqa: BLE001
            print(f"[aviso] primeiro chamado em {rota}: {exc}", flush=True)
    return min(datas) if datas else "2022-01"


def trecho(texto, m, raio=110):
    a, b = max(0, m.start() - raio), min(len(texto), m.end() + raio)
    return ("…" if a else "") + re.sub(r"\s+", " ", texto[a:b]).strip() + ("…" if b < len(texto) else "")


def extrair(t):
    """Onde 'tabela de preco' aparece neste chamado (lista de {campo, trecho, ...})."""
    mencoes = []
    for campo, valor in (("Assunto", t.get("subject")), ("Justificativa", t.get("justification"))):
        if valor and (m := REGEX.search(valor)):
            mencoes.append({"campo": campo, "trecho": trecho(valor, m)})
    for tag in t.get("tags") or []:
        if REGEX.search(tag or ""):
            mencoes.append({"campo": "Tag", "trecho": tag})
    for cf in t.get("customFieldValues") or []:
        textos = [cf.get("value") or ""] + [str((i or {}).get("customFieldItem") or "") for i in (cf.get("items") or [])]
        for tx in textos:
            if tx and (m := REGEX.search(tx)):
                mencoes.append({"campo": f"Campo adicional {cf.get('customFieldId')}", "trecho": trecho(tx, m)})
    nome_acoes = {1: "Interna", 2: "Publica"}
    for n, a in enumerate(sorted(t.get("actions") or [], key=lambda x: x.get("id") or 0), 1):
        desc = a.get("description") or ""
        for m in REGEX.finditer(desc):
            autor = ((a.get("createdBy") or {}).get("businessName")) or ""
            mencoes.append({
                "campo": f"Acao {a.get('id')}" + (" (descricao do chamado)" if a.get("id") == 1 else ""),
                "tipo": nome_acoes.get(a.get("type"), str(a.get("type"))),
                "data": (a.get("createdDate") or "")[:16], "autor": autor, "trecho": trecho(desc, m)})
            break  # 1 trecho por acao basta; a contagem de mencoes usa o numero de acoes/campos
    return mencoes


def org(t):
    nomes = []
    for c in t.get("clients") or []:
        o = c.get("organization") or {}
        n = o.get("businessName") or c.get("businessName") or ""
        if n and n not in nomes:
            nomes.append(n)
    return nomes


def resumo(t, mencoes):
    acoes = sorted(t.get("actions") or [], key=lambda x: x.get("id") or 0)
    primeira = (acoes[0].get("description") or "") if acoes else ""
    return {
        "id": t.get("id"), "protocolo": t.get("protocol"), "assunto": t.get("subject"), "categoria": t.get("category"),
        "urgencia": t.get("urgency"), "status": t.get("status"), "equipe": t.get("ownerTeam"),
        "responsavel": ((t.get("owner") or {}).get("businessName")) or "",
        "clientes": org(t), "aberto_em": t.get("createdDate"), "resolvido_em": t.get("resolvedIn"),
        "fechado_em": t.get("closedIn"), "servico": " > ".join([x for x in (t.get("serviceFirstLevel"), t.get("serviceSecondLevel"), t.get("serviceThirdLevel")) if x]),
        "origem": t.get("origin"), "tags": t.get("tags") or [], "qtd_acoes": t.get("actionCount"),
        "descricao_inicial": re.sub(r"\s+", " ", primeira).strip()[:400],
        "mencoes": mencoes,
    }


def main():
    agora = datetime.utcnow()
    ini = primeiro_mes()
    ano, mes = int(ini[:4]), int(ini[5:7])
    print(f"[info] chamado mais antigo em {ini}; varrendo mes a mes ate {agora:%Y-%m}", flush=True)
    achados = {}
    sem_confirmacao = []
    while (ano, mes) <= (agora.year, agora.month):
        inicio = datetime(ano, mes, 1)
        fim = datetime(ano + (mes == 12), 1 if mes == 12 else mes + 1, 1)
        for rota in ROTAS:
            itens, variante = None, 0
            while itens is None and variante <= 2:
                try:
                    itens = buscar_janela(rota, inicio, fim, variante)
                except ValueError as exc:
                    print(f"[aviso] {rota} {ano}-{mes:02d} variante {variante} rejeitada ({exc}) — tentando filtro mais simples", flush=True)
                    variante += 1
                except RuntimeError as exc:
                    print(f"[erro] {rota} {ano}-{mes:02d}: {exc}", flush=True)
                    sem_confirmacao.append(f"{rota} {ano}-{mes:02d}")
                    break
            for t in itens or []:
                mencoes = extrair(t)
                if mencoes and t["id"] not in achados:  # a regex confirma; o 'contains' do servidor pode ser mais frouxo
                    achados[t["id"]] = resumo(t, mencoes)
        print(f"[info] {ano}-{mes:02d}: acumulado {len(achados)} chamados", flush=True)
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    lista = sorted(achados.values(), key=lambda r: r["aberto_em"] or "")
    with open(os.path.join(OUT_DIR, "tabela_preco_raw.json"), "w", encoding="utf-8") as f:
        json.dump({"geradoEm": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "primeiroMes": ini, "janelasComErro": sem_confirmacao,
                   "total": len(lista), "chamados": lista}, f, ensure_ascii=False)
    print(f"[ok] {len(lista)} chamados com mencao; janelas com erro: {sem_confirmacao or 'nenhuma'}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
