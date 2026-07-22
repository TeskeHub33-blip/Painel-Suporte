# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "tickets_full.json")
RESOLVED_PATH = os.path.join(BASE_DIR, "resolved_today.json")
LOGO_B64_PATH = os.path.join(BASE_DIR, "ref_assets", "logo_b64.txt")
OUT_PATH = os.path.join(BASE_DIR, "dashboard_suporte.html")

with open(LOGO_B64_PATH, encoding='ascii') as f:
    LOGO_B64 = f.read().strip()

NOW_UTC_STR = sys.argv[1] if len(sys.argv) > 1 else None
now_iso = (NOW_UTC_STR or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
now = datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%S")
now_brasilia = now - timedelta(hours=3)

with open(DATA_PATH, encoding='utf-8-sig') as f:
    raw_tickets = json.load(f)

try:
    with open(RESOLVED_PATH, encoding='utf-8-sig') as f:
        raw_resolved = json.load(f)
except FileNotFoundError:
    raw_resolved = []

def clean_status_histories(raw_list):
    out = []
    for h in (raw_list or []):
        out.append({
            'status': h.get('status'),
            'changedDate': h.get('changedDate'),
            'permanencyTimeFullTime': h.get('permanencyTimeFullTime'),
        })
    return out

GENERIC_EMAIL_DOMAINS = {
    'gmail.com', 'hotmail.com', 'hotmail.com.br', 'outlook.com', 'outlook.com.br',
    'yahoo.com', 'yahoo.com.br', 'live.com', 'live.com.br', 'icloud.com',
    'uol.com.br', 'bol.com.br', 'terra.com.br', 'msn.com',
}

def company_name_from_domain(domain):
    domain = (domain or '').lower().strip()
    if not domain or domain in GENERIC_EMAIL_DOMAINS:
        return None
    # remove sufixos comuns de dominio (.com.br, .com, .ind.br, .net, .me, etc.)
    label = re.sub(r'\.(com|net|org|ind|log|me)(\.br)?$', '', domain)
    label = re.sub(r'\.br$', '', label)
    if not label:
        return None
    words = re.split(r'[.\-_]+', label)
    return ' '.join(w.capitalize() for w in words if w)

def extract_org(clients_list):
    # Sempre resolve para a EMPRESA do cliente, nunca para o nome de uma pessoa fisica:
    # 1) se o Movidesk retornou um client do tipo organizacao (personType == 2), usa o nome dele.
    # 2) senao, tenta inferir a empresa a partir do dominio do e-mail do contato (ignorando
    #    provedores genericos como gmail/hotmail/outlook).
    # 3) se nada disso for possivel, marca como "Sem cliente" (nunca usa nome de pessoa).
    clients_list = clients_list or []
    orgs = [c for c in clients_list if c.get('personType') == 2]
    if orgs:
        return orgs[0].get('businessName') or 'Sem cliente'
    for c in clients_list:
        email = c.get('email') or ''
        m = re.search(r'@([\w.-]+)$', email)
        if m:
            nome = company_name_from_domain(m.group(1))
            if nome:
                return nome
    return 'Sem cliente'

MESES_PT = ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
def month_label(dt):
    return f"{MESES_PT[dt.month-1]}/{dt.year}"

def month_offset_date(base_dt, offset):
    y, m = base_dt.year, base_dt.month - offset
    while m <= 0:
        m += 12
        y -= 1
    return datetime(y, m, 1)

# campos minimos necessarios no cliente (reduz payload e evita vazar HTML de descricao etc.)
clean = []
for t in raw_tickets:
    owner = t.get('owner') or {}
    clean.append({
        'id': t.get('id'),
        'protocol': t.get('protocol'),
        'subject': t.get('subject') or '',
        'category': t.get('category'),
        'urgency': t.get('urgency'),
        'status': t.get('status'),
        'ownerTeam': t.get('ownerTeam'),
        'ownerName': owner.get('businessName') or 'Sem tecnico',
        'createdDate': t.get('createdDate'),
        'lastUpdate': t.get('lastUpdate'),
        'origin': t.get('origin'),
        'chatGroup': t.get('chatGroup'),
        'tags': t.get('tags') or [],
        'slaSolutionDate': t.get('slaSolutionDate'),
        'reopenedIn': t.get('reopenedIn'),
        'clientOrg': extract_org(t.get('clients')),
        'statusHistories': clean_status_histories(t.get('statusHistories')),
    })

clean_resolved = []
for t in raw_resolved:
    owner = t.get('owner') or {}
    clean_resolved.append({
        'id': t.get('id'),
        'protocol': t.get('protocol'),
        'subject': t.get('subject') or '',
        'category': t.get('category'),
        'resolvedIn': t.get('resolvedIn'),
        'resolvedInFirstCall': bool(t.get('resolvedInFirstCall')),
        'actionCount': t.get('actionCount'),
        'origin': t.get('origin'),
        'ownerName': owner.get('businessName') or 'Sem tecnico',
        'ownerTeam': t.get('ownerTeam'),
    })

def clean_month_record(t, keep_status_histories):
    owner = t.get('owner') or {}
    rec = {
        'id': t.get('id'),
        'protocol': t.get('protocol'),
        'subject': t.get('subject') or '',
        'category': t.get('category') or 'Sem categoria',
        'urgency': t.get('urgency') or 'Sem urgencia',
        'resolvedIn': t.get('resolvedIn'),
        'slaSolutionDate': t.get('slaSolutionDate'),
        'origin': t.get('origin'),
        'ownerName': owner.get('businessName') or 'Sem tecnico',
        'createdDate': t.get('createdDate'),
        'resolvedInFirstCall': bool(t.get('resolvedInFirstCall')),
        'actionCount': t.get('actionCount'),
        'ownerTeam': t.get('ownerTeam'),
        'reopenedIn': t.get('reopenedIn'),
        'clientOrg': extract_org(t.get('clients')),
        'tags': t.get('tags') or [],
    }
    if keep_status_histories:
        rec['statusHistories'] = clean_status_histories(t.get('statusHistories'))
    return rec

# Carrega os 3 meses (0 = corrente, 1 = mes anterior, 2 = dois meses atras).
# statusHistories so e mantido para o mes corrente (usado nas metricas de Bug da aba Historico).
resolved_months_clean = {}
month_labels = {}
for offset in range(3):
    path = os.path.join(BASE_DIR, f"resolved_month_{offset}.json")
    try:
        with open(path, encoding='utf-8-sig') as f:
            raw = json.load(f)
    except FileNotFoundError:
        raw = []
    resolved_months_clean[str(offset)] = [clean_month_record(t, offset == 0) for t in raw]
    month_labels[str(offset)] = month_label(month_offset_date(now, offset))

clean_resolved_month = resolved_months_clean['0']  # mantem nome usado no resto do script (mes corrente)

tickets_json = json.dumps(clean, ensure_ascii=False)
resolved_json = json.dumps(clean_resolved, ensure_ascii=False)
resolved_month_json = json.dumps(clean_resolved_month, ensure_ascii=False)
resolved_months_json = json.dumps(resolved_months_clean, ensure_ascii=False)
month_labels_json = json.dumps(month_labels, ensure_ascii=False)

html = rf"""<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  /* Identidade visual EmiteAi — variante escura (mesma paleta navy/pink, superficies invertidas) */
  --navy: #EAEAF2;
  --navy-mid: #C9C9DC;
  --navy-lt: #B8B8D0;
  --pink: #ED6DA2;
  --pink2: #E05592;
  --pink-dim: rgba(237,109,162,0.14);
  --pink-logo: #E8386D;
  --bg: #1B1B33;
  --panel: #242444;
  --panel-border: rgba(255,255,255,0.10);
  --surface2: #2D2D52;
  --text: #EAEAF2;
  --text-dim: #A5A5BD;
  --text3: #82829C;
  --ok: #34D399;
  --ok-solid: #10B981;
  --ok-dim: rgba(16,185,129,0.15);
  --ok-bord: rgba(52,211,153,0.35);
  --warn: #FBBF24;
  --warn-solid: #F59E0B;
  --warn-dim: rgba(245,158,11,0.15);
  --warn-bord: rgba(251,191,36,0.35);
  --danger: #F87171;
  --danger-solid: #EF4444;
  --danger-dim: rgba(239,68,68,0.15);
  --danger-bord: rgba(248,113,113,0.35);
  --shadow: rgba(0,0,0,0.35) 0px 2px 8px 0px;
  --shadow2: rgba(0,0,0,0.5) 0px 6px 18px 0px;
}}
* {{ box-sizing: border-box; }}
body, .dashboard-root {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', 'Poppins', 'Segoe UI', sans-serif;
  margin: 0;
  min-height: 100vh;
  overflow-x: hidden;
}}
.dashboard-root {{ padding: 26px 34px; }}
.header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; background: var(--panel); border-radius: 6px; padding: 14px 22px; box-shadow: var(--shadow); }}
.header-left {{ display: flex; align-items: center; gap: 16px; }}
.logo-img {{
  height: 40px; width: auto; flex-shrink: 0; display: block;
}}
.header h1 {{ font-size: 24px; margin: 0; font-weight: 400; letter-spacing: 0; color: var(--text); }}
.header .subtitle {{ color: var(--text3); font-size: 13px; margin-top: 2px; }}
.header-right {{ text-align: right; font-size: 13px; color: var(--text3); }}
.header-right .clock {{ font-size: 20px; color: var(--navy); font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.5px; }}

.tabs {{ display: flex; gap: 8px; margin-bottom: 18px; }}
.tab-btn {{
  background: var(--panel); border: 1.25px solid #878799; color: var(--navy);
  font-family: inherit; font-size: 13px; font-weight: 600; padding: 9px 20px; border-radius: 6px;
  cursor: pointer; letter-spacing: 0; transition: all .15s ease; box-shadow: var(--shadow);
}}
.tab-btn:hover {{ background: rgba(255,255,255,0.06); border-color: var(--navy); }}
.tab-btn.active {{ background: var(--pink-dim); color: var(--pink); border-color: rgba(232,56,109,0.3); font-weight: 700; }}
.tab-btn:focus-visible {{ outline: 2px solid var(--pink); outline-offset: 2px; }}
.tab-panel {{ display: none; }}
.itil-select {{
  background: var(--panel); color: var(--text); border: 0.625px solid #878799;
  border-radius: 6px; padding: 9px 12px; font-family: inherit; font-size: 13px; min-width: 180px;
}}
.itil-select:focus {{ outline: none; border-color: var(--navy); border-width: 1.5px; }}
.tab-panel.active {{ display: block; }}

.kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 14px; }}
.kpi {{ background: var(--panel); border: none; border-radius: 6px; padding: 16px 18px; cursor: pointer; transition: box-shadow .15s ease; box-shadow: var(--shadow); position: relative; overflow: hidden; }}
.kpi::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--text3); }}
.kpi:hover {{ box-shadow: var(--shadow2); }}
.kpi:focus-visible {{ outline: 2px solid var(--pink); outline-offset: 2px; }}
.kpi .value {{ font-size: 22px; font-weight: 700; line-height: 1.2; font-variant-numeric: tabular-nums; letter-spacing: -0.5px; color: var(--navy); }}
.kpi .label {{ color: var(--text3); font-size: 11px; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; }}
.kpi .hint {{ color: var(--text3); font-size: 10.5px; margin-top: 4px; }}
.kpi.danger::before {{ background: var(--danger-solid); }}
.kpi.danger .value {{ color: var(--danger); }}
.kpi.warn::before {{ background: var(--warn-solid); }}
.kpi.warn .value {{ color: var(--warn); }}
.kpi.ok::before {{ background: var(--ok-solid); }}
.kpi.ok .value {{ color: var(--ok); }}
.kpi.neutral::before {{ background: var(--navy); }}
.kpi.neutral .value {{ color: var(--navy); }}
.kpi.pink::before {{ background: var(--pink); }}
.kpi.pink .value {{ color: var(--pink); }}

.grid {{ display: flex; flex-wrap: wrap; align-items: flex-start; gap: 18px; }}
.grid > .panel {{ flex: 1 1 auto; width: 300px; }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 18px; }}
.panel {{ background: var(--panel); border: none; border-radius: 6px; padding: 16px 18px; min-height: 280px; box-shadow: var(--shadow); }}
.panel.resizable {{ position: relative; overflow: auto; min-width: 260px; min-height: 180px; }}
.panel.resizable.dragging {{ opacity: 0.35; }}
.panel.resizable.drag-over {{ box-shadow: 0 0 0 2px var(--pink); }}
.resize-handle {{
  position: absolute; right: 0; bottom: 0; width: 18px; height: 18px;
  cursor: nwse-resize; z-index: 5;
  background: linear-gradient(135deg, transparent 0 50%, var(--panel-border) 50% 60%, transparent 60% 70%, var(--panel-border) 70% 80%, transparent 80%);
}}
.resize-handle:hover {{ background: linear-gradient(135deg, transparent 0 50%, var(--pink) 50% 60%, transparent 60% 70%, var(--pink) 70% 80%, transparent 80%); }}
.drag-handle {{
  cursor: grab; user-select: none; color: var(--text3); font-size: 14px;
  padding: 0 4px; margin-left: auto; flex-shrink: 0;
}}
.drag-handle:active {{ cursor: grabbing; }}
.panel h2 {{ justify-content: space-between; }}
.export-btn {{
  cursor: pointer; user-select: none; font-size: 11px; font-weight: 600; color: var(--navy);
  border: 1.25px solid #878799; border-radius: 6px; padding: 4px 9px; white-space: nowrap;
  transition: all .15s ease;
}}
.export-btn:hover {{ background: rgba(255,255,255,0.06); border-color: var(--navy); }}
.panel h2 .export-btn {{ margin-left: 6px; }}
.panel h2 {{ font-size: 16px; font-weight: 600; margin: 0 0 4px 0; display: flex; align-items: center; gap: 8px; color: var(--text); }}
.panel .panel-sub {{ color: var(--text3); font-size: 11.5px; margin-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
th {{ text-align: center; color: var(--text); font-weight: 600; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.6px; padding: 8px 6px; background: var(--surface2); border-bottom: 1px solid var(--panel-border); }}
td {{ padding: 8px 6px; border-bottom: 1px solid var(--panel-border); vertical-align: top; }}
.col-id {{ color: var(--text3); width: 92px; font-variant-numeric: tabular-nums; }}
.col-subject {{ max-width: 260px; }}
.col-team {{ color: var(--text-dim); width: 110px; font-size: 11.5px; }}
.col-status {{ width: 90px; font-size: 11px; font-weight: 700; }}
.col-time {{ width: 80px; font-size: 12px; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }}
.stalest {{ color: var(--danger); }}
.ticket-link {{ color: var(--pink); text-decoration: none; font-weight: 600; }}
.ticket-link:hover {{ text-decoration: underline; color: var(--pink2); }}
.hist-bar-row {{ cursor: pointer !important; }}
.hist-row {{ cursor: pointer; }}
.hist-row:hover td {{ background: rgba(255,255,255,0.03); }}
tr.clickable-row {{ cursor: pointer; }}
tr.clickable-row:hover td {{ background: rgba(255,255,255,0.03); }}

.bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 7px; cursor: pointer; padding: 2px 4px; border-radius: 6px; }}
.bar-row:hover {{ background: rgba(255,255,255,0.05); }}
.bar-label {{ width: 150px; font-size: 11.5px; color: var(--text-dim); flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bar-track {{ flex: 1; background: var(--surface2); border-radius: 6px; height: 12px; overflow: hidden; }}
.bar-fill {{ background: var(--pink); height: 100%; }}
.bar-value {{ width: 26px; text-align: right; font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; color: var(--text); }}
.empty-msg {{ color: var(--text3); font-size: 12px; padding: 8px 0; }}

.footer-note {{ margin-top: 18px; text-align: center; color: var(--text3); font-size: 10.5px; }}

.tier-badge {{ display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; }}
.tier-1 {{ background: var(--danger-dim); color: var(--danger); border: 1px solid var(--danger-bord); }}
.tier-2 {{ background: var(--warn-dim); color: var(--warn); border: 1px solid var(--warn-bord); }}
.tier-3 {{ background: var(--ok-dim); color: var(--ok); border: 1px solid var(--ok-bord); }}
.tier-4 {{ background: var(--surface2); color: var(--text3); border: 1px solid var(--panel-border); }}
.col-tier {{ width: 130px; }}

.priority-panel {{ margin-bottom: 18px; }}
.priority-panel table {{ font-size: 12.5px; }}

.sla-cat-row {{ display: grid; grid-template-columns: 1fr 70px 70px 70px; gap: 8px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--panel-border); font-size: 12px; }}
.sla-cat-row.head {{ color: var(--text3); font-size: 10.5px; text-transform: uppercase; font-weight: 600; text-align: center; letter-spacing: 0.6px; }}
.sla-cat-name {{ color: var(--text); }}
.sla-cat-num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 700; color: var(--text); }}
.sla-cat-num.danger {{ color: var(--danger); }}

.modal-overlay {{
  position: fixed; inset: 0; background: rgba(26,26,44,0.45);
  display: none; align-items: center; justify-content: center; z-index: 50;
  backdrop-filter: blur(2px);
}}
.modal-overlay.open {{ display: flex; }}
.modal-box {{
  background: var(--panel); border: none; border-radius: 6px;
  width: min(920px, 92vw); max-height: 82vh; display: flex; flex-direction: column;
  box-shadow: 0 24px 64px rgba(26,26,44,0.22), 0 4px 16px rgba(0,0,0,0.10);
}}
.modal-head {{ display: flex; justify-content: space-between; align-items: center; padding: 21px 26px 16px; }}
.modal-head h3 {{ margin: 0; font-size: 20px; font-weight: 600; color: var(--text); }}
.modal-head .modal-count {{ color: var(--text3); font-size: 13px; margin-top: 2px; }}
.modal-close {{ background: transparent; border: none; color: var(--text3); width: 32px; height: 32px; border-radius: 6px; font-size: 16px; cursor: pointer; transition: all .15s; }}
.modal-close:hover {{ color: var(--text); background: var(--surface2); }}
.modal-body {{ overflow-y: auto; padding: 6px 26px 20px 26px; }}

@media (prefers-reduced-motion: reduce) {{ .kpi {{ transition: none; }} }}
</style>

<div class="dashboard-root">
  <div class="header">
    <div class="header-left">
      <img class="logo-img" src="data:image/png;base64,{LOGO_B64}" alt="EmiteAi" />
      <div>
        <h1>Painel Diario</h1>
        <div class="subtitle">Visao executiva ao vivo dos chamados Movidesk · clique em qualquer numero para ver a lista</div>
      </div>
    </div>
    <div class="header-right">
      <div class="clock" id="clock">--:--:--</div>
      <div>Dados de {now_brasilia.strftime('%d/%m/%Y %H:%M')} (Brasilia)</div>
    </div>
  </div>

  <div class="tabs">
    <button class="tab-btn active" id="tabBtnLive" onclick="showTab('live')">Ao Vivo</button>
    <button class="tab-btn" id="tabBtnHist" onclick="showTab('hist')">Historico</button>
    <button class="tab-btn" id="tabBtnClientes" onclick="showTab('clientes')">Clientes</button>
    <button class="tab-btn" id="tabBtnOneOnOne" onclick="showTab('oneOnOne')">One-on-One</button>
    <button class="tab-btn" id="tabBtnGamificacao" onclick="showTab('gamificacao')">Gamificacao</button>
  </div>

  <div class="tab-panel active" id="tabLive">
    <div class="kpi-row" id="kpiRow"></div>
    <div class="kpi-row" id="kpiRow2" style="grid-template-columns: repeat(4, 1fr); margin-top: -4px;"></div>

    <div class="panel" id="chatsLivePanel" style="margin-top: 18px;"></div>

    <div class="grid" id="gridTop"></div>

    <div class="panel priority-panel" id="priorityPanel" style="margin-top: 18px;"></div>

    <div class="grid" id="gridBottom" style="grid-template-columns: repeat(2, 1fr); margin-top: 18px;"></div>
  </div>

  <div class="tab-panel" id="tabHist">
    <div style="display:flex; justify-content:flex-end; margin-bottom: 10px;">
      <select id="selClienteHistorico" class="itil-select" title="Filtrar todos os cards do mes por um cliente especifico" style="max-width:220px; font-size:12px; padding:4px 8px;"></select>
    </div>
    <div class="kpi-row" id="kpiRowHist" style="grid-template-columns: repeat(4, 1fr);"></div>
    <div class="kpi-row" id="kpiRowHistMttr" style="grid-template-columns: repeat(1, 1fr); margin-top:-4px;"></div>
    <div class="panel-sub" style="margin: 12px 0 4px 2px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-dim); font-weight: 700;">Ciclo de vida do Bug — urgencia Media</div>
    <div class="kpi-row" id="kpiRowHistBugMedia" style="grid-template-columns: repeat(3, 1fr);"></div>
    <div class="panel-sub" style="margin: 12px 0 4px 2px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-dim); font-weight: 700;">Ciclo de vida do Bug — urgencia Alta</div>
    <div class="kpi-row" id="kpiRowHistBugAlta" style="grid-template-columns: repeat(3, 1fr);"></div>
    <div class="grid" id="gridHist" style="grid-template-columns: 1fr 1fr; margin-top: 18px;"></div>
  </div>

  <div class="tab-panel" id="tabClientes">
    <div style="display:flex; justify-content:flex-end; gap:8px; margin-bottom: 10px;">
      <select id="selMesCliente" class="itil-select" title="Mes" style="max-width:160px; font-size:12px; padding:4px 8px;"></select>
      <select id="selCliente" class="itil-select" title="Cliente" style="max-width:220px; font-size:12px; padding:4px 8px;"></select>
    </div>
    <div class="kpi-row" id="kpiCliente" style="grid-template-columns: repeat(5, 1fr);"></div>
    <div class="grid" id="gridCliente" style="margin-top: 18px;"></div>
  </div>

  <div class="tab-panel" id="tabOneOnOne">
    <div class="panel" id="oneOnOneGate" style="max-width: 420px; margin: 60px auto; text-align:center;">
      <h2 style="justify-content:center;">🔒 Acesso restrito</h2>
      <div class="panel-sub" style="text-align:center; margin-bottom:14px;">Esta aba e de uso da lideranca. Informe a senha para continuar.</div>
      <input id="oneOnOnePassInput" type="password" class="itil-select" style="width:100%; text-align:center; margin-bottom:10px;" placeholder="Senha" />
      <div><span class="export-btn" style="padding:8px 22px; font-size:13px;" onclick="checkOneOnOnePassword()">Entrar</span></div>
      <div id="oneOnOneError" style="color:var(--danger); font-size:12px; margin-top:10px; display:none;">Senha incorreta.</div>
    </div>
    <div id="oneOnOneContent" style="display:none;">
      <div style="display:flex; justify-content:flex-end; align-items:center; gap:8px; margin-bottom: 10px;">
        <span id="tierBadgeOneOnOne" style="font-size:12px; font-weight:700; padding:5px 12px; border-radius:20px;"></span>
        <select id="selPeriodoOneOnOne" class="itil-select" title="Periodo" style="max-width:160px; font-size:12px; padding:4px 8px;"></select>
        <select id="selTecnicoOneOnOne" class="itil-select" title="Responsavel" style="max-width:220px; font-size:12px; padding:4px 8px;"></select>
      </div>
      <div class="kpi-row" id="kpiOneOnOne" style="grid-template-columns: repeat(3, 1fr);"></div>
      <div class="kpi-row" id="kpiOneOnOne2" style="grid-template-columns: repeat(3, 1fr); margin-top:-4px;"></div>
      <div class="kpi-row" id="kpiOneOnOneMetas" style="grid-template-columns: repeat(3, 1fr); margin-top:-4px;"></div>
      <div class="kpi-row" id="kpiOneOnOneN2" style="grid-template-columns: repeat(3, 1fr); margin-top:-4px;"></div>
    </div>
  </div>

  <div class="tab-panel" id="tabGamificacao">
    <div class="panel" id="gamificacaoGate" style="max-width: 420px; margin: 60px auto; text-align:center;">
      <h2 style="justify-content:center;">🔒 Acesso restrito</h2>
      <div class="panel-sub" style="text-align:center; margin-bottom:14px;">Esta aba e de uso da lideranca. Informe a senha para continuar.</div>
      <input id="gamificacaoPassInput" type="password" class="itil-select" style="width:100%; text-align:center; margin-bottom:10px;" placeholder="Senha" />
      <div><span class="export-btn" style="padding:8px 22px; font-size:13px;" onclick="checkGamificacaoPassword()">Entrar</span></div>
      <div id="gamificacaoError" style="color:var(--danger); font-size:12px; margin-top:10px; display:none;">Senha incorreta.</div>
    </div>
    <div id="gamificacaoContent" style="display:none;">
      <div style="display:flex; justify-content:flex-end; margin-bottom: 10px;">
        <select id="selMesGamificacao" class="itil-select" title="Mes / periodo" style="max-width:220px; font-size:12px; padding:4px 8px;"></select>
      </div>
      <div class="kpi-row" id="kpiGamificacao" style="grid-template-columns: repeat(2, 1fr);"></div>
      <div class="grid" id="gridGamificacao" style="margin-top: 18px;"></div>
    </div>
  </div>

  <div class="footer-note">
    Board gerado a partir do Movidesk (chamados nao fechados/cancelados/resolvidos) · Atualizacao agendada a cada 5 minutos · "Bouncing" = Em atendimento sem update ha 48h+ · "Contraturno" = chamados em atendimento com Alife Caetano dos Santos ou Vinicius Campestrini
  </div>
</div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <h3 id="modalTitle">Chamados</h3>
        <div class="modal-count" id="modalCount"></div>
      </div>
      <div style="display:flex; align-items:center; gap:10px;">
        <span class="export-btn" title="Exportar para Excel (.txt)" onclick="exportCurrentModal()">⬇ Excel</span>
        <button class="modal-close" id="modalCloseBtn" aria-label="Fechar">✕</button>
      </div>
    </div>
    <div class="modal-body">
      <table>
        <thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th id="modalTimeHeader">Tempo</th></tr></thead>
        <tbody id="modalTbody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const MOVIDESK_BASE = 'https://emiteai.movidesk.com/Ticket/Edit/';
const TICKETS = {tickets_json};
// Historico (resolvidos por tecnico, SLA, indicadores) considera somente o time de Suporte
const RESOLVED_TODAY = ({resolved_json}).filter(r => r.ownerTeam === 'Suporte');
const RESOLVED_MONTH_ALL = ({resolved_month_json}).filter(r => r.ownerTeam === 'Suporte');
// RESOLVED_MONTH e chatsMes ficam mutaveis (let) porque a aba Historico pode filtrar por cliente
// e reatribui-los em renderHistoricoMes() — assim os modais de drill-down (openModalHist*) sempre
// refletem o filtro de cliente atualmente selecionado.
let RESOLVED_MONTH = RESOLVED_MONTH_ALL;
let chatsMes = [];
const RESOLVED_MONTHS_RAW = {resolved_months_json};
const MONTH_LABELS = {month_labels_json};
// Todos os 3 meses, ja restritos ao time de Suporte (mesmo criterio do resto do Historico)
const RESOLVED_MONTHS = {{}};
Object.keys(RESOLVED_MONTHS_RAW).forEach(k => {{
  RESOLVED_MONTHS[k] = RESOLVED_MONTHS_RAW[k].filter(r => r.ownerTeam === 'Suporte');
}});
const NOW = new Date("{now_iso}Z");
const TODAY_STR = NOW.toISOString().slice(0,10);

function parseDt(s) {{ return s ? new Date(s.split('.')[0] + 'Z') : null; }}
TICKETS.forEach(t => {{
  t._created = parseDt(t.createdDate);
  t._lastUpdate = parseDt(t.lastUpdate);
  t._sla = parseDt(t.slaSolutionDate);
  t._hoursOpen = t._created ? (NOW - t._created) / 3600000 : null;
  t._hoursSinceUpdate = t._lastUpdate ? (NOW - t._lastUpdate) / 3600000 : null;
  t._slaHoursLeft = t._sla ? (t._sla - NOW) / 3600000 : null;
  t._slaVencido = t._slaHoursLeft !== null && t._slaHoursLeft < 0;
  t._updatedToday = t._lastUpdate ? t._lastUpdate.toISOString().slice(0,10) === TODAY_STR : false;
  t._isPriorizado = (t.tags || []).some(tg => (tg||'').toLowerCase().indexOf('priorizado') !== -1);
}});

// Alife e Vinicius sao os tecnicos do turno de contraturno
const CONTRATURNO_TECNICOS = ['Alife Caetano dos Santos', 'Vinicius Campestrini'];

// "Carga parada": carga travada, ou problema na emissao de CIOT/MDFe/CTe
const CARGA_PARADA_RE = /carga\s*(trava|parad)|travad|\bciot\b|\bmdf[-\s]?e\b|\bct[-\s]?e\b/i;

// Classificacao incorreta: Melhoria, Bug e (alguns) Servicos legitimamente tem task associada
// (passam pela fila de Bugs/dev). Duvida, Erro Operacional e Terceiros NAO deveriam ter task —
// se um desses tiver passado pela fila de Bugs, e sinal real de categoria errada.
const BUG_QUEUE_STATUS = 'Aguardando Desenvolvimento - fila Bugs';
const CATEGORIAS_SEM_TASK = ['Dúvida', 'Erro Operacional', 'Terceiros'];
TICKETS.forEach(t => {{
  const passouPorFilaBugs = (t.statusHistories||[]).some(h => h.status === BUG_QUEUE_STATUS);
  t._classificacaoIncorreta = CATEGORIAS_SEM_TASK.indexOf(t.category) !== -1 && passouPorFilaBugs;
  t._motivoClassificacao = 'categoria "' + t.category + '" com task associada (fila de Bugs)';
}});

const FILTERS = {{
  novos: t => t.status === 'Novo',
  emAtendimento: t => t.status === 'Em atendimento',
  aguardandoCliente: t => t.status === 'Aguardando Cliente',
  bouncing: t => t.ownerTeam === 'Suporte' && t.status === 'Em atendimento' && t._hoursSinceUpdate !== null && t._hoursSinceUpdate >= 48,
  priorizados: t => t.ownerTeam === 'Suporte' && t._isPriorizado,
  contraturno: t => t.status === 'Em atendimento' && CONTRATURNO_TECNICOS.indexOf(t.ownerName) !== -1,
  naoAtualizadosHoje: t => (t.status === 'Em atendimento' || t.status === 'Aguardando Cliente') && !t._updatedToday,
  cargaParada: t => t.status === 'Em atendimento' && CARGA_PARADA_RE.test(t.subject || ''),
  classificacaoIncorreta: t => t._classificacaoIncorreta,
  chatsEmAtendimento: t => t.status === 'Em atendimento' && (t.origin === 24 || !!t.chatGroup),
  chatsAguardando: t => t.status === 'Novo' && (t.origin === 24 || !!t.chatGroup),
}};

// --- Priorizacao operacional ---
// Ordem de atendimento pedida: 1) bloqueio operacional (MDFe/CIOT/GNRE/integracoes/carga travada,
// cadeia logistica conectada) -> 2) risco fiscal (possiveis multas) -> 3) recorrencias/melhorias estruturais -> 4) demais.
const OPERACIONAL_RE = /mdf[-\s]?e|\bciot\b|\bgnre\b|integra[cç][aã]o|carga\s*(trava|parad)|travad/i;
const FISCAL_RISCO_RE = /multa|risco fiscal|imposto|difal|\bicms\b|vencimento.*guia|guia.*vencid/i;

function normalizeSubject(s) {{
  return (s || '').toLowerCase().replace(/[^a-z0-9à-ü ]/g, '').replace(/\s+/g, ' ').trim();
}}
const subjectCounts = {{}};
TICKETS.forEach(t => {{
  const key = normalizeSubject(t.subject);
  if (key) subjectCounts[key] = (subjectCounts[key] || 0) + 1;
}});

function priorityTier(t) {{
  const s = t.subject || '';
  const isFiscal = FISCAL_RISCO_RE.test(s);
  const isOperacional = OPERACIONAL_RE.test(s);
  const isRecorrente = subjectCounts[normalizeSubject(s)] > 1;
  if (isOperacional && !isFiscal) return 1;
  if (isFiscal) return 2;
  if (t.category === 'Melhoria' || isRecorrente) return 3;
  return 4;
}}
const TIER_INFO = {{
  1: {{ label: 'Bloqueio operacional', cls: 'tier-1' }},
  2: {{ label: 'Risco fiscal (multas)', cls: 'tier-2' }},
  3: {{ label: 'Recorrencia / melhoria', cls: 'tier-3' }},
  4: {{ label: 'Outros', cls: 'tier-4' }},
}};
const ATIVOS = TICKETS.filter(t => t.status !== 'Aguardando Time CS' || true); // todos os TICKETS ja sao nao-fechados
ATIVOS.forEach(t => {{ t._tier = priorityTier(t); }});
const filaPriorizada = ATIVOS.slice().sort((a,b) => {{
  if (a._tier !== b._tier) return a._tier - b._tier;
  return (b._hoursOpen||0) - (a._hoursOpen||0);
}});

function apply(name) {{ return TICKETS.filter(FILTERS[name]); }}
function fmtH(h) {{
  if (h === null || h === undefined) return '-';
  if (h < 24) return h.toFixed(1) + 'h';
  return (h/24).toFixed(1) + 'd';
}}
function esc(s) {{
  return (s === null || s === undefined) ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
// String literal em aspas simples para uso dentro de atributos onclick="..." (que usam aspas duplas) —
// evita que nomes de cliente/categoria com aspas duplas quebrem o parsing do atributo HTML.
function jsStr(s) {{
  return "'" + String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
}}

function byTecnico(items) {{
  const agg = {{}};
  items.forEach(t => {{ agg[t.ownerName] = (agg[t.ownerName]||0) + 1; }});
  return Object.entries(agg).sort((a,b) => b[1]-a[1]);
}}

function barsHtml(aggEntries, filterName, maxRows) {{
  maxRows = maxRows || 10;
  if (!aggEntries.length) return '<div class="empty-msg">Nenhum registro</div>';
  const top = Math.max(...aggEntries.map(e => e[1]));
  return aggEntries.slice(0, maxRows).map(([name, count]) => `
    <div class="bar-row" onclick="openModalTecnico('${{filterName}}', '${{name.replace(/'/g, "\\\\'")}}')">
      <div class="bar-label">${{esc(name)}}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${{(count/top*100).toFixed(0)}}%"></div></div>
      <div class="bar-value">${{count}}</div>
    </div>`).join('');
}}

function ticketLink(id, protocol) {{
  return `<a href="${{MOVIDESK_BASE}}${{id}}" target="_blank" rel="noopener" class="ticket-link">${{esc(protocol)}}</a>`;
}}
function rowHtml(t, timeField) {{
  const timeVal = timeField === 'update' ? t._hoursSinceUpdate : t._hoursOpen;
  const cls = (timeField === 'update' && timeVal !== null && timeVal >= 48) ? 'stalest' : '';
  return `<tr>
    <td class="col-id">${{ticketLink(t.id, t.protocol)}}</td>
    <td class="col-subject">${{esc((t.subject||'').slice(0,60))}}</td>
    <td class="col-team">${{esc(t.ownerName)}}</td>
    <td class="col-status">${{esc(t.status)}}</td>
    <td class="col-time ${{cls}}">${{fmtH(timeVal)}}</td>
  </tr>`;
}}

function tableHtml(items, timeField, maxRows) {{
  maxRows = maxRows || 12;
  if (!items.length) return '<tr><td colspan="5" class="empty-msg">Nenhum chamado</td></tr>';
  return items.slice(0, maxRows).map(t => rowHtml(t, timeField)).join('');
}}

function rowHtmlTier(t) {{
  const info = TIER_INFO[t._tier];
  return `<tr>
    <td class="col-tier"><span class="tier-badge ${{info.cls}}">${{info.label}}</span></td>
    <td class="col-id">${{ticketLink(t.id, t.protocol)}}</td>
    <td class="col-subject">${{esc((t.subject||'').slice(0,55))}}</td>
    <td class="col-team">${{esc(t.ownerName)}}</td>
    <td class="col-status">${{esc(t.status)}}</td>
    <td class="col-time">${{fmtH(t._hoursOpen)}}</td>
  </tr>`;
}}
function tableHtmlTier(items, maxRows) {{
  maxRows = maxRows || 20;
  if (!items.length) return '<tr><td colspan="6" class="empty-msg">Nenhum chamado</td></tr>';
  return items.slice(0, maxRows).map(rowHtmlTier).join('');
}}

function rowHtmlMisclass(t) {{
  return `<tr>
    <td class="col-id">${{ticketLink(t.id, t.protocol)}}</td>
    <td class="col-subject">${{esc((t.subject||'').slice(0,50))}}</td>
    <td class="col-status">${{esc(t.category)}}</td>
    <td class="col-team">${{esc(t._motivoClassificacao)}}</td>
    <td class="col-team">${{esc(t.ownerName)}}</td>
  </tr>`;
}}
function tableHtmlMisclass(items, maxRows) {{
  maxRows = maxRows || 14;
  if (!items.length) return '<tr><td colspan="5" class="empty-msg">Nenhum chamado sinalizado</td></tr>';
  return items.slice(0, maxRows).map(rowHtmlMisclass).join('');
}}

const LABELS = {{
  novos: 'Chamados novos',
  emAtendimento: 'Em atendimento',
  aguardandoCliente: 'Aguardando cliente',
  bouncing: 'Bouncing — Em atendimento parado ha mais de 2 dias',
  priorizados: 'Priorizados (WhatsApp)',
  naoAtualizadosHoje: 'Nao atualizados hoje',
  contraturno: 'Contraturno (Alife e Vinicius) — em atendimento',
  cargaParada: 'Carga parada / emissao CIOT-MDFe-CTe',
  classificacaoIncorreta: 'Possivel classificacao incorreta',
  chatsEmAtendimento: 'Chats em atendimento (aproximado)',
  chatsAguardando: 'Chats aguardando atendimento (aproximado)',
}};

function openModal(name) {{
  const items = apply(name);
  renderModal(LABELS[name] || name, items, name === 'bouncing' ? 'update' : 'open');
}}
function openModalTecnico(name, tecnico) {{
  const items = apply(name).filter(t => t.ownerName === tecnico);
  renderModal((LABELS[name]||name) + ' — ' + tecnico, items, name === 'bouncing' ? 'update' : 'open');
}}
// --- Exportacao para Excel (via .txt separado por tabulacao — o sandbox do Artifact so libera .txt/.json/.md) ---
function exportTxt(filename, headers, rows) {{
  const escCell = v => String(v === null || v === undefined ? '' : v).replace(/\t/g, ' ').replace(/\r?\n/g, ' ');
  const lines = [headers.join('\t')].concat(rows.map(r => headers.map(h => escCell(r[h])).join('\t')));
  const content = '﻿' + lines.join('\r\n');
  if (!window.claude || !window.claude.downloads) {{
    alert('Exportacao nao disponivel neste ambiente.');
    return;
  }}
  window.claude.downloads.save({{filename, data: content}}).catch(err => {{
    console.error('export failed', err);
    if (err && err.code !== 'declined') alert('Nao foi possivel exportar: ' + (err.message || err.code));
  }});
}}
function exportLiveList(items, filename) {{
  const headers = ['Protocolo','Assunto','Tecnico','Status','AbertoHoras'];
  const rows = items.map(t => ({{
    Protocolo: t.protocol, Assunto: t.subject, Tecnico: t.ownerName, Status: t.status,
    AbertoHoras: (t._hoursOpen != null ? t._hoursOpen.toFixed(1) : '')
  }}));
  exportTxt(filename, headers, rows);
}}
function exportHistListToExcel(items, filename) {{
  const headers = ['Protocolo','Assunto','Tecnico','Categoria','ResolvidoEm'];
  const rows = items.map(r => ({{
    Protocolo: r.protocol, Assunto: r.subject, Tecnico: r.ownerName, Categoria: r.category, ResolvidoEm: fmtDate(r.resolvedIn)
  }}));
  exportTxt(filename, headers, rows);
}}
function exportButtonHtml(onclickExpr, title) {{
  return `<span class="export-btn" title="${{title || 'Exportar para Excel (.txt)'}}" onclick="${{onclickExpr}}">⬇ Excel</span>`;
}}

let CURRENT_MODAL_ITEMS = [];
let CURRENT_MODAL_KIND = 'live';
function exportCurrentModal() {{
  const fname = 'chamados_' + Date.now() + '.txt';
  if (CURRENT_MODAL_KIND === 'hist') exportHistListToExcel(CURRENT_MODAL_ITEMS, fname);
  else exportLiveList(CURRENT_MODAL_ITEMS, fname);
}}

function renderModal(title, items, timeField) {{
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalCount').textContent = items.length + ' chamado(s)';
  document.getElementById('modalTimeHeader').textContent = timeField === 'update' ? 'Parado ha' : 'Aberto ha';
  document.getElementById('modalTbody').innerHTML = tableHtml(items.sort((a,b) => (b._hoursOpen||0)-(a._hoursOpen||0)), timeField, 200);
  document.getElementById('modalOverlay').classList.add('open');
  CURRENT_MODAL_ITEMS = items;
  CURRENT_MODAL_KIND = 'live';
}}

// --- Historico: modal com os chamados por tras de cada media/barra/categoria ---
function fmtDate(s) {{
  const d = parseDt(s);
  if (!d) return '-';
  return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', {{hour:'2-digit', minute:'2-digit'}});
}}
function rowHtmlHist(r) {{
  return `<tr class="hist-row">
    <td class="col-id">${{ticketLink(r.id, r.protocol)}}</td>
    <td class="col-subject">${{esc((r.subject||'').slice(0,60))}}</td>
    <td class="col-team">${{esc(r.ownerName)}}</td>
    <td class="col-status">${{esc(r.category)}}</td>
    <td class="col-time">${{fmtDate(r.resolvedIn)}}</td>
  </tr>`;
}}
function tableHtmlHist(items, maxRows) {{
  maxRows = maxRows || 300;
  if (!items.length) return '<tr><td colspan="5" class="empty-msg">Nenhum chamado</td></tr>';
  return items.slice(0, maxRows).map(rowHtmlHist).join('');
}}
function renderModalHist(title, items) {{
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalCount').textContent = items.length + ' chamado(s)';
  document.getElementById('modalTimeHeader').textContent = 'Resolvido em';
  const sorted = items.slice().sort((a,b) => new Date(b.resolvedIn) - new Date(a.resolvedIn));
  document.getElementById('modalTbody').innerHTML = tableHtmlHist(sorted);
  document.getElementById('modalOverlay').classList.add('open');
  CURRENT_MODAL_ITEMS = sorted;
  CURRENT_MODAL_KIND = 'hist';
}}
function openModalHistTecnico(source, tecnico) {{
  const items = (source === 'chats' ? chatsMes : RESOLVED_MONTH).filter(r => r.ownerName === tecnico);
  const label = source === 'chats' ? 'Chats resolvidos' : 'Chamados resolvidos';
  renderModalHist(`${{label}} — ${{tecnico}} (mes)`, items);
}}
function openModalHistCategoria(cat) {{
  const items = RESOLVED_MONTH.filter(r => (r.category || 'Sem categoria') === cat && r.slaSolutionDate);
  renderModalHist(`SLA — ${{cat}} (mes)`, items);
}}
function openModalHistSimple(kind) {{
  if (kind === 'primeiraRespostaHoje') renderModalHist('Resolvidos c/ 1a resposta (hoje)', RESOLVED_TODAY.filter(isPrimeiraResposta));
  else if (kind === 'primeiraRespostaMes') renderModalHist('Resolvidos c/ 1a resposta (mes)', RESOLVED_MONTH.filter(isPrimeiraResposta));
  else if (kind === 'slaNoPrazoMes') renderModalHist('Fora do SLA (mes) — todas categorias', RESOLVED_MONTH.filter(r => {{
    if (!r.slaSolutionDate) return false;
    const resolvedIn = parseDt(r.resolvedIn); const slaDate = parseDt(r.slaSolutionDate);
    return resolvedIn && slaDate && resolvedIn > slaDate;
  }}));
  else if (kind === 'chatsMes') renderModalHist('Chats resolvidos (mes)', chatsMes);
}}
document.getElementById('modalCloseBtn').addEventListener('click', () => {{
  document.getElementById('modalOverlay').classList.remove('open');
}});
document.getElementById('modalOverlay').addEventListener('click', (e) => {{
  if (e.target.id === 'modalOverlay') e.currentTarget.classList.remove('open');
}});
document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape') document.getElementById('modalOverlay').classList.remove('open');
}});

// Titulos/nomes dos cards principais podem ser editados (duplo clique) — a alteracao fica
// salva no localStorage deste navegador e sobrevive a atualizacoes automaticas dos dados.
function labelKey(rawLabel) {{
  let h = 0;
  for (let i = 0; i < rawLabel.length; i++) {{ h = (h * 31 + rawLabel.charCodeAt(i)) | 0; }}
  return 'labelOverride_' + h;
}}
function saveLabelOverride(el, key) {{
  el.contentEditable = 'false';
  const text = el.textContent.trim();
  if (text) localStorage.setItem(key, text); else localStorage.removeItem(key);
}}
function editableLabel(rawLabel) {{
  const key = labelKey(rawLabel);
  const saved = localStorage.getItem(key);
  const displayHtml = saved ? esc(saved) : rawLabel;
  return `<div class="label" title="Duplo clique para renomear"
    ondblclick="event.stopPropagation(); this.contentEditable='true'; this.focus();"
    onmousedown="if(this.isContentEditable) event.stopPropagation();"
    onblur="saveLabelOverride(this, '${{key}}')"
    onkeydown="if(event.key==='Enter'){{event.preventDefault(); this.blur();}} event.stopPropagation();"
  >${{displayHtml}}</div>`;
}}

function kpiTile(cls, count, label, filterName, hint) {{
  return `<div class="kpi ${{cls}}" tabindex="0" role="button" onclick="openModal('${{filterName}}')" onkeydown="if(event.key==='Enter')openModal('${{filterName}}')">
    <div class="value">${{count}}</div>
    ${{editableLabel(label)}}
    ${{hint ? `<div class="hint">${{hint}}</div>` : ''}}
  </div>`;
}}
function kpiTileStatic(cls, count, label, hint) {{
  return `<div class="kpi ${{cls}}">
    <div class="value">${{count}}</div>
    ${{editableLabel(label)}}
    ${{hint ? `<div class="hint">${{hint}}</div>` : ''}}
  </div>`;
}}
function kpiTileHist(cls, count, label, kind, hint) {{
  return `<div class="kpi ${{cls}}" tabindex="0" role="button" onclick="openModalHistSimple('${{kind}}')" onkeydown="if(event.key==='Enter')openModalHistSimple('${{kind}}')">
    <div class="value">${{count}}</div>
    ${{editableLabel(label)}}
    ${{hint ? `<div class="hint">${{hint}}</div>` : ''}}
  </div>`;
}}

function showTab(name, skipSave) {{
  document.getElementById('tabLive').classList.toggle('active', name === 'live');
  document.getElementById('tabHist').classList.toggle('active', name === 'hist');
  document.getElementById('tabClientes').classList.toggle('active', name === 'clientes');
  document.getElementById('tabOneOnOne').classList.toggle('active', name === 'oneOnOne');
  document.getElementById('tabGamificacao').classList.toggle('active', name === 'gamificacao');
  document.getElementById('tabBtnLive').classList.toggle('active', name === 'live');
  document.getElementById('tabBtnHist').classList.toggle('active', name === 'hist');
  document.getElementById('tabBtnClientes').classList.toggle('active', name === 'clientes');
  document.getElementById('tabBtnOneOnOne').classList.toggle('active', name === 'oneOnOne');
  document.getElementById('tabBtnGamificacao').classList.toggle('active', name === 'gamificacao');
  if (!skipSave) localStorage.setItem('activeTab', name);
}}
// Restaura a aba ativa apos o auto-refresh da pagina (nunca restaura direto em abas com senha, exige senha de novo)
const _savedTab = localStorage.getItem('activeTab') || 'live';
showTab((_savedTab === 'oneOnOne' || _savedTab === 'gamificacao') ? 'live' : _savedTab, true);

// Resolvidos com 1a resposta (hoje e no mes)
// Regra: chamado aberto e resolvido com no maximo 2 respostas (abertura + 1 retorno que ja resolveu),
// ou seja actionCount <= 3 (abertura do cliente + retorno automatico + a resposta que resolveu).
// Isso substitui o campo nativo resolvedInFirstCall do Movidesk, que usa outro criterio.
const FIRST_RESPONSE_MAX_ACTIONS = 3;
function isPrimeiraResposta(r) {{
  return typeof r.actionCount === 'number' && r.actionCount <= FIRST_RESPONSE_MAX_ACTIONS;
}}

const resolvidosHoje = RESOLVED_TODAY.length;
const resolvidosPrimeiraRespostaHoje = RESOLVED_TODAY.filter(isPrimeiraResposta).length;
const pctPrimeiraRespostaHoje = resolvidosHoje ? Math.round(resolvidosPrimeiraRespostaHoje / resolvidosHoje * 100) : 0;

const resolvidosMes = RESOLVED_MONTH.length;
const resolvidosPrimeiraRespostaMes = RESOLVED_MONTH.filter(isPrimeiraResposta).length;
const pctPrimeiraRespostaMes = resolvidosMes ? Math.round(resolvidosPrimeiraRespostaMes / resolvidosMes * 100) : 0;

// SLA por categoria — somente chamados RESOLVIDOS dentro do mes corrente,
// comparando data de resolucao contra o prazo de SLA (slaSolutionDate)
const slaPorCategoria = {{}};
RESOLVED_MONTH.filter(r => r.slaSolutionDate).forEach(r => {{
  const cat = r.category || 'Sem categoria';
  if (!slaPorCategoria[cat]) slaPorCategoria[cat] = {{ total: 0, noPrazo: 0 }};
  slaPorCategoria[cat].total++;
  const resolvedIn = parseDt(r.resolvedIn);
  const slaDate = parseDt(r.slaSolutionDate);
  if (resolvedIn && slaDate && resolvedIn <= slaDate) slaPorCategoria[cat].noPrazo++;
}});
const slaCategoriasOrdenadas = Object.entries(slaPorCategoria).sort((a,b) => (a[1].noPrazo/a[1].total) - (b[1].noPrazo/b[1].total));
const totalComSla = Object.values(slaPorCategoria).reduce((s,v)=>s+v.total,0);
const totalSlaNoPrazo = Object.values(slaPorCategoria).reduce((s,v)=>s+v.noPrazo,0);
const pctSlaNoPrazoGeral = totalComSla ? Math.round(totalSlaNoPrazo/totalComSla*100) : 0;

// Chats — historico (origin 24 no Movidesk), resolvidos no mes e hoje
chatsMes = RESOLVED_MONTH.filter(r => r.origin === 24);
const chatsHoje = RESOLVED_TODAY.filter(r => r.origin === 24);
const pctChatsMes = RESOLVED_MONTH.length ? Math.round(chatsMes.length / RESOLVED_MONTH.length * 100) : 0;
const chatsPorTecnico = byTecnicoResolved(chatsMes);
const resolvidosPorTecnicoMes = byTecnicoResolved(RESOLVED_MONTH);

function byTecnicoResolved(items) {{
  const agg = {{}};
  items.forEach(r => {{ agg[r.ownerName] = (agg[r.ownerName]||0) + 1; }});
  return Object.entries(agg).sort((a,b) => b[1]-a[1]);
}}

// --- Ciclo de vida do Bug (chamados categoria Bug, resolvidos no mes) ---
// Baseado no historico de status (statusHistories) de cada chamado:
// - "tempo para abrir bug": da criacao do chamado ate a 1a vez que entrou na fila de Bugs
// - "tempo em devops": soma do tempo (todas as passagens) no status 'Aguardando Desenvolvimento - fila Bugs'
// - "tempo em validacao": tempo em 'Em atendimento'/'Aguardando Cliente' APOS a ultima saida da fila de Bugs, ate resolver
const bugsMes = RESOLVED_MONTH.filter(r => r.category === 'Bug' && (r.statusHistories||[]).length);
const bugMetrics = bugsMes.map(r => {{
  const hist = r.statusHistories.map(h => ({{ ...h, _d: parseDt(h.changedDate) }})).sort((a,b) => a._d - b._d);
  const created = parseDt(r.createdDate);
  const firstBugQueue = hist.find(h => h.status === BUG_QUEUE_STATUS);
  const tempoParaAbrirH = (firstBugQueue && created) ? (firstBugQueue._d - created) / 3600000 : null;

  const devopsSeconds = hist.filter(h => h.status === BUG_QUEUE_STATUS)
    .reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0);

  let lastBugQueueIdx = -1;
  hist.forEach((h,i) => {{ if (h.status === BUG_QUEUE_STATUS) lastBugQueueIdx = i; }});
  const validacaoSeconds = lastBugQueueIdx >= 0
    ? hist.slice(lastBugQueueIdx+1)
        .filter(h => h.status === 'Em atendimento' || h.status === 'Aguardando Cliente')
        .reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0)
    : null;

  return {{
    protocol: r.protocol,
    urgency: r.urgency,
    ownerName: r.ownerName,
    tempoParaAbrirH,
    devopsH: devopsSeconds / 3600,
    validacaoH: validacaoSeconds !== null ? validacaoSeconds / 3600 : null,
    passouPorDevops: lastBugQueueIdx >= 0,
  }};
}});
function avg(arr) {{ return arr.length ? arr.reduce((s,v)=>s+v,0) / arr.length : null; }}

// Meta = 10% de melhoria ao mes sobre a media dos ultimos 3 meses.
// Para metricas onde MENOR e melhor (tempo, quantidade de problema) a meta e a media * 0.9.
// Para metricas onde MAIOR e melhor (percentuais de qualidade/SLA) a meta e a media * 1.1 (limitado a 100%).
function metaMelhoria10(mediaBase, menorEhMelhor) {{
  if (mediaBase === null || mediaBase === undefined) return null;
  const meta = menorEhMelhor ? mediaBase * 0.9 : Math.min(100, mediaBase * 1.1);
  return meta;
}}
function bateMeta(atual, meta, menorEhMelhor) {{
  if (atual === null || meta === null) return null;
  return menorEhMelhor ? atual <= meta : atual >= meta;
}}

// Media dos ultimos 3 meses (usada como referencia em varios cards) — so' cobre campos
// disponiveis em todos os meses (statusHistories so' fica no mes corrente, entao metricas
// de ciclo de vida do Bug nao entram aqui).
function statsForMonth(items) {{
  const total = items.length;
  const primeira = items.filter(isPrimeiraResposta).length;
  const pctPrimeira = total ? Math.round(primeira / total * 100) : 0;
  const comSla = items.filter(r => r.slaSolutionDate);
  const noPrazo = comSla.filter(r => parseDt(r.resolvedIn) <= parseDt(r.slaSolutionDate)).length;
  const pctSla = comSla.length ? Math.round(noPrazo / comSla.length * 100) : 0;
  const chats = items.filter(r => r.origin === 24).length;
  const mttrH = avg(items.filter(r => r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 3600000));
  return {{ total, pctPrimeira, pctSla, chats, mttrH }};
}}
const statsPorMes3 = Object.keys(RESOLVED_MONTHS).map(k => ({{ key: k, ...statsForMonth(RESOLVED_MONTHS[k]) }}));
const media3Meses = {{
  total: Math.round(avg(statsPorMes3.map(s => s.total))),
  pctPrimeira: Math.round(avg(statsPorMes3.map(s => s.pctPrimeira))),
  pctSla: Math.round(avg(statsPorMes3.map(s => s.pctSla))),
  chats: Math.round(avg(statsPorMes3.map(s => s.chats))),
  mttrH: avg(statsPorMes3.filter(s => s.mttrH !== null).map(s => s.mttrH)),
}};
const comparativoMttr = statsPorMes3.map(s => `${{MONTH_LABELS[s.key].split('/')[0].slice(0,3)}}: ${{s.mttrH !== null ? fmtH(s.mttrH) : '-'}}`).join(' · ');

function bugMetricsFor(urgency) {{
  const subset = urgency ? bugMetrics.filter(b => b.urgency === urgency) : bugMetrics;
  const comAbertura = subset.filter(b => b.tempoParaAbrirH !== null).map(b => b.tempoParaAbrirH);
  const comDevops = subset.filter(b => b.passouPorDevops).map(b => b.devopsH);
  const comValidacao = subset.filter(b => b.validacaoH !== null).map(b => b.validacaoH);
  return {{
    total: subset.length,
    comAbertura, comDevops, comValidacao,
    mediaParaAbrirBug: avg(comAbertura),
    mediaDevops: avg(comDevops),
    mediaValidacao: avg(comValidacao),
  }};
}}
const bugMetricsMedia = bugMetricsFor('Média');
const bugMetricsAlta = bugMetricsFor('Alta');

// ============================================================
// N1/N2 — configuracao dos tecnicos de nivel 2 (o restante do time e considerado N1).
// Edite esta lista com os nomes exatos (iguais ao Movidesk) dos tecnicos N2.
// ============================================================
const N2_TECNICOS = ['Alife Caetano dos Santos', 'Vinicius Campestrini', 'Vitor Hugo Siegel da Silva', 'Gabriel Schmitt Müller', 'Monique A. Zeferino', 'Anderson Gustavo Fischer'];
function tierDoTecnico(tecnico) {{ return N2_TECNICOS.indexOf(tecnico) !== -1 ? 'N2' : 'N1'; }}

const CATEGORIAS_TECNICAS_N2 = ['Bug', 'Melhoria', 'Serviços'];
function cicloVidaTecnicaPorItem(r) {{
  if (!(r.statusHistories || []).length) return null;
  const hist = r.statusHistories.map(h => ({{ ...h, _d: parseDt(h.changedDate) }})).sort((a,b) => a._d - b._d);
  const devopsSeconds = hist.filter(h => h.status === BUG_QUEUE_STATUS).reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0);
  let lastIdx = -1;
  hist.forEach((h,i) => {{ if (h.status === BUG_QUEUE_STATUS) lastIdx = i; }});
  const validacaoSeconds = lastIdx >= 0
    ? hist.slice(lastIdx+1).filter(h => h.status === 'Em atendimento' || h.status === 'Aguardando Cliente').reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0)
    : null;
  return {{ passouPorTask: lastIdx >= 0, devopsH: devopsSeconds / 3600, validacaoH: validacaoSeconds !== null ? validacaoSeconds / 3600 : null }};
}}
// So' disponivel para o mes corrente (offset 0) — statusHistories nao e mantido nos meses anteriores.
function computeN2Metrics(tecnico, periodoKey) {{
  if (periodoKey !== '0') return null;
  const items = (RESOLVED_MONTHS['0'] || []).filter(r => r.ownerName === tecnico && CATEGORIAS_TECNICAS_N2.indexOf(r.category) !== -1);
  const ciclos = items.map(cicloVidaTecnicaPorItem).filter(Boolean);
  const total = items.length;
  const comTask = ciclos.filter(c => c.passouPorTask).length;
  return {{
    total,
    pctTask: total ? Math.round(comTask / total * 100) : null,
    devopsMedio: avg(ciclos.filter(c => c.passouPorTask).map(c => c.devopsH)),
    validacaoMedio: avg(ciclos.filter(c => c.validacaoH !== null).map(c => c.validacaoH)),
  }};
}}

// Media da equipe (N1 ou N2) no periodo selecionado — media simples entre os tecnicos do mesmo nivel.
function mediaEquipe(periodoKey, tier) {{
  const items = RESOLVED_MONTHS[periodoKey] || [];
  const tecnicos = Array.from(new Set(items.map(r => r.ownerName).filter(Boolean))).filter(t => tierDoTecnico(t) === tier);
  const porTecnico = tecnicos.map(t => {{
    const seus = items.filter(r => r.ownerName === t);
    const ind = computeIndicadores(seus);
    const pctPrimeira = seus.length ? Math.round(seus.filter(isPrimeiraResposta).length / seus.length * 100) : null;
    return {{ ...ind, pctPrimeira }};
  }});
  return {{
    total: avg(porTecnico.map(i => i.total)),
    pctPrimeira: avg(porTecnico.filter(i => i.pctPrimeira !== null).map(i => i.pctPrimeira)),
    mttrH: avg(porTecnico.filter(i => i.mttrH !== null).map(i => i.mttrH)),
    pctSla: avg(porTecnico.filter(i => i.pctSla !== null).map(i => i.pctSla)),
    qtdTecnicos: tecnicos.length,
  }};
}}

// Media (baseline) dos ultimos 3 meses de um tecnico especifico — usada tanto no One-on-One
// quanto na Gamificacao para calcular a meta de 10% de melhoria.
function indicadoresTecnico3Meses(tecnico) {{
  const porMesRaw = Object.keys(RESOLVED_MONTHS).map(k => {{
    const items = (RESOLVED_MONTHS[k]||[]).filter(r => r.ownerName === tecnico);
    const ind = computeIndicadores(items);
    const pctPrimeira = items.length ? Math.round(items.filter(isPrimeiraResposta).length / items.length * 100) : null;
    return {{ ...ind, pctPrimeira, label: MONTH_LABELS[k].split('/')[0].slice(0,3) }};
  }});
  const comparativoTotal = porMesRaw.map(i => `${{i.label}}: ${{i.total}}`).join(' · ');
  return {{
    total: avg(porMesRaw.map(i => i.total)),
    pctPrimeira: avg(porMesRaw.filter(i => i.pctPrimeira !== null).map(i => i.pctPrimeira)),
    mttrH: avg(porMesRaw.filter(i => i.mttrH !== null).map(i => i.mttrH)),
    pctSla: avg(porMesRaw.filter(i => i.pctSla !== null).map(i => i.pctSla)),
    comparativoTotal,
  }};
}}

// Metas de um tecnico num mes especifico (X de 3 batidas) — usado na Gamificacao e reaproveitavel
// pelo One-on-One. Baseado na propria media de 3 meses do tecnico, com 10% de melhoria.
function metasDoTecnicoNoMes(tecnico, mesKey) {{
  const items = (RESOLVED_MONTHS[mesKey] || []).filter(r => r.ownerName === tecnico);
  const ind = computeIndicadores(items);
  const pctPrimeira = items.length ? Math.round(items.filter(isPrimeiraResposta).length / items.length * 100) : null;
  const m3 = indicadoresTecnico3Meses(tecnico);
  const metaMttr = metaMelhoria10(m3.mttrH, true);
  const metaSla = metaMelhoria10(m3.pctSla, false);
  const metaPrimeira = metaMelhoria10(m3.pctPrimeira, false);
  const itens = [
    {{ nome: 'MTTR', bateu: bateMeta(ind.mttrH, metaMttr, true) }},
    {{ nome: 'SLA no prazo', bateu: bateMeta(ind.pctSla, metaSla, false) }},
    {{ nome: '1a resposta', bateu: bateMeta(pctPrimeira, metaPrimeira, false) }},
  ];
  const validas = itens.filter(i => i.bateu !== null);
  const batidas = validas.filter(i => i.bateu).length;
  return {{ itens, batidas, total: validas.length, temDados: items.length > 0 }};
}}

const novos = apply('novos');
const emAtendimento = apply('emAtendimento');
const aguardandoCliente = apply('aguardandoCliente');
const bouncing = apply('bouncing');
const priorizados = apply('priorizados');
const naoAtualizadosHoje = apply('naoAtualizadosHoje');
const contraturno = apply('contraturno');
const cargaParada = apply('cargaParada');
const classificacaoIncorreta = apply('classificacaoIncorreta');
const chatsEmAtendimentoLive = apply('chatsEmAtendimento');

document.getElementById('kpiRow').innerHTML =
  kpiTile('neutral', novos.length, 'Novos (aguard. atend.)', 'novos') +
  kpiTile('neutral', emAtendimento.length, 'Em atendimento', 'emAtendimento') +
  kpiTile(aguardandoCliente.length === 0 ? 'ok' : 'warn', aguardandoCliente.length, 'Aguardando cliente', 'aguardandoCliente') +
  kpiTile(bouncing.length === 0 ? 'ok' : 'danger', bouncing.length, 'Bouncing (Em atend. &gt;2 dias)', 'bouncing');

// Tempo medio de resolucao: priorizados vs nao-priorizados (chamados resolvidos no mes, time Suporte)
const resolvidosComTag = RESOLVED_MONTH_ALL.map(r => ({{
  ...r,
  _isPriorizado: (r.tags || []).some(tg => (tg||'').toLowerCase().indexOf('priorizado') !== -1),
}}));
const mttrPriorizados = avg(resolvidosComTag.filter(r => r._isPriorizado && r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 3600000));
const mttrNaoPriorizados = avg(resolvidosComTag.filter(r => !r._isPriorizado && r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 3600000));
const hintPriorizados = `Tempo medio de resolucao (mes) — priorizados: ${{mttrPriorizados !== null ? fmtH(mttrPriorizados) : '-'}} · nao priorizados: ${{mttrNaoPriorizados !== null ? fmtH(mttrNaoPriorizados) : '-'}}`;

document.getElementById('kpiRow2').innerHTML =
  kpiTile('neutral', priorizados.length, 'Priorizados (WhatsApp)', 'priorizados', hintPriorizados) +
  kpiTile('neutral', contraturno.length, 'Contraturno em atendimento', 'contraturno') +
  kpiTile(cargaParada.length === 0 ? 'ok' : 'danger', cargaParada.length, 'Carga parada / CIOT-MDFe-CTe', 'cargaParada') +
  kpiTile(classificacaoIncorreta.length === 0 ? 'ok' : 'warn', classificacaoIncorreta.length, 'Possivel classificacao incorreta', 'classificacaoIncorreta');

document.getElementById('chatsLivePanel').innerHTML = `
  <h2>💬 Chats em atendimento — quem e ha quanto tempo${{exportButtonHtml("exportLiveList(chatsEmAtendimentoLive, 'chats_em_atendimento.txt')")}}</h2>
  <div class="panel-sub">${{chatsEmAtendimentoLive.length}} chamados de origem chat em atendimento agora (tempo desde a ultima atualizacao)</div>
  <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Tempo</th></tr></thead>
    <tbody>${{tableHtml(chatsEmAtendimentoLive.sort((a,b)=>(b._hoursSinceUpdate||0)-(a._hoursSinceUpdate||0)), 'update', 20)}}</tbody></table>
`;

const metaPctPrimeira = metaMelhoria10(media3Meses.pctPrimeira, false);
const metaPctSla = metaMelhoria10(media3Meses.pctSla, false);
document.getElementById('kpiRowHist').innerHTML =
  kpiTileHist('ok', resolvidosPrimeiraRespostaHoje, 'Resolvidos c/ 1a resposta (hoje)', 'primeiraRespostaHoje', `${{pctPrimeiraRespostaHoje}}% de ${{resolvidosHoje}} resolvidos hoje`) +
  kpiTileHist(bateMeta(pctPrimeiraRespostaMes, metaPctPrimeira, false) ? 'ok' : 'warn', resolvidosPrimeiraRespostaMes, 'Resolvidos c/ 1a resposta (mes)', 'primeiraRespostaMes', `${{pctPrimeiraRespostaMes}}% de ${{resolvidosMes}} resolvidos no mes · media 3m: ${{media3Meses.pctPrimeira}}% · meta (+10%/mes): ${{metaPctPrimeira !== null ? Math.round(metaPctPrimeira)+'%' : '-'}}`) +
  kpiTileHist(bateMeta(pctSlaNoPrazoGeral, metaPctSla, false) ? 'ok' : 'danger', `${{pctSlaNoPrazoGeral}}%`, 'SLA atendido no prazo (mes)', 'slaNoPrazoMes', `${{totalSlaNoPrazo}} de ${{totalComSla}} resolvidos com SLA definido · media 3m: ${{media3Meses.pctSla}}% · meta (+10%/mes): ${{metaPctSla !== null ? Math.round(metaPctSla)+'%' : '-'}} (clique p/ ver os fora do prazo)`) +
  kpiTileHist('neutral', chatsMes.length, 'Chats resolvidos (mes)', 'chatsMes', `${{pctChatsMes}}% do total resolvido no mes · ${{chatsHoje.length}} hoje · media 3m: ${{media3Meses.chats}}`);

const mttrMesAtual = statsPorMes3.find(s => s.key === '0').mttrH;
const metaMttr = metaMelhoria10(media3Meses.mttrH, true);
const mttrBateMeta = bateMeta(mttrMesAtual, metaMttr, true);
document.getElementById('kpiRowHistMttr').innerHTML =
  kpiTileStatic(mttrBateMeta === null ? 'warn' : (mttrBateMeta ? 'ok' : 'danger'), mttrMesAtual !== null ? fmtH(mttrMesAtual) : '-', 'Tempo medio de atendimento (MTTR)', `mes corrente: ${{MONTH_LABELS['0']}} · media 3m: ${{media3Meses.mttrH !== null ? fmtH(media3Meses.mttrH) : '-'}} · meta (10% menor que a media 3m): ${{metaMttr !== null ? fmtH(metaMttr) : '-'}} · ultimos 3 meses: ${{comparativoMttr}}`);

function renderBugMetricsRow(elId, m) {{
  // Sem meta/limite definido para estes 3 tempos — cor neutra (nao ha "bom"/"ruim" estabelecido ainda).
  document.getElementById(elId).innerHTML =
    kpiTileStatic('neutral', m.mediaParaAbrirBug!==null ? fmtH(m.mediaParaAbrirBug) : '-', 'Tempo medio para abrir bug', `media sobre ${{m.comAbertura.length}} de ${{m.total}} bugs`) +
    kpiTileStatic('neutral', m.mediaDevops!==null ? fmtH(m.mediaDevops) : '-', 'Tempo medio aberto no devops', `media sobre ${{m.comDevops.length}} bugs que passaram pela fila`) +
    kpiTileStatic('neutral', m.mediaValidacao!==null ? fmtH(m.mediaValidacao) : '-', 'Tempo medio em validacao', `media sobre ${{m.comValidacao.length}} bugs pos-devops`);
}}
renderBugMetricsRow('kpiRowHistBugMedia', bugMetricsMedia);
renderBugMetricsRow('kpiRowHistBugAlta', bugMetricsAlta);

document.getElementById('priorityPanel').innerHTML = `
  <h2>🎯 Fila de priorizacao operacional${{exportButtonHtml("exportLiveList(filaPriorizada, 'fila_priorizacao.txt')")}}</h2>
  <div class="panel-sub">Ordem: bloqueio operacional (MDFe/CIOT/GNRE/integracoes/carga travada) → risco fiscal (multas) → recorrencia/melhoria → demais. Dentro de cada grupo, mais antigo primeiro.</div>
  <table>
    <thead><tr><th>Prioridade</th><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Aberto ha</th></tr></thead>
    <tbody>${{tableHtmlTier(filaPriorizada, 20)}}</tbody>
  </table>
`;

document.getElementById('gridTop').innerHTML = `
  <div class="panel">
    <h2>👤 Em atendimento por tecnico</h2>
    <div class="panel-sub">${{emAtendimento.length}} chamados em atendimento agora — clique num tecnico para ver a lista</div>
    <div id="barsEmAtendimento"></div>
  </div>
  <div class="panel">
    <h2>🕓 Nao atualizados hoje por tecnico</h2>
    <div class="panel-sub">${{naoAtualizadosHoje.length}} chamados (Em atendimento / Aguardando Cliente) sem update hoje</div>
    <div id="barsNaoAtualizados"></div>
  </div>
  <div class="panel">
    <h2>🌙 Contraturno — em atendimento${{exportButtonHtml("exportLiveList(contraturno, 'contraturno.txt')")}}</h2>
    <div class="panel-sub">${{contraturno.length}} chamados em atendimento com Alife Caetano dos Santos ou Vinicius Campestrini</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Aberto ha</th></tr></thead>
      <tbody>${{tableHtml(contraturno, 'open', 10)}}</tbody></table>
  </div>
`;
document.getElementById('barsEmAtendimento').innerHTML = barsHtml(byTecnico(emAtendimento), 'emAtendimento');
document.getElementById('barsNaoAtualizados').innerHTML = barsHtml(byTecnico(naoAtualizadosHoje), 'naoAtualizadosHoje');

document.getElementById('gridBottom').innerHTML = `
  <div class="panel">
    <h2>🔴 Bouncing — em atendimento parado ha mais de 2 dias${{exportButtonHtml("exportLiveList(bouncing, 'bouncing.txt')")}}</h2>
    <div class="panel-sub">${{bouncing.length}} chamados Em atendimento sem nenhuma atualizacao ha 48h+</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Parado ha</th></tr></thead>
      <tbody>${{tableHtml(bouncing.sort((a,b)=>(b._hoursSinceUpdate||0)-(a._hoursSinceUpdate||0)), 'update', 14)}}</tbody></table>
  </div>
  <div class="panel">
    <h2>🕓 Nao atualizados hoje (lista)${{exportButtonHtml("exportLiveList(naoAtualizadosHoje, 'nao_atualizados_hoje.txt')")}}</h2>
    <div class="panel-sub">${{naoAtualizadosHoje.length}} chamados Em atendimento / Aguardando Cliente sem update hoje</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Aberto ha</th></tr></thead>
      <tbody>${{tableHtml(naoAtualizadosHoje.sort((a,b)=>(b._hoursOpen||0)-(a._hoursOpen||0)), 'open', 14)}}</tbody></table>
  </div>
  <div class="panel">
    <h2>🚛 Carga parada / emissao CIOT-MDFe-CTe${{exportButtonHtml("exportLiveList(cargaParada, 'carga_parada.txt')")}}</h2>
    <div class="panel-sub">${{cargaParada.length}} chamados abertos com carga travada ou problema de emissao de CIOT, MDFe ou CTe</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Status</th><th>Aberto ha</th></tr></thead>
      <tbody>${{tableHtml(cargaParada.sort((a,b)=>(b._hoursOpen||0)-(a._hoursOpen||0)), 'open', 14)}}</tbody></table>
  </div>
  <div class="panel">
    <h2>⚠️ Possivel classificacao incorreta${{exportButtonHtml("exportLiveList(classificacaoIncorreta, 'classificacao_incorreta.txt')")}}</h2>
    <div class="panel-sub">${{classificacaoIncorreta.length}} chamados abertos com categoria diferente de Bug, mas que ja passaram pela fila de Bugs ou tem assunto de bug</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Categoria atual</th><th>Motivo</th><th>Tecnico</th></tr></thead>
      <tbody>${{tableHtmlMisclass(classificacaoIncorreta, 14)}}</tbody></table>
  </div>
`;

document.getElementById('gridHist').innerHTML = `
  <div class="panel">
    <h2>⏱️ SLA por categoria (resolvidos no mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>r.slaSolutionDate), 'sla_por_categoria.txt')")}}</h2>
    <div class="panel-sub">${{totalSlaNoPrazo}} de ${{totalComSla}} chamados resolvidos este mes com SLA definido foram resolvidos dentro do prazo (${{pctSlaNoPrazoGeral}}%)</div>
    <div class="sla-cat-row head"><div>Categoria</div><div>Resolvidos</div><div>No prazo</div><div>% no prazo</div></div>
    ${{slaCategoriasOrdenadas.map(([cat, v]) => {{
      const pct = Math.round(v.noPrazo/v.total*100);
      return `<div class="sla-cat-row hist-bar-row" onclick="openModalHistCategoria('${{cat.replace(/'/g, "\\\\'")}}')">
        <div class="sla-cat-name">${{esc(cat)}}</div>
        <div class="sla-cat-num">${{v.total}}</div>
        <div class="sla-cat-num ${{pct<50?'danger':''}}">${{v.noPrazo}}</div>
        <div class="sla-cat-num ${{pct<50?'danger':''}}">${{pct}}%</div>
      </div>`;
    }}).join('') || '<div class="empty-msg">Nenhum chamado com SLA definido</div>'}}
    <div class="sla-cat-row" style="border-top: 2px solid var(--panel-border); margin-top: 4px; padding-top: 8px; font-weight: 700;">
      <div class="sla-cat-name">Total geral</div>
      <div class="sla-cat-num">${{totalComSla}}</div>
      <div class="sla-cat-num ${{pctSlaNoPrazoGeral<50?'danger':''}}">${{totalSlaNoPrazo}}</div>
      <div class="sla-cat-num ${{pctSlaNoPrazoGeral<50?'danger':''}}">${{pctSlaNoPrazoGeral}}%</div>
    </div>
  </div>
  <div class="panel">
    <h2>💬 Chats resolvidos por tecnico (mes)${{exportButtonHtml("exportHistListToExcel(chatsMes, 'chats_resolvidos_mes.txt')")}}</h2>
    <div class="panel-sub">${{chatsMes.length}} chamados originados via chat resolvidos este mes (${{chatsHoje.length}} hoje)</div>
    <div>${{chatsPorTecnico.length ? chatsPorTecnico.map(([name,count]) => {{
      const top = Math.max(...chatsPorTecnico.map(e=>e[1]));
      return `<div class="bar-row" onclick="openModalHistTecnico('chats', '${{name.replace(/'/g, "\\\\'")}}')">
        <div class="bar-label">${{esc(name)}}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${{(count/top*100).toFixed(0)}}%"></div></div>
        <div class="bar-value">${{count}}</div>
      </div>`;
    }}).join('') : '<div class="empty-msg">Nenhum chat resolvido no mes</div>'}}</div>
  </div>
  <div class="panel">
    <h2>✅ Chamados resolvidos por tecnico (mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH, 'chamados_resolvidos_mes.txt')")}}</h2>
    <div class="panel-sub">${{resolvidosMes}} chamados resolvidos este mes, por tecnico · media 3 meses: ${{media3Meses.total}}</div>
    <div>${{resolvidosPorTecnicoMes.length ? resolvidosPorTecnicoMes.map(([name,count]) => {{
      const top = Math.max(...resolvidosPorTecnicoMes.map(e=>e[1]));
      return `<div class="bar-row" onclick="openModalHistTecnico('resolvidos', '${{name.replace(/'/g, "\\\\'")}}')">
        <div class="bar-label">${{esc(name)}}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${{(count/top*100).toFixed(0)}}%"></div></div>
        <div class="bar-value">${{count}}</div>
      </div>`;
    }}).join('') : '<div class="empty-msg">Nenhum chamado resolvido no mes</div>'}}</div>
  </div>
`;

// --- Redimensionar e reordenar paineis (arrastar pelo icone ⠿), salvo no navegador ---
function saveOrder(containerId) {{
  const container = document.getElementById(containerId);
  const order = Array.from(container.children).filter(c => c.classList.contains('panel')).map(c => c.dataset.pid);
  localStorage.setItem('panelorder_' + containerId, JSON.stringify(order));
}}
function enhancePanels(containerId, allowReorder) {{
  const container = document.getElementById(containerId);
  if (!container) return;
  const panels = Array.from(container.classList && container.classList.contains('panel') ? [container] : container.querySelectorAll(':scope > .panel'));
  panels.forEach((p, i) => {{
    p.classList.add('resizable');
    if (!p.dataset.pid) p.dataset.pid = containerId + '_' + i;
    const savedSize = localStorage.getItem('panelsize_' + p.dataset.pid);
    if (savedSize) {{
      try {{
        const s = JSON.parse(savedSize);
        if (s.w) {{ p.style.width = s.w; p.style.flexGrow = '0'; p.style.flexShrink = '0'; }}
        if (s.h) p.style.height = s.h;
      }} catch(e) {{}}
    }}

    // Redimensionamento customizado (nao depende do resize:both nativo do navegador)
    if (!p.querySelector('.resize-handle')) {{
      const rh = document.createElement('div');
      rh.className = 'resize-handle';
      rh.title = 'Arrastar para redimensionar';
      p.appendChild(rh);
      let startX = 0, startY = 0, startW = 0, startH = 0, resizing = false;
      const onMove = e => {{
        if (!resizing) return;
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        const newW = Math.max(260, startW + (clientX - startX));
        const newH = Math.max(180, startH + (clientY - startY));
        p.style.width = newW + 'px';
        p.style.height = newH + 'px';
      }};
      const onUp = () => {{
        if (!resizing) return;
        resizing = false;
        document.body.style.userSelect = '';
        localStorage.setItem('panelsize_' + p.dataset.pid, JSON.stringify({{w: p.style.width, h: p.style.height}}));
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        window.removeEventListener('touchmove', onMove);
        window.removeEventListener('touchend', onUp);
      }};
      const onDown = e => {{
        e.preventDefault();
        resizing = true;
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        startX = clientX; startY = clientY;
        const box = p.getBoundingClientRect();
        startW = box.width; startH = box.height;
        p.style.flexGrow = '0';
        p.style.flexShrink = '0';
        document.body.style.userSelect = 'none';
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        window.addEventListener('touchmove', onMove, {{passive:false}});
        window.addEventListener('touchend', onUp);
      }};
      rh.addEventListener('mousedown', onDown);
      rh.addEventListener('touchstart', onDown, {{passive:false}});
    }}

    if (!allowReorder) return;
    const h2 = p.querySelector('h2');
    if (h2 && !h2.querySelector('.drag-handle')) {{
      const handle = document.createElement('span');
      handle.className = 'drag-handle';
      handle.textContent = '⠿';
      handle.title = 'Arrastar para reordenar';
      handle.addEventListener('mousedown', () => {{ p.setAttribute('draggable', 'true'); }});
      h2.appendChild(handle);
    }}
    p.addEventListener('dragstart', e => {{ e.dataTransfer.setData('text/plain', p.dataset.pid); p.classList.add('dragging'); }});
    p.addEventListener('dragend', () => {{ p.removeAttribute('draggable'); p.classList.remove('dragging'); saveOrder(containerId); }});
    p.addEventListener('dragover', e => {{ e.preventDefault(); p.classList.add('drag-over'); }});
    p.addEventListener('dragleave', () => p.classList.remove('drag-over'));
    p.addEventListener('drop', e => {{
      e.preventDefault();
      p.classList.remove('drag-over');
      const draggedId = e.dataTransfer.getData('text/plain');
      const dragged = container.querySelector(`[data-pid="${{draggedId}}"]`);
      if (dragged && dragged !== p) {{
        const all = Array.from(container.children);
        if (all.indexOf(dragged) < all.indexOf(p)) p.after(dragged); else p.before(dragged);
        saveOrder(containerId);
      }}
    }});
  }});
  if (allowReorder) {{
    const savedOrder = localStorage.getItem('panelorder_' + containerId);
    if (savedOrder) {{
      try {{
        JSON.parse(savedOrder).forEach(pid => {{
          const el = container.querySelector(`[data-pid="${{pid}}"]`);
          if (el) container.appendChild(el);
        }});
      }} catch(e) {{}}
    }}
  }}
}}
enhancePanels('gridTop', true);
enhancePanels('gridBottom', true);
enhancePanels('gridHist', true);
enhancePanels('priorityPanel', false);
enhancePanels('chatsLivePanel', false);

// ============================================================
// Filtro de cliente na aba Historico — reaproveita a mesma logica de calculo dos cards
// (SLA, MTTR, bugs, resolvidos por tecnico), mas escopada a um unico cliente quando selecionado.
// Reatribui RESOLVED_MONTH/chatsMes (globais) para que os modais de drill-down (openModalHist*)
// tambem reflitam o filtro atual.
// ============================================================
function renderHistoricoMes(clienteFiltro) {{
  RESOLVED_MONTH = clienteFiltro ? RESOLVED_MONTH_ALL.filter(r => r.clientOrg === clienteFiltro) : RESOLVED_MONTH_ALL;

  const resolvidosMes = RESOLVED_MONTH.length;
  const resolvidosPrimeiraRespostaMes = RESOLVED_MONTH.filter(isPrimeiraResposta).length;
  const pctPrimeiraRespostaMes = resolvidosMes ? Math.round(resolvidosPrimeiraRespostaMes / resolvidosMes * 100) : 0;

  const slaPorCategoria = {{}};
  RESOLVED_MONTH.filter(r => r.slaSolutionDate).forEach(r => {{
    const cat = r.category || 'Sem categoria';
    if (!slaPorCategoria[cat]) slaPorCategoria[cat] = {{ total: 0, noPrazo: 0 }};
    slaPorCategoria[cat].total++;
    const resolvedIn = parseDt(r.resolvedIn);
    const slaDate = parseDt(r.slaSolutionDate);
    if (resolvedIn && slaDate && resolvedIn <= slaDate) slaPorCategoria[cat].noPrazo++;
  }});
  const slaCategoriasOrdenadas = Object.entries(slaPorCategoria).sort((a,b) => (a[1].noPrazo/a[1].total) - (b[1].noPrazo/b[1].total));
  const totalComSla = Object.values(slaPorCategoria).reduce((s,v)=>s+v.total,0);
  const totalSlaNoPrazo = Object.values(slaPorCategoria).reduce((s,v)=>s+v.noPrazo,0);
  const pctSlaNoPrazoGeral = totalComSla ? Math.round(totalSlaNoPrazo/totalComSla*100) : 0;

  chatsMes = RESOLVED_MONTH.filter(r => r.origin === 24);
  const pctChatsMes = RESOLVED_MONTH.length ? Math.round(chatsMes.length / RESOLVED_MONTH.length * 100) : 0;
  const chatsPorTecnico = byTecnicoResolved(chatsMes);
  const resolvidosPorTecnicoMes = byTecnicoResolved(RESOLVED_MONTH);

  const bugsMes = RESOLVED_MONTH.filter(r => r.category === 'Bug' && (r.statusHistories||[]).length);
  const bugMetricsF = bugsMes.map(r => {{
    const hist = r.statusHistories.map(h => ({{ ...h, _d: parseDt(h.changedDate) }})).sort((a,b) => a._d - b._d);
    const created = parseDt(r.createdDate);
    const firstBugQueue = hist.find(h => h.status === BUG_QUEUE_STATUS);
    const tempoParaAbrirH = (firstBugQueue && created) ? (firstBugQueue._d - created) / 3600000 : null;
    const devopsSeconds = hist.filter(h => h.status === BUG_QUEUE_STATUS).reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0);
    let lastBugQueueIdx = -1;
    hist.forEach((h,i) => {{ if (h.status === BUG_QUEUE_STATUS) lastBugQueueIdx = i; }});
    const validacaoSeconds = lastBugQueueIdx >= 0
      ? hist.slice(lastBugQueueIdx+1).filter(h => h.status === 'Em atendimento' || h.status === 'Aguardando Cliente').reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0)
      : null;
    return {{ protocol: r.protocol, urgency: r.urgency, ownerName: r.ownerName, tempoParaAbrirH, devopsH: devopsSeconds/3600, validacaoH: validacaoSeconds !== null ? validacaoSeconds/3600 : null, passouPorDevops: lastBugQueueIdx >= 0 }};
  }});
  function bugMetricsForF(urgency) {{
    const subset = urgency ? bugMetricsF.filter(b => b.urgency === urgency) : bugMetricsF;
    const comAbertura = subset.filter(b => b.tempoParaAbrirH !== null).map(b => b.tempoParaAbrirH);
    const comDevops = subset.filter(b => b.passouPorDevops).map(b => b.devopsH);
    const comValidacao = subset.filter(b => b.validacaoH !== null).map(b => b.validacaoH);
    return {{ total: subset.length, comAbertura, comDevops, comValidacao, mediaParaAbrirBug: avg(comAbertura), mediaDevops: avg(comDevops), mediaValidacao: avg(comValidacao) }};
  }}
  const bugMetricsMediaF = bugMetricsForF('Média');
  const bugMetricsAltaF = bugMetricsForF('Alta');

  function statsForMonthCliente(items) {{
    return statsForMonth(clienteFiltro ? items.filter(r => r.clientOrg === clienteFiltro) : items);
  }}
  const statsPorMes3F = Object.keys(RESOLVED_MONTHS).map(k => ({{ key: k, ...statsForMonthCliente(RESOLVED_MONTHS[k]) }}));
  const media3MesesF = {{
    total: Math.round(avg(statsPorMes3F.map(s => s.total))),
    pctPrimeira: Math.round(avg(statsPorMes3F.map(s => s.pctPrimeira))),
    pctSla: Math.round(avg(statsPorMes3F.map(s => s.pctSla))),
    chats: Math.round(avg(statsPorMes3F.map(s => s.chats))),
    mttrH: avg(statsPorMes3F.filter(s => s.mttrH !== null).map(s => s.mttrH)),
  }};
  const comparativoMttrF = statsPorMes3F.map(s => `${{MONTH_LABELS[s.key].split('/')[0].slice(0,3)}}: ${{s.mttrH !== null ? fmtH(s.mttrH) : '-'}}`).join(' · ');

  const metaPctPrimeiraF = metaMelhoria10(media3MesesF.pctPrimeira, false);
  const metaPctSlaF = metaMelhoria10(media3MesesF.pctSla, false);
  const filtroSufixo = clienteFiltro ? ` · cliente: ${{clienteFiltro}}` : '';
  document.getElementById('kpiRowHist').innerHTML =
    kpiTileHist('ok', resolvidosPrimeiraRespostaHoje, 'Resolvidos c/ 1a resposta (hoje)', 'primeiraRespostaHoje', `${{pctPrimeiraRespostaHoje}}% de ${{resolvidosHoje}} resolvidos hoje (nao filtra por cliente)`) +
    kpiTileHist(bateMeta(pctPrimeiraRespostaMes, metaPctPrimeiraF, false) ? 'ok' : 'warn', resolvidosPrimeiraRespostaMes, 'Resolvidos c/ 1a resposta (mes)', 'primeiraRespostaMes', `${{pctPrimeiraRespostaMes}}% de ${{resolvidosMes}} resolvidos no mes · media 3m: ${{media3MesesF.pctPrimeira}}% · meta (+10%/mes): ${{metaPctPrimeiraF !== null ? Math.round(metaPctPrimeiraF)+'%' : '-'}}${{filtroSufixo}}`) +
    kpiTileHist(bateMeta(pctSlaNoPrazoGeral, metaPctSlaF, false) ? 'ok' : 'danger', `${{pctSlaNoPrazoGeral}}%`, 'SLA atendido no prazo (mes)', 'slaNoPrazoMes', `${{totalSlaNoPrazo}} de ${{totalComSla}} resolvidos com SLA definido · media 3m: ${{media3MesesF.pctSla}}% · meta (+10%/mes): ${{metaPctSlaF !== null ? Math.round(metaPctSlaF)+'%' : '-'}}${{filtroSufixo}} (clique p/ ver os fora do prazo)`) +
    kpiTileHist('neutral', chatsMes.length, 'Chats resolvidos (mes)', 'chatsMes', `${{pctChatsMes}}% do total resolvido no mes · ${{chatsHoje.length}} hoje · media 3m: ${{media3MesesF.chats}}${{filtroSufixo}}`);

  const mttrMesAtualF = statsPorMes3F.find(s => s.key === '0').mttrH;
  const metaMttrF = metaMelhoria10(media3MesesF.mttrH, true);
  const mttrBateMetaF = bateMeta(mttrMesAtualF, metaMttrF, true);
  document.getElementById('kpiRowHistMttr').innerHTML =
    kpiTileStatic(mttrBateMetaF === null ? 'warn' : (mttrBateMetaF ? 'ok' : 'danger'), mttrMesAtualF !== null ? fmtH(mttrMesAtualF) : '-', 'Tempo medio de atendimento (MTTR)', `mes corrente: ${{MONTH_LABELS['0']}} · media 3m: ${{media3MesesF.mttrH !== null ? fmtH(media3MesesF.mttrH) : '-'}} · meta (10% menor que a media 3m): ${{metaMttrF !== null ? fmtH(metaMttrF) : '-'}} · ultimos 3 meses: ${{comparativoMttrF}}${{filtroSufixo}}`);

  renderBugMetricsRow('kpiRowHistBugMedia', bugMetricsMediaF);
  renderBugMetricsRow('kpiRowHistBugAlta', bugMetricsAltaF);

  document.getElementById('gridHist').innerHTML = `
    <div class="panel">
      <h2>⏱️ SLA por categoria (resolvidos no mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>r.slaSolutionDate), 'sla_por_categoria.txt')")}}</h2>
      <div class="panel-sub">${{totalSlaNoPrazo}} de ${{totalComSla}} chamados resolvidos este mes com SLA definido foram resolvidos dentro do prazo (${{pctSlaNoPrazoGeral}}%)${{filtroSufixo}}</div>
      <div class="sla-cat-row head"><div>Categoria</div><div>Resolvidos</div><div>No prazo</div><div>% no prazo</div></div>
      ${{slaCategoriasOrdenadas.map(([cat, v]) => {{
        const pct = Math.round(v.noPrazo/v.total*100);
        return `<div class="sla-cat-row hist-bar-row" onclick="openModalHistCategoria(${{jsStr(cat)}})">
          <div class="sla-cat-name">${{esc(cat)}}</div>
          <div class="sla-cat-num">${{v.total}}</div>
          <div class="sla-cat-num ${{pct<50?'danger':''}}">${{v.noPrazo}}</div>
          <div class="sla-cat-num ${{pct<50?'danger':''}}">${{pct}}%</div>
        </div>`;
      }}).join('') || '<div class="empty-msg">Nenhum chamado com SLA definido</div>'}}
      <div class="sla-cat-row" style="border-top: 2px solid var(--panel-border); margin-top: 4px; padding-top: 8px; font-weight: 700;">
        <div class="sla-cat-name">Total geral</div>
        <div class="sla-cat-num">${{totalComSla}}</div>
        <div class="sla-cat-num ${{pctSlaNoPrazoGeral<50?'danger':''}}">${{totalSlaNoPrazo}}</div>
        <div class="sla-cat-num ${{pctSlaNoPrazoGeral<50?'danger':''}}">${{pctSlaNoPrazoGeral}}%</div>
      </div>
    </div>
    <div class="panel">
      <h2>💬 Chats resolvidos por tecnico (mes)${{exportButtonHtml("exportHistListToExcel(chatsMes, 'chats_resolvidos_mes.txt')")}}</h2>
      <div class="panel-sub">${{chatsMes.length}} chamados originados via chat resolvidos este mes (${{chatsHoje.length}} hoje)${{filtroSufixo}}</div>
      <div>${{chatsPorTecnico.length ? chatsPorTecnico.map(([name,count]) => {{
        const top = Math.max(...chatsPorTecnico.map(e=>e[1]));
        return `<div class="bar-row" onclick="openModalHistTecnico('chats', ${{jsStr(name)}})">
          <div class="bar-label">${{esc(name)}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{(count/top*100).toFixed(0)}}%"></div></div>
          <div class="bar-value">${{count}}</div>
        </div>`;
      }}).join('') : '<div class="empty-msg">Nenhum chat resolvido no mes</div>'}}</div>
    </div>
    <div class="panel">
      <h2>✅ Chamados resolvidos por tecnico (mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH, 'chamados_resolvidos_mes.txt')")}}</h2>
      <div class="panel-sub">${{resolvidosMes}} chamados resolvidos este mes, por tecnico · media 3 meses: ${{media3MesesF.total}}${{filtroSufixo}}</div>
      <div>${{resolvidosPorTecnicoMes.length ? resolvidosPorTecnicoMes.map(([name,count]) => {{
        const top = Math.max(...resolvidosPorTecnicoMes.map(e=>e[1]));
        return `<div class="bar-row" onclick="openModalHistTecnico('resolvidos', ${{jsStr(name)}})">
          <div class="bar-label">${{esc(name)}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{(count/top*100).toFixed(0)}}%"></div></div>
          <div class="bar-value">${{count}}</div>
        </div>`;
      }}).join('') : '<div class="empty-msg">Nenhum chamado resolvido no mes</div>'}}</div>
    </div>
  `;
  enhancePanels('gridHist', true);
}}

const selClienteHistorico = document.getElementById('selClienteHistorico');
if (selClienteHistorico) {{
  const clientesHist = Array.from(new Set(RESOLVED_MONTH_ALL.map(r => r.clientOrg).filter(Boolean))).sort((a,b) => a.localeCompare(b));
  populateSelect(selClienteHistorico, [['', 'Todos os clientes'], ...clientesHist.map(c => [c, c])]);
  selClienteHistorico.addEventListener('change', () => {{
    renderHistoricoMes(selClienteHistorico.value || null);
  }});
}}

// ============================================================
// Aba Clientes — Status Report (indicadores ITIL por mes/cliente)
// ============================================================
function computeIndicadores(items) {{
  const total = items.length;
  const comTempo = items.filter(r => r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 3600000);
  const mttrH = avg(comTempo);
  const comSla = items.filter(r => r.slaSolutionDate);
  const noPrazo = comSla.filter(r => parseDt(r.resolvedIn) <= parseDt(r.slaSolutionDate)).length;
  const pctSla = comSla.length ? Math.round(noPrazo / comSla.length * 100) : null;
  const reincidencia = items.filter(r => r.reopenedIn).length;
  const pctReincidencia = total ? Math.round(reincidencia / total * 100) : 0;
  return {{ total, mttrH, pctSla, comSlaLength: comSla.length, reincidencia, pctReincidencia }};
}}

function populateSelect(sel, options, selectedValue) {{
  sel.innerHTML = options.map(([val, label]) => `<option value="${{esc(val)}}">${{esc(label)}}</option>`).join('');
  if (selectedValue !== undefined) sel.value = selectedValue;
}}

const selMesCliente = document.getElementById('selMesCliente');
const selCliente = document.getElementById('selCliente');
populateSelect(selMesCliente, Object.keys(MONTH_LABELS).map(k => [k, MONTH_LABELS[k]]));

function clientesDoMes(mesKey) {{
  const set = new Set((RESOLVED_MONTHS[mesKey] || []).map(r => r.clientOrg).filter(Boolean));
  return Array.from(set).sort((a,b) => a.localeCompare(b));
}}

function refreshClienteOptions() {{
  const mesKey = selMesCliente.value;
  const clientesList = clientesDoMes(mesKey);
  const prevSelected = selCliente.value;
  populateSelect(selCliente, clientesList.map(c => [c, c]));
  if (clientesList.indexOf(prevSelected) !== -1) selCliente.value = prevSelected;
}}

function indicadores3MesesCliente(cliente) {{
  const porMes = Object.keys(RESOLVED_MONTHS).map(k => computeIndicadores((RESOLVED_MONTHS[k]||[]).filter(r => r.clientOrg === cliente)));
  return {{
    total: avg(porMes.map(i => i.total)),
    mttrH: avg(porMes.filter(i => i.mttrH !== null).map(i => i.mttrH)),
    pctSla: avg(porMes.filter(i => i.pctSla !== null).map(i => i.pctSla)),
    pctReincidencia: avg(porMes.map(i => i.pctReincidencia)),
  }};
}}

function renderClienteReport() {{
  const mesKey = selMesCliente.value;
  const cliente = selCliente.value;
  const monthItems = (RESOLVED_MONTHS[mesKey] || []).filter(r => r.clientOrg === cliente);
  const ind = computeIndicadores(monthItems);
  const backlog = TICKETS.filter(t => t.clientOrg === cliente).length;
  const m3 = indicadores3MesesCliente(cliente);

  document.getElementById('kpiCliente').innerHTML =
    kpiTileStatic('neutral', ind.total, 'Chamados no mes', `${{MONTH_LABELS[mesKey]}} · time Suporte · media 3m: ${{m3.total !== null ? Math.round(m3.total) : '-'}}`) +
    kpiTileStatic('warn', ind.mttrH !== null ? fmtH(ind.mttrH) : '-', 'MTTR (tempo medio resolucao)', `${{monthItems.filter(r=>r.createdDate && r.resolvedIn).length}} chamados com tempo calculavel · media 3m: ${{m3.mttrH !== null ? fmtH(m3.mttrH) : '-'}}`) +
    kpiTileStatic(ind.pctSla !== null && ind.pctSla < 70 ? 'danger' : 'ok', ind.pctSla !== null ? `${{ind.pctSla}}%` : '-', 'SLA no prazo', `${{ind.comSlaLength}} chamados com SLA definido · media 3m: ${{m3.pctSla !== null ? Math.round(m3.pctSla)+'%' : '-'}}`) +
    kpiTileStatic('neutral', backlog, 'Backlog (em aberto agora)', 'chamados atualmente nao fechados deste cliente') +
    kpiTileStatic(ind.reincidencia > 0 ? 'danger' : 'ok', ind.reincidencia, 'Reincidencia (reabertos)', `${{ind.pctReincidencia}}% do total do mes · media 3m: ${{Math.round(m3.pctReincidencia)}}%`);

  // Backlog aberto por categoria e status — no mesmo formato do status report que o CS apresenta
  // ao cliente (contagem de categoria com detalhamento por status + tabela resumo Tipo/Quantidade).
  const backlogItems = TICKETS.filter(t => t.clientOrg === cliente);
  const porCategoria = {{}};
  backlogItems.forEach(t => {{
    const cat = t.category || 'Sem categoria';
    if (!porCategoria[cat]) porCategoria[cat] = {{ total: 0, status: {{}} }};
    porCategoria[cat].total++;
    const st = t.status || 'Sem status';
    porCategoria[cat].status[st] = (porCategoria[cat].status[st] || 0) + 1;
  }});
  const categoriasOrdenadas = Object.entries(porCategoria).sort((a,b) => b[1].total - a[1].total);
  const gestaoChamadosHtml = categoriasOrdenadas.length ? categoriasOrdenadas.map(([cat, info]) => `
    <div class="bar-row" style="font-weight:700; cursor:pointer;" onclick="openModalClienteCategoria(${{jsStr(cliente)}}, ${{jsStr(cat)}}, null)">
      <div class="bar-label">${{esc(cat)}}</div><div></div><div class="bar-value">${{info.total}}</div>
    </div>
    ${{Object.entries(info.status).sort((a,b)=>b[1]-a[1]).map(([st,qtd]) => `
      <div class="bar-row" style="padding-left:18px; opacity:.85; cursor:pointer;" onclick="openModalClienteCategoria(${{jsStr(cliente)}}, ${{jsStr(cat)}}, ${{jsStr(st)}})">
        <div class="bar-label">${{esc(st)}}</div><div></div><div class="bar-value">${{qtd}}</div>
      </div>`).join('')}}
  `).join('') : '<div class="empty-msg">Sem chamados em aberto</div>';
  const totalBacklogGeral = backlogItems.length;

  document.getElementById('gridCliente').innerHTML = `
    <div class="panel">
      <h2>📋 Chamados resolvidos no mes${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTHS[" + jsStr(mesKey) + "].filter(r=>r.clientOrg===" + jsStr(cliente) + "), 'cliente.txt')")}}</h2>
      <div class="panel-sub">${{ind.total}} chamados resolvidos — ${{esc(cliente)}} — ${{MONTH_LABELS[mesKey]}}</div>
      <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Tecnico</th><th>Categoria</th><th>Resolvido em</th></tr></thead>
        <tbody>${{tableHtmlHist(monthItems.slice().sort((a,b)=>new Date(b.resolvedIn)-new Date(a.resolvedIn)), 100)}}</tbody></table>
    </div>
    <div class="panel">
      <h2>📌 Gestao de Chamados — backlog em aberto agora${{exportButtonHtml("exportLiveList(TICKETS.filter(t=>t.clientOrg===" + jsStr(cliente) + "), 'backlog_cliente.txt')")}}</h2>
      <div class="panel-sub">${{totalBacklogGeral}} chamados em aberto — ${{esc(cliente)}} — mesmo formato do status report apresentado ao cliente (categoria e status)</div>
      <div>${{gestaoChamadosHtml}}</div>
    </div>
  `;
}}
function openModalClienteCategoria(cliente, categoria, status) {{
  const items = TICKETS.filter(t => t.clientOrg === cliente && (t.category || 'Sem categoria') === categoria && (!status || (t.status || 'Sem status') === status));
  const label = status ? `${{categoria}} — ${{status}}` : categoria;
  renderModal(`${{label}} — ${{cliente}}`, items, 'open');
}}
selMesCliente.addEventListener('change', () => {{ refreshClienteOptions(); renderClienteReport(); }});
selCliente.addEventListener('change', renderClienteReport);
refreshClienteOptions();
renderClienteReport();

// ============================================================
// Aba One-on-One — protegida por senha (aviso: trava simples do lado do navegador, nao e seguranca real)
// ============================================================
const ONE_ON_ONE_PASSWORD = '3300';
function checkOneOnOnePassword() {{
  const val = document.getElementById('oneOnOnePassInput').value;
  if (val === ONE_ON_ONE_PASSWORD) {{
    document.getElementById('oneOnOneGate').style.display = 'none';
    document.getElementById('oneOnOneContent').style.display = 'block';
    sessionStorage.setItem('oneOnOneUnlocked', '1');
    initOneOnOne();
  }} else {{
    document.getElementById('oneOnOneError').style.display = 'block';
  }}
}}
document.getElementById('oneOnOnePassInput').addEventListener('keydown', e => {{ if (e.key === 'Enter') checkOneOnOnePassword(); }});
if (sessionStorage.getItem('oneOnOneUnlocked') === '1') {{
  document.getElementById('oneOnOneGate').style.display = 'none';
  document.getElementById('oneOnOneContent').style.display = 'block';
}}

let oneOnOneInited = false;
function initOneOnOne() {{
  if (oneOnOneInited) return;
  oneOnOneInited = true;
  const selPeriodo = document.getElementById('selPeriodoOneOnOne');
  const selTecnico = document.getElementById('selTecnicoOneOnOne');
  populateSelect(selPeriodo, Object.keys(MONTH_LABELS).map(k => [k, MONTH_LABELS[k]]));

  function tecnicosDoPeriodo(periodoKey) {{
    const set = new Set((RESOLVED_MONTHS[periodoKey] || []).map(r => r.ownerName).filter(Boolean));
    return Array.from(set).sort((a,b) => a.localeCompare(b));
  }}
  function refreshTecnicoOptions() {{
    const periodoKey = selPeriodo.value;
    const list = tecnicosDoPeriodo(periodoKey);
    const prev = selTecnico.value;
    populateSelect(selTecnico, list.map(t => [t, t]));
    if (list.indexOf(prev) !== -1) selTecnico.value = prev;
  }}
  function renderOneOnOne() {{
    const periodoKey = selPeriodo.value;
    const tecnico = selTecnico.value;
    const tier = tierDoTecnico(tecnico);
    const periodItems = (RESOLVED_MONTHS[periodoKey] || []).filter(r => r.ownerName === tecnico);
    const ind = computeIndicadores(periodItems);
    const pctPrimeira = periodItems.length ? Math.round(periodItems.filter(isPrimeiraResposta).length / periodItems.length * 100) : 0;
    const m3 = indicadoresTecnico3Meses(tecnico);
    const equipe = mediaEquipe(periodoKey, tier);

    const liveDoTecnico = TICKETS.filter(t => t.ownerName === tecnico);
    const bouncingTecnico = liveDoTecnico.filter(t => t.status === 'Em atendimento' && t._hoursSinceUpdate !== null && t._hoursSinceUpdate >= 48).length;
    const naoAtualizadosTecnico = liveDoTecnico.filter(t => (t.status === 'Em atendimento' || t.status === 'Aguardando Cliente') && !t._updatedToday).length;

    const badge = document.getElementById('tierBadgeOneOnOne');
    badge.textContent = tier;
    badge.style.background = tier === 'N2' ? 'var(--pink)' : 'var(--ok)';
    badge.style.color = '#fff';

    document.getElementById('kpiOneOnOne').innerHTML =
      kpiTileStatic('neutral', ind.total, 'Chamados resolvidos', `${{MONTH_LABELS[periodoKey]}} · media time ${{tier}}: ${{equipe.total !== null ? Math.round(equipe.total) : '-'}} (${{equipe.qtdTecnicos}} tec.) · ultimos 3m: ${{m3.comparativoTotal}}`) +
      kpiTileStatic('ok', `${{pctPrimeira}}%`, 'Resolvidos na 1a resposta', `de ${{ind.total}} chamados no periodo · media time ${{tier}}: ${{equipe.pctPrimeira !== null ? Math.round(equipe.pctPrimeira)+'%' : '-'}} · media 3m: ${{m3.pctPrimeira !== null ? Math.round(m3.pctPrimeira)+'%' : '-'}}`) +
      kpiTileStatic('warn', ind.mttrH !== null ? fmtH(ind.mttrH) : '-', 'Tempo medio de resolucao', `${{ind.comSlaLength}} chamados com SLA definido · media time ${{tier}}: ${{equipe.mttrH !== null ? fmtH(equipe.mttrH) : '-'}}`);

    document.getElementById('kpiOneOnOne2').innerHTML =
      kpiTileStatic(ind.pctSla !== null && ind.pctSla < 70 ? 'danger' : 'ok', ind.pctSla !== null ? `${{ind.pctSla}}%` : '-', 'SLA no prazo', `media time ${{tier}}: ${{equipe.pctSla !== null ? Math.round(equipe.pctSla)+'%' : '-'}} · media 3m: ${{m3.pctSla !== null ? Math.round(m3.pctSla)+'%' : '-'}}`) +
      kpiTileStatic(bouncingTecnico > 0 ? 'danger' : 'ok', bouncingTecnico, 'Bouncing atual (>2 dias)', 'situacao ao vivo, nao e do periodo') +
      kpiTileStatic(naoAtualizadosTecnico > 0 ? 'warn' : 'ok', naoAtualizadosTecnico, 'Nao atualizados hoje', 'situacao ao vivo, nao e do periodo');

    // Metas — melhoria de 10% ao mes sobre a media dos ultimos 3 meses do proprio tecnico.
    // Bouncing/nao-atualizados sao indicadores ao vivo (sem serie mensal), entao continuam com meta fixa de zero.
    const metaMttrTec = metaMelhoria10(m3.mttrH, true);
    const metaSlaTec = metaMelhoria10(m3.pctSla, false);
    const metaPrimeiraTec = metaMelhoria10(m3.pctPrimeira, false);
    const mttrBateMetaTec = bateMeta(ind.mttrH, metaMttrTec, true);
    const slaBateMetaTec = bateMeta(ind.pctSla, metaSlaTec, false);
    const primeiraBateMetaTec = bateMeta(pctPrimeira, metaPrimeiraTec, false);
    document.getElementById('kpiOneOnOneMetas').innerHTML =
      kpiTileStatic(bouncingTecnico === 0 ? 'ok' : 'danger', bouncingTecnico === 0 ? 'Meta batida' : 'Meta nao batida', 'Meta: 0 bouncing', `atual: ${{bouncingTecnico}} chamado(s) em bouncing`) +
      kpiTileStatic(naoAtualizadosTecnico === 0 ? 'ok' : 'warn', naoAtualizadosTecnico === 0 ? 'Meta batida' : 'Meta nao batida', 'Meta: 0 nao atualizados', `atual: ${{naoAtualizadosTecnico}} chamado(s) sem atualizar hoje`) +
      kpiTileStatic(mttrBateMetaTec === null ? 'warn' : (mttrBateMetaTec ? 'ok' : 'danger'), mttrBateMetaTec === null ? '-' : (mttrBateMetaTec ? 'Meta batida' : 'Meta nao batida'), 'Meta MTTR (10% melhor que media 3m)', `atual: ${{ind.mttrH !== null ? fmtH(ind.mttrH) : '-'}} · meta: ${{metaMttrTec !== null ? fmtH(metaMttrTec) : '-'}}`) +
      kpiTileStatic(slaBateMetaTec === null ? 'warn' : (slaBateMetaTec ? 'ok' : 'danger'), slaBateMetaTec === null ? '-' : (slaBateMetaTec ? 'Meta batida' : 'Meta nao batida'), 'Meta SLA (+10%/mes s/ media 3m)', `atual: ${{ind.pctSla !== null ? ind.pctSla+'%' : '-'}} · meta: ${{metaSlaTec !== null ? Math.round(metaSlaTec)+'%' : '-'}}`) +
      kpiTileStatic(primeiraBateMetaTec === null ? 'warn' : (primeiraBateMetaTec ? 'ok' : 'danger'), primeiraBateMetaTec === null ? '-' : (primeiraBateMetaTec ? 'Meta batida' : 'Meta nao batida'), 'Meta 1a resposta (+10%/mes s/ media 3m)', `atual: ${{pctPrimeira}}% · meta: ${{metaPrimeiraTec !== null ? Math.round(metaPrimeiraTec)+'%' : '-'}}`);

    // Indicadores tecnicos N2 — cobranca sobre tasks (Bug/Melhoria/Servicos), diferente do foco em
    // volume + qualidade na 1a resposta dos N1. So' calculavel para o mes corrente.
    if (tier === 'N2') {{
      const n2 = computeN2Metrics(tecnico, periodoKey);
      document.getElementById('kpiOneOnOneN2').style.display = '';
      if (n2) {{
        document.getElementById('kpiOneOnOneN2').innerHTML =
          kpiTileStatic('neutral', n2.total, 'Chamados tecnicos (Bug/Melhoria/Servicos)', 'resolvidos no mes corrente') +
          kpiTileStatic('neutral', n2.pctTask !== null ? `${{n2.pctTask}}%` : '-', '% com task associada (fila de Bugs)', 'de chamados tecnicos que geraram task de dev') +
          kpiTileStatic('warn', n2.devopsMedio !== null ? fmtH(n2.devopsMedio) : '-', 'Tempo medio em devops/validacao', `devops: ${{n2.devopsMedio !== null ? fmtH(n2.devopsMedio) : '-'}} · validacao: ${{n2.validacaoMedio !== null ? fmtH(n2.validacaoMedio) : '-'}}`);
      }} else {{
        document.getElementById('kpiOneOnOneN2').innerHTML =
          kpiTileStatic('neutral', '-', 'Indicadores tecnicos (N2)', 'so disponivel para o mes corrente (o historico de status nao e mantido para meses anteriores)');
      }}
    }} else {{
      document.getElementById('kpiOneOnOneN2').style.display = 'none';
      document.getElementById('kpiOneOnOneN2').innerHTML = '';
    }}
  }}
  selPeriodo.addEventListener('change', () => {{ refreshTecnicoOptions(); renderOneOnOne(); }});
  selTecnico.addEventListener('change', renderOneOnOne);
  refreshTecnicoOptions();
  renderOneOnOne();
}}
if (sessionStorage.getItem('oneOnOneUnlocked') === '1') initOneOnOne();

// ============================================================
// Aba Gamificacao — protegida por senha (mesmo esquema simples do One-on-One).
// ============================================================
const GAMIFICACAO_PASSWORD = '3300';
function checkGamificacaoPassword() {{
  const val = document.getElementById('gamificacaoPassInput').value;
  if (val === GAMIFICACAO_PASSWORD) {{
    document.getElementById('gamificacaoGate').style.display = 'none';
    document.getElementById('gamificacaoContent').style.display = 'block';
    sessionStorage.setItem('gamificacaoUnlocked', '1');
    initGamificacao();
  }} else {{
    document.getElementById('gamificacaoError').style.display = 'block';
  }}
}}
document.getElementById('gamificacaoPassInput').addEventListener('keydown', e => {{ if (e.key === 'Enter') checkGamificacaoPassword(); }});
if (sessionStorage.getItem('gamificacaoUnlocked') === '1') {{
  document.getElementById('gamificacaoGate').style.display = 'none';
  document.getElementById('gamificacaoContent').style.display = 'block';
}}

let gamificacaoInited = false;
function initGamificacao() {{
  if (gamificacaoInited) return;
  gamificacaoInited = true;
  const selMes = document.getElementById('selMesGamificacao');
  const opcoes = Object.keys(MONTH_LABELS).map(k => [k, MONTH_LABELS[k]]);
  opcoes.push(['all', 'Soma dos ultimos 3 meses']);
  populateSelect(selMes, opcoes);

  function renderGamificacao() {{
    const mesKey = selMes.value;
    const todosTecnicos = Array.from(new Set(Object.values(RESOLVED_MONTHS).flat().map(r => r.ownerName).filter(Boolean))).sort((a,b) => a.localeCompare(b));
    const meses = mesKey === 'all' ? Object.keys(MONTH_LABELS) : [mesKey];

    // Agrega por CRITERIO (MTTR, SLA no prazo, 1a resposta) — sem expor nome de tecnico individual.
    const porCriterio = {{}};
    todosTecnicos.forEach(t => {{
      meses.forEach(k => {{
        const m = metasDoTecnicoNoMes(t, k);
        if (!m.temDados) return;
        m.itens.forEach(item => {{
          if (item.bateu === null) return;
          if (!porCriterio[item.nome]) porCriterio[item.nome] = {{ batidas: 0, total: 0 }};
          porCriterio[item.nome].total++;
          if (item.bateu) porCriterio[item.nome].batidas++;
        }});
      }});
    }});
    const criterios = Object.entries(porCriterio);
    const somaBatidas = criterios.reduce((s,[,v]) => s + v.batidas, 0);
    const somaTotal = criterios.reduce((s,[,v]) => s + v.total, 0);
    const periodoLabel = mesKey === 'all' ? 'soma dos ultimos 3 meses' : MONTH_LABELS[mesKey];

    document.getElementById('kpiGamificacao').innerHTML =
      kpiTileStatic('ok', `${{somaBatidas}} de ${{somaTotal}}`, 'Metas batidas (soma geral)', `${{somaTotal ? Math.round(somaBatidas/somaTotal*100) : 0}}% de aproveitamento · ${{periodoLabel}}`) +
      kpiTileStatic('neutral', criterios.length, 'Criterios avaliados', `MTTR, SLA no prazo e 1a resposta — 10% de melhoria s/ media 3m de cada tecnico`);

    document.getElementById('gridGamificacao').innerHTML = `
      <div class="panel">
        <h2>🏆 Metas batidas por criterio</h2>
        <div class="panel-sub">${{periodoLabel}} — cada avaliacao (tecnico x mes) conta uma vez por criterio</div>
        <table><thead><tr><th>Criterio</th><th>Meta batida</th><th>Total avaliado</th><th>Aproveitamento</th></tr></thead>
          <tbody>${{criterios.map(([nome, v]) => `
            <tr>
              <td>${{esc(nome)}}</td>
              <td>${{v.batidas}}</td>
              <td>${{v.total}}</td>
              <td>${{v.total ? Math.round(v.batidas/v.total*100) : 0}}%</td>
            </tr>`).join('')}}
          </tbody></table>
      </div>
    `;
  }}
  selMes.addEventListener('change', renderGamificacao);
  renderGamificacao();
}}
if (sessionStorage.getItem('gamificacaoUnlocked') === '1') initGamificacao();

function tick() {{
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('pt-BR');
}}
setInterval(tick, 1000);
tick();

// Auto-refresh da pagina a cada 5 minutos (mesmo ciclo da atualizacao automatica dos dados).
// Nao recarrega se um modal estiver aberto, pra nao interromper quem esta olhando uma lista.
// Usa uma URL com timestamp (em vez de location.reload()) para forcar o navegador a buscar
// a versao mais nova do HTML na rede, sem risco de servir uma copia antiga do cache.
setInterval(() => {{
  const modalOpen = document.getElementById('modalOverlay') && document.getElementById('modalOverlay').classList.contains('open');
  if (!modalOpen) location.href = location.pathname + '?t=' + Date.now();
}}, 5 * 60 * 1000);
</script>
"""

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("Dashboard salvo em:", OUT_PATH)
