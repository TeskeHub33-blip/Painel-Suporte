# -*- coding: utf-8 -*-
"""Busca os dados do Movidesk usados pelo build_dashboard.py.

Le o token da variavel de ambiente MOVIDESK_TOKEN (nunca hardcoded), pra poder
rodar tanto localmente quanto no GitHub Actions (via repository secret).
"""
import json
import os
import time
from datetime import datetime, timedelta

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://api.movidesk.com/public/v1/tickets"
TOKEN = os.environ["MOVIDESK_TOKEN"]

MONTH_SELECT = "id,protocol,category,urgency,resolvedIn,slaSolutionDate,status,origin,createdDate,resolvedInFirstCall,actionCount,subject,ownerTeam,reopenedIn,tags"
MONTH_EXPAND = "owner($select=businessName),clients,statusHistories"


def fetch(params, retries=2):
    params = dict(params)
    params["token"] = TOKEN
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=90)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(2)
    raise last_exc


# Teto de tempo total pra bisecao de uma pagina problematica — se um erro nao for um registro
# isolado mas algo sistemico (ex.: a API rejeitando por outro motivo, nao um dado corrompido),
# bisectar ate top=1 pode significar centenas de sub-requisicoes. Depois desse teto, desiste do
# resto da pagina (loga um aviso) em vez de travar o job inteiro por muito tempo.
BISECT_DEADLINE_S = 150


def fetch_page_resilient(base_params, skip, top, deadline=None):
    """Busca uma pagina ($skip/$top); se a API devolver erro (ex.: 500 por um registro
    corrompido especifico numa das paginas — o que vinha travando TODA a sincronizacao desde
    2026-08-03 ~19h), particiona a pagina em blocos menores pra isolar e pular so' o(s) registro(s)
    problematicos, em vez de abortar a busca inteira dos chamados abertos.

    Retorna (items, completo). completo=False significa que parte da pagina foi desistida (erro
    persistente ou teto de tempo) — quem chama NAO pode usar len(items) pra decidir se chegou ao
    fim da paginacao, senao uma pagina incompleta (menor que $top so' por ter desistido, nao por
    ser genuinamente a ultima) faz o loop parar cedo demais e perder chamados (foi o que aconteceu:
    parou em ~500, escondendo justamente os chamados mais novos/'Novo'/'Em atendimento')."""
    if deadline is None:
        deadline = time.time() + BISECT_DEADLINE_S
    if time.time() > deadline:
        print(f"[aviso] tempo de bisecao esgotado — pulando o restante da pagina em $skip={skip} $top={top}", flush=True)
        return [], False
    try:
        return fetch({**base_params, "$top": top, "$skip": skip}), True
    except requests.exceptions.RequestException:
        if top <= 1:
            print(f"[aviso] pulando registro problematico em $skip={skip} (a API rejeitou mesmo isolado)", flush=True)
            return [], False
        half = top // 2
        first, ok1 = fetch_page_resilient(base_params, skip, half, deadline)
        second, ok2 = fetch_page_resilient(base_params, skip + half, top - half, deadline)
        return first + second, ok1 and ok2


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


def fetch_paginated(base_params, page_size=500, deadline_s=25):
    """Busca TODAS as paginas de um filtro, com $skip — um $top fixo sem paginacao (usado antes
    pra meses resolvidos) pode voltar incompleto silenciosamente (ex.: por rate-limit da API
    devolvendo menos itens sem erro). Confirmado que a API pode devolver MENOS itens que o $top
    pedido mesmo sem ter chegado ao fim de verdade (ex.: abril/2026 sempre voltava exatamente 89
    chamados criados no mes, mesmo pedindo $top=500 ou $top=5000 — a API aplica um teto proprio,
    bem menor, pra essa consulta pesada com $expand=statusHistories). Por isso NAO da pra usar
    'pagina veio menor que o $top' como sinal de fim — so' avanca $skip pela quantidade REAL
    recebida, e so para quando uma pagina de verdade vier vazia. Usa fetch_page_resilient (com
    bisecao) pra tambem sobreviver a erros 500 pontuais numa pagina especifica. deadline_s baixo
    (bem menor que o usado pros chamados abertos) pra nao deixar um mes com problema comer o tempo
    de todos os outros."""
    items = []
    skip = 0
    while skip < 50000:
        page, completo = fetch_page_resilient(base_params, skip, page_size, time.time() + deadline_s)
        items += page
        if not completo:
            # pagina incompleta (erro/tempo esgotado) nao pode ser confundida com "acabou" — avanca
            # pelo tamanho pedido mesmo sem saber quanto realmente existia ali, pra nao travar.
            skip += page_size
            continue
        if not page:
            break
        skip += len(page)
    return items


def fetch_created_month(year, month):
    """Busca TODOS os chamados CRIADOS num mes (qualquer status), com historico de status
    completo. Diferente de filtrar por resolvedIn (ver comentario grande abaixo sobre o porque),
    createdDate e' um campo estavel — uma vez criado, nunca muda — entao essa busca nao sofre
    o mesmo problema de 'encolher' com o tempo."""
    start, mid, end = month_window(year, month)

    def fetch_window(a, b):
        return fetch_paginated({
            "$select": MONTH_SELECT,
            "$expand": MONTH_EXPAND,
            "$filter": f"createdDate ge {a.strftime('%Y-%m-%d')}T00:00:00Z and createdDate lt {b.strftime('%Y-%m-%d')}T00:00:00Z",
        })

    result = fetch_window(start, mid) + fetch_window(mid, end)
    time.sleep(3)  # respiro generoso — a API parece degradar (devolver poucos itens, sem erro) apos
    # muitas requisicoes seguidas; isso ajuda o proximo mes/janela nao herdar esse estado.
    return result


def first_resolution_month(ticket):
    """Mes (ano, mes) em que o chamado foi resolvido/fechado PELA PRIMEIRA VEZ, usando o
    historico de status — nao o campo resolvedIn atual do chamado.

    Por que nao usar resolvedIn direto: esse campo reflete a resolucao MAIS RECENTE, nao a
    primeira. Um chamado criado e resolvido em abril, mas REABERTO (pela integracao do Azure ou
    por um agente) e resolvido de novo em julho, passa a ter resolvedIn apontando pra julho — ele
    simplesmente desaparece da contagem de abril, mesmo tendo sido resolvido la' originalmente.
    Confirmado isso investigando abril/2026: dezenas de chamados criados naquele mes e resolvidos
    na epoca foram reabertos meses depois, fazendo o filtro `resolvedIn em abril` da API devolver
    so' uma fracao (15 de ~1100+) dos chamados que realmente foram resolvidos pela 1a vez em
    abril. Por isso a busca agora e' por MES DE CRIACAO (campo estavel, nunca muda) e este
    calculo deriva o mes da 1a resolucao a partir do historico de status de cada chamado."""
    hist = ticket.get('statusHistories') or []
    resolvidos = sorted(
        (h for h in hist if h.get('status') in ('Resolvido', 'Fechado') and h.get('changedDate')),
        key=lambda h: h['changedDate'],
    )
    if resolvidos:
        dt_str = resolvidos[0]['changedDate']
    elif ticket.get('resolvedIn'):
        dt_str = ticket['resolvedIn']  # fallback se por algum motivo nao ha statusHistories
    else:
        return None
    dt = datetime.fromisoformat(dt_str.split('.')[0])
    return dt.year, dt.month


# Chamados criados/mes historicamente sempre passam de umas poucas centenas — se um mes voltar
# bem abaixo disso e' sinal de que a API devolveu uma resposta 200 incompleta (sem lancar erro,
# entao nem a bisecao nem os retries do fetch() percebem). Um mes suspeito NAO e salvo/cacheado —
# fica pra tentar de novo no proximo ciclo, em vez de congelar um numero errado pra sempre.
MES_TOTAL_MINIMO_SANIDADE = 700


def main():
    now_utc = datetime.utcnow()
    today_str = now_utc.strftime("%Y-%m-%d")

    # 1. Chamados abertos (com clients/organizacao, reopenedIn, e a 1a acao/descricao do chamado —
    # usada para detectar "carga parada" tambem pelo texto da descricao, nao so pelo assunto).
    # Pagina com $skip ate a API retornar menos que $top — um $top fixo (usado antes) corta
    # silenciosamente os chamados abertos mais recentes assim que o backlog passa desse numero
    # (foi o que aconteceu: com $top=500 e ~744 chamados abertos, os ~244 mais novos sumiam do
    # painel inteiro, nao so' da busca do Fluxograma).
    # customFieldValues($select=customFieldId,items) traz o campo customizado "Motivo de
    # Priorizacao" (customFieldId 248215) usado pra detalhar o motivo do chamado ter sido
    # priorizado (ex.: "Whatsapp", "Carga parada (saida de veiculo)", etc.) — igual ao padrao ja
    # usado pra actions/statusHistories, e' uma colecao relacionada, entao precisa de $expand (nao
    # $select simples).
    open_tickets_base_params = {
        "$select": "id,protocol,subject,category,urgency,status,ownerTeam,createdDate,lastUpdate,tags,slaSolutionDate,reopenedIn,origin",
        "$expand": "owner($select=businessName),clients,statusHistories,actions($select=description,type,origin;$top=1),customFieldValues",
        "$filter": "status ne 'Fechado' and status ne 'Cancelado' and status ne 'Resolvido'",
    }
    open_tickets = []
    page_size = 200
    skip = 0
    paginas_incompletas = 0
    while skip < 20000:  # teto de seguranca — evita loop infinito se a API estiver persistentemente fora
        page, completo = fetch_page_resilient(open_tickets_base_params, skip, page_size)
        open_tickets += page
        if not completo:
            # Pagina incompleta (desistiu por erro/tempo) NAO pode ser confundida com "chegou ao
            # fim" — senao os chamados das paginas seguintes (tipicamente os mais novos) somem do
            # painel inteiro em silencio, como aconteceu antes. Continua avancando mesmo assim.
            paginas_incompletas += 1
            print(f"[aviso] pagina em $skip={skip} ficou incompleta — seguindo para a proxima mesmo assim", flush=True)
            skip += page_size
            continue
        if not page:
            break
        # Igual ao fetch_paginated: uma pagina menor que $top NAO significa fim de verdade — a API
        # pode aplicar um teto proprio menor que o pedido. So avanca pelo tamanho REAL recebido.
        skip += len(page)
    if paginas_incompletas:
        print(f"[aviso] total de paginas incompletas nesta sincronizacao: {paginas_incompletas}", flush=True)
    save("tickets_full.json", open_tickets)

    # 2. Resolvidos hoje
    resolved_today = fetch({
        "$select": "id,protocol,subject,category,status,resolvedIn,resolvedInFirstCall,actionCount,createdDate,origin,ownerTeam",
        "$expand": "owner($select=businessName)",
        "$filter": f"resolvedIn ge {today_str}T00:00:00Z",
        "$top": 200,
    })
    save("resolved_today.json", resolved_today)

    # 3. Resolvidos desde janeiro/2026, agrupados pelo MES DA 1a RESOLUCAO (nao pelo resolvedIn
    # atual — ver o comentario grande na funcao first_resolution_month acima sobre o porque).
    #
    # Passo A: busca os chamados por MES DE CRIACAO (createdDate, campo estavel) — offsets aqui
    # sao relativos ao mes de criacao. offsets 0/1 (mes corrente + anterior) sao buscados de novo
    # em toda sincronizacao; mais antigos que isso sao buscados uma unica vez e ficam em cache
    # (created_raw_N.json, commitado no repo) — uma vez criado, um chamado nunca muda de mes de
    # criacao, entao esse cache nunca fica desatualizado nesse sentido. So' faz o backfill de UM
    # mes de criacao sem cache por execucao (nao todos de uma vez): buscar tudo numa unica
    # execucao levou quase 40 minutos e ainda assim vinha truncado — um mes por vez, com folego
    # entre requisicoes, mantem cada execucao rapida.
    #
    # Passo B: com todos os chamados criados desde jan/2026 disponiveis (cache + frescos), calcula
    # o mes da 1a resolucao de cada um (a partir do statusHistories) e agrupa nesses baldes — essa
    # parte e' recalculada do zero a cada execucao (rapida, em memoria, sem chamada de API), entao
    # os baldes de resolucao sempre refletem o que ja foi buscado ate agora por criacao.
    JAN_2026 = datetime(2026, 1, 1)
    meses_desde_jan2026 = (now_utc.year - JAN_2026.year) * 12 + (now_utc.month - JAN_2026.month) + 1
    MESES_SEMPRE_FRESCOS = 2
    todos_criados = []
    backfill_feito = False
    for offset in range(meses_desde_jan2026):
        path = os.path.join(BASE_DIR, f"created_raw_{offset}.json")
        if offset < MESES_SEMPRE_FRESCOS:
            target = add_months(now_utc, -offset)
            print(f"[info] buscando mes de criacao offset={offset} ({target.year}-{target.month:02d})...", flush=True)
            data = fetch_created_month(target.year, target.month)
            save(f"created_raw_{offset}.json", data)
            print(f"[info] mes de criacao offset={offset}: {len(data)} chamados", flush=True)
        elif os.path.exists(path):
            with open(path, encoding='utf-8-sig') as f:
                data = json.load(f)
        elif not backfill_feito:
            backfill_feito = True
            target = add_months(now_utc, -offset)
            print(f"[info] backfill: buscando mes de criacao historico offset={offset} ({target.year}-{target.month:02d})...", flush=True)
            data = fetch_created_month(target.year, target.month)
            if len(data) < MES_TOTAL_MINIMO_SANIDADE:
                print(f"[aviso] mes de criacao offset={offset} voltou com so' {len(data)} chamados (< {MES_TOTAL_MINIMO_SANIDADE}) — "
                      f"provavel resposta incompleta da API; NAO cacheando, tenta de novo no proximo ciclo", flush=True)
                data = []
            else:
                save(f"created_raw_{offset}.json", data)
                print(f"[info] mes de criacao offset={offset}: {len(data)} chamados — cacheado", flush=True)
        else:
            data = []  # ainda sem cache e o backfill deste ciclo ja foi usado noutro mes
        todos_criados.extend(data)

    # Passo B: agrupa por mes da 1a resolucao (offset relativo ao mes CORRENTE, mesma numeracao
    # 0=corrente/1=anterior/etc. usada pelo resto do painel).
    resolved_months = {offset: [] for offset in range(meses_desde_jan2026)}
    fora_do_periodo = 0
    sem_resolucao = 0
    for t in todos_criados:
        ym = first_resolution_month(t)
        if ym is None:
            sem_resolucao += 1
            continue
        ano, mes = ym
        offset_resolucao = (now_utc.year - ano) * 12 + (now_utc.month - mes)
        if 0 <= offset_resolucao < meses_desde_jan2026:
            resolved_months[offset_resolucao].append(t)
        else:
            fora_do_periodo += 1  # resolvido antes de jan/2026 (chamado antigo reaberto ha pouco) ou no futuro
    print(f"[info] chamados criados desde jan/2026 buscados ate agora: {len(todos_criados)} "
          f"({sem_resolucao} ainda sem resolucao, {fora_do_periodo} resolvidos fora do periodo jan/2026-atual)", flush=True)
    for offset in range(meses_desde_jan2026):
        save(f"resolved_month_{offset}.json", resolved_months[offset])

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
