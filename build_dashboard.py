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
            'permanencyTimeWorkingTime': h.get('permanencyTimeWorkingTime'),
        })
    return out


# Notas/acoes de chamados as vezes trazem links de anexo com URLs assinadas do S3 do Movidesk
# (AWSAccessKeyId=...&Signature=...) ou outras credenciais coladas por engano — removidas antes de
# qualquer texto de acao ser embutido no HTML publicado, para nao vazar nada na pagina publica.
_S3_PRESIGNED_RE = re.compile(r'https://s3\.amazonaws\.com/\S+')
_AWS_KEY_RE = re.compile(r'AKIA[0-9A-Z]{16}')

def redact_secrets(text):
    if not text:
        return text
    text = _S3_PRESIGNED_RE.sub('[anexo removido]', text)
    text = _AWS_KEY_RE.sub('[chave removida]', text)
    return text

def clean_actions(raw_list):
    out = []
    for a in (raw_list or []):
        out.append({
            'description': redact_secrets(a.get('description') or ''),
            'createdDate': a.get('createdDate'),
            'type': a.get('type'),
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
    primeira_acao = (t.get('actions') or [{}])[0]
    clean.append({
        'id': t.get('id'),
        'protocol': t.get('protocol'),
        'subject': t.get('subject') or '',
        'description': redact_secrets(primeira_acao.get('description') or ''),
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
        'status': t.get('status'),
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

# Acoes/notas dos chamados tecnicos (Bug/Melhoria/Servicos) resolvidos no mes corrente — usadas so'
# pra achar, no log do DevOps/Azure, o comentario que marca task em validacao/impedimento. So existe
# pro mes corrente (mesma limitacao do statusHistories).
try:
    with open(os.path.join(BASE_DIR, "resolved_month_0_actions.json"), encoding='utf-8-sig') as f:
        raw_bug_actions = json.load(f)
except FileNotFoundError:
    raw_bug_actions = []
actions_by_id = {str(t.get('id')): clean_actions(t.get('actions')) for t in raw_bug_actions if t.get('id') is not None}

# Acoes dos chamados candidatos a expurgo retroativo de SLA por indisponibilidade de orgao
# governamental (resolvidos em 2026 e fora do prazo, ou ainda abertos) — ver fetch_data.py.
try:
    with open(os.path.join(BASE_DIR, "gov_check_actions.json"), encoding='utf-8-sig') as f:
        raw_gov_actions = json.load(f)
except FileNotFoundError:
    raw_gov_actions = []
gov_actions_by_id = {str(t.get('id')): clean_actions(t.get('actions')) for t in raw_gov_actions if t.get('id') is not None}

tickets_json = json.dumps(clean, ensure_ascii=False)
resolved_json = json.dumps(clean_resolved, ensure_ascii=False)
resolved_month_json = json.dumps(clean_resolved_month, ensure_ascii=False)
resolved_months_json = json.dumps(resolved_months_clean, ensure_ascii=False)
month_labels_json = json.dumps(month_labels, ensure_ascii=False)
actions_by_id_json = json.dumps(actions_by_id, ensure_ascii=False)
gov_actions_by_id_json = json.dumps(gov_actions_by_id, ensure_ascii=False)

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

.flow-wrap {{ display: flex; flex-direction: column; gap: 10px; }}
.flow-row {{ display: flex; align-items: stretch; gap: 6px; flex-wrap: wrap; }}
.flow-box {{
  background: var(--surface2); border: 1.5px solid var(--panel-border); border-radius: 8px;
  padding: 10px 14px; font-size: 12px; color: var(--text-dim); min-width: 140px; flex: 1;
  transition: all .2s ease; position: relative;
}}
.flow-box .flow-title {{ font-weight: 700; color: var(--text); font-size: 12.5px; margin-bottom: 3px; }}
.flow-box .flow-sub {{ font-size: 10.5px; color: var(--text3); line-height: 1.4; }}
.flow-box.flow-done {{ border-color: var(--ok-bord); background: var(--ok-dim); }}
.flow-box.flow-done .flow-title {{ color: var(--ok); }}
.flow-box.flow-current {{ border-color: var(--pink); background: var(--pink-dim); box-shadow: 0 0 0 2px rgba(237,109,162,0.25); }}
.flow-box.flow-current .flow-title {{ color: var(--pink); }}
.flow-box.flow-clickable {{ cursor: pointer; }}
.flow-box.flow-clickable:hover {{ border-color: var(--navy); box-shadow: var(--shadow2); }}
.flow-box.flow-clickable:focus-visible {{ outline: 2px solid var(--pink); outline-offset: 2px; }}
.flow-time {{ font-size: 10.5px; color: var(--text-dim); margin-top: 6px; font-weight: 600; }}
.flow-count {{ display: inline-block; margin-top: 4px; font-size: 10px; font-weight: 700; color: var(--pink); background: var(--pink-dim); border-radius: 20px; padding: 2px 8px; }}
.flow-arrow {{ display: flex; align-items: center; justify-content: center; color: var(--text3); font-size: 18px; padding: 0 2px; flex-shrink: 0; }}
.flow-branch {{ display: flex; flex-direction: column; gap: 6px; flex: 1; }}
.flow-sla-table {{ font-size: 11px; }}
.flow-sla-table td, .flow-sla-table th {{ padding: 4px 8px; }}
.flow-search-row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }}
.flow-timeline {{ display: flex; flex-direction: column; gap: 0; margin-top: 10px; }}
.flow-timeline-item {{ display: flex; gap: 10px; padding: 6px 0; border-left: 2px solid var(--panel-border); padding-left: 14px; margin-left: 6px; position: relative; }}
.flow-timeline-item::before {{ content: ''; position: absolute; left: -5px; top: 12px; width: 8px; height: 8px; border-radius: 50%; background: var(--text3); }}
.flow-timeline-item.is-last::before {{ background: var(--pink); }}
.flow-timeline-status {{ font-weight: 700; font-size: 12px; color: var(--text); min-width: 220px; }}
.flow-timeline-dur {{ font-size: 11.5px; color: var(--text-dim); }}
.flow-next-steps {{ background: var(--surface2); border-radius: 8px; padding: 12px 16px; font-size: 12.5px; color: var(--text); margin-top: 4px; border-left: 3px solid var(--pink); }}
.flow-next-options {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
.flow-next-pill {{
  background: var(--panel); border: 1.25px solid #878799; color: var(--text); font-size: 11.5px; font-weight: 600;
  padding: 6px 14px; border-radius: 20px; cursor: pointer; transition: all .15s ease;
}}
.flow-next-pill:hover {{ background: var(--pink-dim); border-color: var(--pink); color: var(--pink); }}
.flow-gantt {{ display: flex; width: 100%; height: 30px; border-radius: 6px; overflow: hidden; margin: 10px 0 6px; }}
.flow-gantt-seg {{ height: 100%; min-width: 3px; }}
.flow-gantt-legend {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 10.5px; color: var(--text-dim); margin-bottom: 6px; }}
.flow-gantt-legend-item {{ display: flex; align-items: center; gap: 5px; }}
.flow-gantt-swatch {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
.flow-stage-tag {{ display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; padding: 2px 8px; border-radius: 4px; background: var(--surface2); color: var(--text-dim); margin-left: 6px; }}

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
    <button class="tab-btn" id="tabBtnReuniaoMensal" onclick="showTab('reuniaoMensal')">Reuniao Mensal</button>
    <button class="tab-btn" id="tabBtnFluxo" onclick="showTab('fluxo')">Fluxograma</button>
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

  <div class="tab-panel" id="tabReuniaoMensal">
    <div class="panel" id="reuniaoMensalGate" style="max-width: 420px; margin: 60px auto; text-align:center;">
      <h2 style="justify-content:center;">🔒 Acesso restrito</h2>
      <div class="panel-sub" style="text-align:center; margin-bottom:14px;">Esta aba e de uso da lideranca. Informe a senha para continuar.</div>
      <input id="reuniaoMensalPassInput" type="password" class="itil-select" style="width:100%; text-align:center; margin-bottom:10px;" placeholder="Senha" />
      <div><span class="export-btn" style="padding:8px 22px; font-size:13px;" onclick="checkReuniaoMensalPassword()">Entrar</span></div>
      <div id="reuniaoMensalError" style="color:var(--danger); font-size:12px; margin-top:10px; display:none;">Senha incorreta.</div>
    </div>
    <div id="reuniaoMensalContent" style="display:none;">
      <div class="kpi-row" id="kpiReuniaoMensalMeta" style="grid-template-columns: repeat(1, 1fr);"></div>
      <div class="kpi-row" id="kpiReuniaoMensalSla" style="grid-template-columns: repeat(3, 1fr); margin-top:-4px;"></div>
      <div class="panel" style="margin-top: 18px;">
        <h2>📋 Chamados fechados por categoria (por mes)</h2>
        <div class="panel-sub">Ultimos 3 meses — time Suporte</div>
        <div id="tabelaReuniaoMensal"></div>
      </div>
    </div>
  </div>

  <div class="tab-panel" id="tabFluxo">
    <div class="flow-search-row">
      <input id="fluxoBuscaProtocolo" class="itil-select" style="max-width:220px;" placeholder="Buscar por numero do chamado" />
      <span class="export-btn" style="padding:9px 18px; font-size:12px;" onclick="buscarChamadoFluxoPorProtocolo()">Buscar</span>
      <span id="fluxoLimparBusca" class="export-btn" style="padding:9px 18px; font-size:12px; display:none;" onclick="limparBuscaFluxo()">Limpar</span>
      <span style="color:var(--text3); font-size:11px; margin-left:6px;">dados gerais de:</span>
      <select id="selMesFluxo" class="itil-select" title="Mes" style="max-width:160px; font-size:12px; padding:4px 8px;"></select>
      <select id="selClienteFluxo" class="itil-select" title="Cliente" style="max-width:220px; font-size:12px; padding:4px 8px;"></select>
    </div>
    <div id="fluxoErro" style="display:none; color:var(--danger); font-size:12.5px; margin-bottom:10px;"></div>

    <div class="panel">
      <h2>🧭 Fluxo de atendimento — Central de Suporte EmiteAi</h2>
      <div class="panel-sub" id="fluxoChamadoInfo">Cada etapa mostra o tempo medio do periodo/cliente selecionado e quantos chamados estao nela agora — clique numa etapa pra ver a lista, ou busque um chamado especifico pelo numero.</div>
      <div class="flow-wrap" id="flowDiagram"></div>
    </div>

    <div class="grid" id="gridFluxoEntrada" style="grid-template-columns: 1fr 1fr; margin-top: 18px;">
      <div class="panel">
        <h2>📥 Entrada — por canal</h2>
        <div class="panel-sub" id="fluxoEntradaSub">Chamados abertos agora, por forma de abertura</div>
        <div id="fluxoEntradaBars"></div>
      </div>
      <div class="panel">
        <h2>🐞 Em desenvolvimento — por categoria</h2>
        <div class="panel-sub">Chamados abertos agora na fila de desenvolvimento, por categoria</div>
        <div id="fluxoDevBars"></div>
      </div>
    </div>

    <div class="grid" id="gridFluxo" style="grid-template-columns: 1fr 1fr; margin-top: 18px;">
      <div class="panel">
        <h2>⏱️ SLA de repasse para N2</h2>
        <div class="panel-sub">Prazo a partir do momento em que o N1 aciona o N2 · tempo medio observado no periodo/cliente selecionado</div>
        <table class="flow-sla-table">
          <thead><tr><th>Classificacao</th><th>Prazo (SLA)</th><th>Tempo medio observado</th><th>Observacao</th></tr></thead>
          <tbody id="fluxoSlaTbody"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>📍 Chamado selecionado — proximos passos</h2>
        <div id="fluxoProximosPassos"><div class="empty-msg">Nenhum chamado selecionado — dados gerais acima</div></div>
      </div>
    </div>

    <div class="panel" style="margin-top: 18px;">
      <h2>🕒 Linha do tempo do chamado</h2>
      <div class="panel-sub" id="fluxoTimelineSub">Busque um chamado para ver a linha do tempo por status</div>
      <div id="fluxoGantt"></div>
      <div class="flow-timeline" id="fluxoTimeline"></div>
    </div>
  </div>

  <div class="footer-note">
    Board gerado a partir do Movidesk (chamados nao fechados/cancelados/resolvidos) · Atualizacao agendada a cada 5 minutos · "Aging" = Em atendimento sem update ha 48h+ · "Contraturno" = chamados em atendimento com Alife Caetano dos Santos ou Vinicius Campestrini
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
const RESOLVED_MONTH_ALL = ({resolved_month_json}).filter(r => r.ownerTeam === 'Suporte' && r.status !== 'Cancelado' && !reaberturaIndevidaAzure(r));
// RESOLVED_MONTH e chatsMes ficam mutaveis (let) porque a aba Historico pode filtrar por cliente
// e reatribui-los em renderHistoricoMes() — assim os modais de drill-down (openModalHist*) sempre
// refletem o filtro de cliente atualmente selecionado.
let RESOLVED_MONTH = RESOLVED_MONTH_ALL;
let chatsMes = [];
const RESOLVED_MONTHS_RAW = {resolved_months_json};
const MONTH_LABELS = {month_labels_json};
// Notas/acoes dos chamados tecnicos (Bug/Melhoria/Servicos) resolvidos no mes corrente, indexadas por
// id do chamado — usadas so' pra achar, no log do DevOps/Azure, o comentario que marca a task em
// validacao/impedimento (o Movidesk nao tem status proprio pra isso).
const ACTIONS_BY_ID = {actions_by_id_json};
// Notas/acoes completas dos chamados candidatos a expurgo retroativo de SLA por indisponibilidade de
// orgao governamental (resolvidos em 2026 e fora do prazo, ou ainda abertos) — ver fetch_data.py.
const GOV_ACTIONS_BY_ID = {gov_actions_by_id_json};
// Todos os 3 meses, ja restritos ao time de Suporte, sem chamados Cancelados, e sem chamados
// reabertos INDEVIDAMENTE pelo Azure (reaberturas legitimas continuam contando normalmente).
// Esse filtro fica aqui na origem dos dados porque TODAS as abas (Historico, Clientes, One-on-One,
// Gamificacao, Reuniao Mensal) partem de RESOLVED_MONTHS — um unico lugar garante consistencia.
const RESOLVED_MONTHS = {{}};
Object.keys(RESOLVED_MONTHS_RAW).forEach(k => {{
  RESOLVED_MONTHS[k] = RESOLVED_MONTHS_RAW[k].filter(r => r.ownerTeam === 'Suporte' && r.status !== 'Cancelado' && !reaberturaIndevidaAzure(r));
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
// (passam pela fila de dev). Duvida, Erro Operacional e Terceiros NAO deveriam ter task —
// se um desses tiver passado pela fila de dev, e sinal real de categoria errada.
// O Movidesk unificou os status "Aguardando Desenvolvimento" (produto/bug/GNRE etc.) em um so —
// mantemos tambem o nome antigo ('...- fila Bugs') pra continuar reconhecendo chamados historicos.
function isDevQueueStatus(status) {{
  return status === 'Aguardando Desenvolvimento' || status === 'Aguardando Desenvolvimento - fila Bugs';
}}
// Status criado para o repasse N1 -> N2: quando o N1 (ou CS/Implantacao) muda o chamado pra este
// status, o N2 passa a monitorar a fila; o chamado so muda de dono quando o N2 efetivamente assume.
const N2_HANDOFF_STATUS = 'Em atendimento - N2';
// A partir desta troca de status, o SLA fica pausado enquanto o chamado depende de orgao governamental
// (SEFAZ, ANTT, Portal Nacional da GNRE) — conforme contrato com o cliente.
function isGovWaitStatus(status) {{
  return /sefaz|antt/i.test(status || '');
}}
const CATEGORIAS_SEM_TASK = ['Dúvida', 'Erro Operacional', 'Terceiros'];
TICKETS.forEach(t => {{
  const passouPorFilaBugs = (t.statusHistories||[]).some(h => isDevQueueStatus(h.status));
  t._classificacaoIncorreta = CATEGORIAS_SEM_TASK.indexOf(t.category) !== -1 && passouPorFilaBugs;
  t._motivoClassificacao = 'categoria "' + t.category + '" com task associada (fila de dev)';
}});
// Chamados resolvidos que passaram pelo status de espera de orgao governamental (SEFAZ/ANTT/GNRE) tem
// o tempo nesse status excluido do calculo de SLA — so detectavel via historico de status, disponivel
// apenas para o mes corrente (RESOLVED_MONTHS['0']).
// Texto de log/comentario indicando indisponibilidade de orgao governamental (usado como fallback
// retroativo, pra chamados de antes do status 'Aguardando Sefaz/ANTT' existir).
const GOV_LOG_RE = /sefaz|antt|prefeitura|portal nacional da gnre/i;
function aguardouOrgaoGovernamental(r) {{
  if ((r.statusHistories || []).some(h => isGovWaitStatus(h.status))) return true;
  const acoes = GOV_ACTIONS_BY_ID[String(r.id)] || [];
  return acoes.some(a => GOV_LOG_RE.test(a.description || ''));
}}

const FILTERS = {{
  novos: t => t.status === 'Novo',
  emAtendimento: t => t.status === 'Em atendimento',
  aguardandoCliente: t => t.status === 'Aguardando Cliente',
  bouncing: t => t.ownerTeam === 'Suporte' && t.status === 'Em atendimento' && t._hoursSinceUpdate !== null && t._hoursSinceUpdate >= 48,
  priorizados: t => t.ownerTeam === 'Suporte' && t._isPriorizado,
  contraturno: t => t.status === 'Em atendimento' && CONTRATURNO_TECNICOS.indexOf(t.ownerName) !== -1,
  naoAtualizadosHoje: t => (t.status === 'Em atendimento' || t.status === 'Aguardando Cliente') && !t._updatedToday,
  cargaParada: t => t.status === 'Em atendimento' && (CARGA_PARADA_RE.test(t.subject || '') || CARGA_PARADA_RE.test(t.description || '')),
  classificacaoIncorreta: t => t._classificacaoIncorreta,
  chatsEmAtendimento: t => t.status === 'Em atendimento' && (t.origin === 24 || !!t.chatGroup),
  chatsAguardando: t => t.status === 'Novo' && (t.origin === 24 || !!t.chatGroup),
}};

// --- Priorizacao operacional ---
// Ordem de atendimento pedida: 1) bloqueio operacional (MDFe/CIOT/GNRE/integracoes/carga travada,
// cadeia logistica conectada) -> 2) risco fiscal (possiveis multas). Niveis 3/4 (recorrencia/outros)
// foram removidos — chamados que nao se encaixam em 1 ou 2 nao aparecem mais nesta fila.
const OPERACIONAL_RE = /mdf[-\s]?e|\bciot\b|\bgnre\b|integra[cç][aã]o|carga\s*(trava|parad)|travad/i;
const FISCAL_RISCO_RE = /multa|risco fiscal|imposto|difal|\bicms\b|vencimento.*guia|guia.*vencid/i;

// Niveis 3 (Recorrencia/melhoria) e 4 (Outros) foram removidos a pedido — a fila agora so' lista
// chamados que se encaixam em bloqueio operacional ou risco fiscal (niveis 1 e 2).
function priorityTier(t) {{
  const s = t.subject || '';
  const isFiscal = FISCAL_RISCO_RE.test(s);
  const isOperacional = OPERACIONAL_RE.test(s);
  if (isOperacional && !isFiscal) return 1;
  if (isFiscal) return 2;
  return null;
}}
const TIER_INFO = {{
  1: {{ label: 'Bloqueio operacional', cls: 'tier-1' }},
  2: {{ label: 'Risco fiscal (multas)', cls: 'tier-2' }},
}};
const ATIVOS = TICKETS; // todos os TICKETS ja sao nao-fechados (o filtro antigo era um no-op)
ATIVOS.forEach(t => {{ t._tier = priorityTier(t); }});
const filaPriorizada = ATIVOS.filter(t => t._tier !== null).slice().sort((a,b) => {{
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
  bouncing: 'Aging — Em atendimento parado ha mais de 2 dias',
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
// Situacoes recorrentes no mes: agrupa os chamados resolvidos por assunto normalizado, listando os
// que se repetiram 2+ vezes e quais clientes ("ofensores") tiveram esse mesmo problema.
function normalizeSubjectHist(s) {{
  return (s || '').toLowerCase().replace(/[^a-z0-9à-ü ]/g, '').replace(/\s+/g, ' ').trim();
}}
function chamadosRecorrentesDoMes(items) {{
  const grupos = {{}};
  items.forEach(r => {{
    const key = normalizeSubjectHist(r.subject);
    if (!key) return;
    if (!grupos[key]) grupos[key] = {{ subject: r.subject, protocolos: new Set(), clientes: new Set(), count: 0 }};
    grupos[key].protocolos.add(r.protocol);
    grupos[key].clientes.add(r.clientOrg || 'Sem cliente');
    grupos[key].count++;
  }});
  return Object.values(grupos).filter(g => g.count >= 2).sort((a,b) => b.count - a.count);
}}
function renderRecorrenciasHtml(grupos) {{
  if (!grupos.length) return '<div class="empty-msg">Nenhuma situacao recorrente identificada no mes</div>';
  return grupos.map((g, i) => `
    <div class="bar-row" onclick="abrirModalRecorrencia(${{i}})">
      <div class="bar-label" style="width:auto; flex:1;">${{esc(g.subject)}} <span style="color:var(--text3); font-size:10.5px;">(${{Array.from(g.clientes).slice(0,3).map(esc).join(', ')}}${{g.clientes.size>3 ? ' +'+(g.clientes.size-3) : ''}})</span></div>
      <div class="bar-value">${{g.count}}</div>
    </div>
  `).join('');
}}
function abrirModalRecorrencia(idx) {{
  const grupos = chamadosRecorrentesDoMes(RESOLVED_MONTH);
  const g = grupos[idx];
  if (!g) return;
  const items = RESOLVED_MONTH.filter(r => g.protocolos.has(r.protocol));
  renderModalHist(`Recorrencia — ${{g.subject}}`, items);
}}
function openModalHistCategoria(cat) {{
  const items = RESOLVED_MONTH.filter(r => (r.category || 'Sem categoria') === cat && r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r));
  renderModalHist(`SLA — ${{cat}} (mes)`, items);
}}
function openModalHistSimple(kind) {{
  if (kind === 'primeiraRespostaHoje') renderModalHist('Resolvidos c/ 1a resposta (hoje)', RESOLVED_TODAY.filter(isPrimeiraResposta));
  else if (kind === 'primeiraRespostaMes') renderModalHist('Resolvidos c/ 1a resposta (mes)', RESOLVED_MONTH.filter(isPrimeiraResposta));
  else if (kind === 'slaNoPrazoMes') renderModalHist('Fora do SLA (mes) — todas categorias', RESOLVED_MONTH.filter(r => {{
    if (!r.slaSolutionDate || reaberturaIndevidaAzure(r) || aguardouOrgaoGovernamental(r)) return false;
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
function kpiTileClick(cls, count, label, onclickExpr, hint) {{
  return `<div class="kpi ${{cls}}" tabindex="0" role="button" onclick="${{onclickExpr}}" onkeydown="if(event.key==='Enter'){{${{onclickExpr}}}}">
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
  document.getElementById('tabReuniaoMensal').classList.toggle('active', name === 'reuniaoMensal');
  document.getElementById('tabFluxo').classList.toggle('active', name === 'fluxo');
  document.getElementById('tabBtnLive').classList.toggle('active', name === 'live');
  document.getElementById('tabBtnHist').classList.toggle('active', name === 'hist');
  document.getElementById('tabBtnClientes').classList.toggle('active', name === 'clientes');
  document.getElementById('tabBtnOneOnOne').classList.toggle('active', name === 'oneOnOne');
  document.getElementById('tabBtnGamificacao').classList.toggle('active', name === 'gamificacao');
  document.getElementById('tabBtnReuniaoMensal').classList.toggle('active', name === 'reuniaoMensal');
  document.getElementById('tabBtnFluxo').classList.toggle('active', name === 'fluxo');
  if (!skipSave) localStorage.setItem('activeTab', name);
}}
// Restaura a aba ativa apos o auto-refresh da pagina (nunca restaura direto em abas com senha, exige senha de novo)
const _savedTab = localStorage.getItem('activeTab') || 'live';
const _abasComSenha = ['oneOnOne', 'gamificacao', 'reuniaoMensal'];
showTab(_abasComSenha.indexOf(_savedTab) !== -1 ? 'live' : _savedTab, true);

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
// comparando data de resolucao contra o prazo de SLA (slaSolutionDate).
// So exclui os reabertos INDEVIDAMENTE (integracao do Azure) — reaberturas legitimas contam normalmente.
const slaPorCategoria = {{}};
RESOLVED_MONTH.filter(r => r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r)).forEach(r => {{
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

// --- Ciclo de atendimento tecnico (N1 -> N2 -> dev), usado no ciclo de vida do Bug (Historico) e
// nos indicadores tecnicos N1/N2 (One-on-One) ---
// Baseado no historico de status (statusHistories) de cada chamado, com 3 etapas:
// - "tempo de repasse - N1": tempo UTIL (permanencyTimeWorkingTime, exclui 'Aguardando Cliente') desde
//   a abertura do chamado ate ele ser passado pro status 'Em atendimento - N2' (repasse do N1 pro N2).
// - "tempo abertura task": tempo (corrido) desde o repasse pro N2 ate o chamado entrar na fila de
//   desenvolvimento ('Aguardando Desenvolvimento') — ou seja, ate a task ser de fato aberta/vinculada.
// - "tempo aberto no devops": desde a task aberta ate o devops registrar (via nota/comentario do
//   Azure, buscada em ACTIONS_BY_ID) que o chamado foi pra validacao ou ficou em impedimento; quando
//   nao ha essa nota (integracao nao logou, ou chamado antigo), cai no fallback de somar o tempo
//   corrido em todas as passagens pela fila de desenvolvimento (comportamento anterior a este ajuste).
function calcularCicloAtendimentoTecnico(r) {{
  if (!(r.statusHistories || []).length) return null;
  const hist = r.statusHistories.map(h => ({{ ...h, _d: parseDt(h.changedDate) }})).sort((a,b) => a._d - b._d);

  const idxN2 = hist.findIndex(h => h.status === N2_HANDOFF_STATUS);
  const tempoRepasseN1H = idxN2 > 0
    ? hist.slice(0, idxN2).filter(h => h.status !== 'Aguardando Cliente').reduce((s,h) => s + (h.permanencyTimeWorkingTime || 0), 0) / 3600
    : (idxN2 === 0 ? 0 : null);

  // "passou por task" (gerou task de dev) nao depende do repasse pro N2 ter acontecido — chamados do
  // fluxo antigo (antes do status 'Em atendimento - N2' existir) tambem geram task normalmente.
  const idxDevQueueAny = hist.findIndex(h => isDevQueueStatus(h.status));
  // Ja o "tempo abertura task" (repasse -> task) so faz sentido quando existe o repasse pro N2 —
  // usamos a primeira entrada na fila de dev QUE VEM DEPOIS do repasse.
  let idxDevQueueAposN2 = -1;
  if (idxN2 !== -1) {{
    for (let i = idxN2; i < hist.length; i++) {{
      if (isDevQueueStatus(hist[i].status)) {{ idxDevQueueAposN2 = i; break; }}
    }}
  }}
  const tempoAberturaTaskH = (idxN2 !== -1 && idxDevQueueAposN2 !== -1)
    ? hist.slice(idxN2, idxDevQueueAposN2).reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0) / 3600
    : null;

  // Ancora do tempo em devops: prefere a entrada na fila de dev POS-repasse (fluxo novo); se nao houver
  // repasse pro N2 registrado (chamado do fluxo antigo), usa a primeira entrada na fila de dev, igual
  // ao calculo anterior a este ajuste.
  const idxDevQueueAncora = idxDevQueueAposN2 !== -1 ? idxDevQueueAposN2 : idxDevQueueAny;
  let devopsSeconds = null;
  if (idxDevQueueAncora !== -1) {{
    const devEntryDate = hist[idxDevQueueAncora]._d;
    const acoes = ACTIONS_BY_ID[String(r.id)] || [];
    const logDevops = acoes
      .map(a => ({{ ...a, _d: parseDt(a.createdDate) }}))
      .filter(a => a._d && devEntryDate && a._d > devEntryDate && /valida|impedimento/i.test(a.description || ''))
      .sort((a,b) => a._d - b._d)[0];
    devopsSeconds = logDevops
      ? (logDevops._d - devEntryDate) / 1000
      : hist.filter(h => isDevQueueStatus(h.status)).reduce((s,h) => s + (h.permanencyTimeFullTime || 0), 0);
  }}

  return {{
    protocol: r.protocol,
    urgency: r.urgency,
    ownerName: r.ownerName,
    tempoRepasseN1H,
    tempoAberturaTaskH,
    devopsH: devopsSeconds !== null ? devopsSeconds / 3600 : null,
    passouPorN2: idxN2 !== -1,
    passouPorTask: idxDevQueueAny !== -1,
  }};
}}
// bugsMes/bugMetrics ficam mutaveis (let) porque a aba Historico pode filtrar por cliente e reatribui-los
// em renderHistoricoMes() — assim o clique nos cards (abrirModalBugMetrica) sempre reflete o filtro atual.
let bugsMes = RESOLVED_MONTH.filter(r => r.category === 'Bug' && (r.statusHistories||[]).length);
let bugMetrics = bugsMes.map(calcularCicloAtendimentoTecnico).filter(Boolean);
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

// Detecta reabertura INDEVIDA (integracao com o Azure reabrindo o chamado logo apos ele ja ter sido
// marcado Resolvido/Fechado, sem uma pessoa envolvida) — diferente de uma reabertura legitima feita
// por cliente/agente. So' e possivel verificar quando o historico de status esta disponivel (mes
// corrente); nos demais meses nao ha como confirmar, entao o chamado e tratado como reabertura
// legitima por padrao (conta normalmente no SLA), a favor de nao penalizar avaliacoes antigas por engano.
// Heuristica: reaberto em menos de 60 minutos apos a transicao anterior ter sido Resolvido/Fechado —
// tempo curto demais para ser uma acao manual de cliente/agente.
function reaberturaIndevidaAzure(r) {{
  if (!r.reopenedIn || !(r.statusHistories || []).length) return false;
  const hist = r.statusHistories.map(h => ({{ ...h, _d: parseDt(h.changedDate) }})).sort((a,b) => a._d - b._d);
  const reopenDt = parseDt(r.reopenedIn);
  let idxReopen = -1;
  for (let i = 0; i < hist.length; i++) {{
    if (hist[i]._d && Math.abs(hist[i]._d - reopenDt) < 5000) {{ idxReopen = i; break; }}
  }}
  if (idxReopen <= 0) return false;
  const anterior = hist[idxReopen - 1];
  if (anterior.status !== 'Resolvido' && anterior.status !== 'Fechado') return false;
  const gapMin = (reopenDt - anterior._d) / 60000;
  return gapMin < 60;
}}

// Media dos ultimos 3 meses (usada como referencia em varios cards) — so' cobre campos
// disponiveis em todos os meses (statusHistories so' fica no mes corrente, entao metricas
// de ciclo de vida do Bug nao entram aqui).
function statsForMonth(items) {{
  const total = items.length;
  const primeira = items.filter(isPrimeiraResposta).length;
  const pctPrimeira = total ? Math.round(primeira / total * 100) : 0;
  // So exclui do SLA os chamados reabertos INDEVIDAMENTE (pela integracao do Azure, apos ja estarem
  // Resolvido/Fechado) — reaberturas legitimas (cliente/agente) continuam contando normalmente.
  const comSla = items.filter(r => r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r));
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
  const comRepasse = subset.filter(b => b.tempoRepasseN1H !== null).map(b => b.tempoRepasseN1H);
  const comAberturaTask = subset.filter(b => b.tempoAberturaTaskH !== null).map(b => b.tempoAberturaTaskH);
  const comDevops = subset.filter(b => b.devopsH !== null).map(b => b.devopsH);
  return {{
    total: subset.length,
    comRepasse, comAberturaTask, comDevops,
    mediaRepasseN1: avg(comRepasse),
    mediaAberturaTask: avg(comAberturaTask),
    mediaDevops: avg(comDevops),
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
// So' disponivel para o mes corrente (offset 0) — statusHistories nao e mantido nos meses anteriores.
function computeN2Metrics(tecnico, periodoKey) {{
  if (periodoKey !== '0') return null;
  const items = (RESOLVED_MONTHS['0'] || []).filter(r => r.ownerName === tecnico && CATEGORIAS_TECNICAS_N2.indexOf(r.category) !== -1);
  const ciclos = items.map(calcularCicloAtendimentoTecnico).filter(Boolean);
  const total = items.length;
  const comTask = ciclos.filter(c => c.passouPorTask).length;
  return {{
    total,
    pctTask: total ? Math.round(comTask / total * 100) : null,
    devopsMedio: avg(ciclos.filter(c => c.devopsH !== null).map(c => c.devopsH)),
    validacaoMedio: avg(ciclos.filter(c => c.tempoAberturaTaskH !== null).map(c => c.tempoAberturaTaskH)),
  }};
}}
// Indicador N1: tempo desde que o chamado foi aberto ate ser repassado pro status 'Em atendimento - N2'.
// Antes disso existir no Movidesk, esta metrica usava a entrada na fila de Bugs como proxy (aproximacao);
// agora usa o repasse real de status, criado especificamente pra marcar quando o N1 aciona o N2. So'
// disponivel para o mes corrente (statusHistories).
function computeN1Metrics(tecnico, periodoKey) {{
  if (periodoKey !== '0') return null;
  const items = (RESOLVED_MONTHS['0'] || []).filter(r => r.ownerName === tecnico && CATEGORIAS_TECNICAS_N2.indexOf(r.category) !== -1);
  const ciclos = items.map(calcularCicloAtendimentoTecnico).filter(Boolean);
  const total = items.length;
  const acionaramN2 = ciclos.filter(c => c.passouPorN2);
  return {{
    total,
    qtdAcionouN2: acionaramN2.length,
    tempoAteAcionarN2Medio: avg(acionaramN2.filter(c => c.tempoRepasseN1H !== null).map(c => c.tempoRepasseN1H)),
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

// Cor por faixa de volume: verde ate okAte, amarelo ate warnAte, vermelho acima disso.
function corPorFaixa(valor, okAte, warnAte) {{
  if (valor <= okAte) return 'ok';
  if (valor <= warnAte) return 'warn';
  return 'danger';
}}

document.getElementById('kpiRow').innerHTML =
  kpiTile('neutral', novos.length, 'Novos (aguard. atend.)', 'novos') +
  kpiTile(corPorFaixa(emAtendimento.length, 19, 50), emAtendimento.length, 'Em atendimento', 'emAtendimento') +
  kpiTile(corPorFaixa(aguardandoCliente.length, 19, 50), aguardandoCliente.length, 'Aguardando cliente', 'aguardandoCliente') +
  kpiTile(corPorFaixa(bouncing.length, 0, 10), bouncing.length, 'Aging (Em atend. &gt;2 dias)', 'bouncing');

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

// MTTR desconsidera chamados de categoria 'Melhoria' (que costumam ficar muito tempo em aberto e
// distorcem a media) — os demais filtros (Suporte, sem Cancelado, sem reabertura indevida do Azure)
// ja vem de RESOLVED_MONTH/RESOLVED_MONTHS na origem.
function mttrSemMelhoria(items) {{
  const comTempo = items.filter(r => r.category !== 'Melhoria' && r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 3600000);
  return avg(comTempo);
}}
const mttrMesAtual = mttrSemMelhoria(RESOLVED_MONTH);
const mttrPorMes3 = Object.keys(MONTH_LABELS).map(k => ({{ key: k, label: MONTH_LABELS[k], mttrH: mttrSemMelhoria(RESOLVED_MONTHS[k]) }}));
const mttrMedia3Meses = avg(mttrPorMes3.filter(s => s.mttrH !== null).map(s => s.mttrH));
const comparativoMttrSemMelhoria = mttrPorMes3.map(s => `${{s.label.split('/')[0].slice(0,3)}}: ${{s.mttrH !== null ? fmtH(s.mttrH) : '-'}}`).join(' · ');
const metaMttr = metaMelhoria10(mttrMedia3Meses, true);
const mttrBateMeta = bateMeta(mttrMesAtual, metaMttr, true);
document.getElementById('kpiRowHistMttr').innerHTML =
  kpiTileStatic(mttrBateMeta === null ? 'warn' : (mttrBateMeta ? 'ok' : 'danger'), mttrMesAtual !== null ? fmtH(mttrMesAtual) : '-', 'Tempo medio de atendimento (MTTR)', `mes corrente: ${{MONTH_LABELS['0']}} · exclui Melhoria · media 3m: ${{mttrMedia3Meses !== null ? fmtH(mttrMedia3Meses) : '-'}} · meta (10% menor que a media 3m): ${{metaMttr !== null ? fmtH(metaMttr) : '-'}} · ultimos 3 meses: ${{comparativoMttrSemMelhoria}}`);

// Abre a lista de chamados (bugs) por tras de um dos 3 cards de ciclo de atendimento tecnico.
function abrirModalBugMetrica(urgency, metrica) {{
  const subset = bugMetrics.filter(b => b.urgency === urgency);
  let elegiveis;
  if (metrica === 'repasse') elegiveis = subset.filter(b => b.tempoRepasseN1H !== null);
  else if (metrica === 'task') elegiveis = subset.filter(b => b.tempoAberturaTaskH !== null);
  else elegiveis = subset.filter(b => b.devopsH !== null);
  const protocolos = new Set(elegiveis.map(b => b.protocol));
  const items = bugsMes.filter(r => protocolos.has(r.protocol));
  const NOMES = {{ repasse: 'Tempo de repasse - N1', task: 'Tempo abertura task', devops: 'Tempo aberto no devops' }};
  renderModalHist(`Bugs — ${{NOMES[metrica]}} (${{urgency}})`, items);
}}
function renderBugMetricsRow(elId, m, urgency) {{
  // Sem meta/limite definido para estes 3 tempos — cor neutra (nao ha "bom"/"ruim" estabelecido ainda).
  document.getElementById(elId).innerHTML =
    kpiTileClick('neutral', m.mediaRepasseN1!==null ? fmtH(m.mediaRepasseN1) : '-', 'Tempo de repasse - N1', `abrirModalBugMetrica(${{jsStr(urgency)}}, 'repasse')`, `media sobre ${{m.comRepasse.length}} de ${{m.total}} bugs · tempo util (exclui Aguardando Cliente) da abertura ate 'Em atendimento - N2'`) +
    kpiTileClick('neutral', m.mediaAberturaTask!==null ? fmtH(m.mediaAberturaTask) : '-', 'Tempo abertura task', `abrirModalBugMetrica(${{jsStr(urgency)}}, 'task')`, `media sobre ${{m.comAberturaTask.length}} bugs · de 'Em atendimento - N2' ate entrar na fila de desenvolvimento`) +
    kpiTileClick('neutral', m.mediaDevops!==null ? fmtH(m.mediaDevops) : '-', 'Tempo aberto no devops', `abrirModalBugMetrica(${{jsStr(urgency)}}, 'devops')`, `media sobre ${{m.comDevops.length}} bugs · ate log de validacao/impedimento do devops (ou, se nao houver log, tempo total na fila)`);
}}
renderBugMetricsRow('kpiRowHistBugMedia', bugMetricsMedia, 'Média');
renderBugMetricsRow('kpiRowHistBugAlta', bugMetricsAlta, 'Alta');

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
    <h2>🔴 Aging — em atendimento parado ha mais de 2 dias${{exportButtonHtml("exportLiveList(bouncing, 'bouncing.txt')")}}</h2>
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
    <div class="panel-sub">${{classificacaoIncorreta.length}} chamados abertos com categoria diferente de Bug, mas que ja passaram pela fila de desenvolvimento ou tem assunto de bug</div>
    <table><thead><tr><th>Chamado</th><th>Assunto</th><th>Categoria atual</th><th>Motivo</th><th>Tecnico</th></tr></thead>
      <tbody>${{tableHtmlMisclass(classificacaoIncorreta, 14)}}</tbody></table>
  </div>
`;

document.getElementById('gridHist').innerHTML = `
  <div class="panel">
    <h2>⏱️ SLA por categoria (resolvidos no mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r)), 'sla_por_categoria.txt')")}}</h2>
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
  <div class="panel" style="flex-basis:100%; width:100%;">
    <h2>🔁 Situacoes recorrentes no mes${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>chamadosRecorrentesDoMes(RESOLVED_MONTH).some(g=>g.protocolos.has(r.protocol))), 'recorrencias_mes.txt')")}}</h2>
    <div class="panel-sub">Assuntos que se repetiram 2 ou mais vezes entre os chamados resolvidos no mes, com os clientes ofensores</div>
    <div>${{renderRecorrenciasHtml(chamadosRecorrentesDoMes(RESOLVED_MONTH))}}</div>
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
  RESOLVED_MONTH.filter(r => r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r)).forEach(r => {{
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

  bugsMes = RESOLVED_MONTH.filter(r => r.category === 'Bug' && (r.statusHistories||[]).length);
  bugMetrics = bugsMes.map(calcularCicloAtendimentoTecnico).filter(Boolean);
  const bugMetricsMediaF = bugMetricsFor('Média');
  const bugMetricsAltaF = bugMetricsFor('Alta');

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

  function mttrSemMelhoriaCliente(items) {{
    const filtrados = clienteFiltro ? items.filter(r => r.clientOrg === clienteFiltro) : items;
    return mttrSemMelhoria(filtrados);
  }}
  const mttrMesAtualF = mttrSemMelhoriaCliente(RESOLVED_MONTH);
  const mttrPorMes3F = Object.keys(MONTH_LABELS).map(k => ({{ key: k, label: MONTH_LABELS[k], mttrH: mttrSemMelhoriaCliente(RESOLVED_MONTHS[k]) }}));
  const mttrMedia3MesesF = avg(mttrPorMes3F.filter(s => s.mttrH !== null).map(s => s.mttrH));
  const comparativoMttrSemMelhoriaF = mttrPorMes3F.map(s => `${{s.label.split('/')[0].slice(0,3)}}: ${{s.mttrH !== null ? fmtH(s.mttrH) : '-'}}`).join(' · ');
  const metaMttrF = metaMelhoria10(mttrMedia3MesesF, true);
  const mttrBateMetaF = bateMeta(mttrMesAtualF, metaMttrF, true);
  document.getElementById('kpiRowHistMttr').innerHTML =
    kpiTileStatic(mttrBateMetaF === null ? 'warn' : (mttrBateMetaF ? 'ok' : 'danger'), mttrMesAtualF !== null ? fmtH(mttrMesAtualF) : '-', 'Tempo medio de atendimento (MTTR)', `mes corrente: ${{MONTH_LABELS['0']}} · exclui Melhoria · media 3m: ${{mttrMedia3MesesF !== null ? fmtH(mttrMedia3MesesF) : '-'}} · meta (10% menor que a media 3m): ${{metaMttrF !== null ? fmtH(metaMttrF) : '-'}} · ultimos 3 meses: ${{comparativoMttrSemMelhoriaF}}${{filtroSufixo}}`);

  renderBugMetricsRow('kpiRowHistBugMedia', bugMetricsMediaF, 'Média');
  renderBugMetricsRow('kpiRowHistBugAlta', bugMetricsAltaF, 'Alta');

  document.getElementById('gridHist').innerHTML = `
    <div class="panel">
      <h2>⏱️ SLA por categoria (resolvidos no mes)${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r)), 'sla_por_categoria.txt')")}}</h2>
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
    <div class="panel" style="flex-basis:100%; width:100%;">
      <h2>🔁 Situacoes recorrentes no mes${{exportButtonHtml("exportHistListToExcel(RESOLVED_MONTH.filter(r=>chamadosRecorrentesDoMes(RESOLVED_MONTH).some(g=>g.protocolos.has(r.protocol))), 'recorrencias_mes.txt')")}}</h2>
      <div class="panel-sub">Assuntos que se repetiram 2 ou mais vezes entre os chamados resolvidos no mes${{filtroSufixo}}, com os clientes ofensores</div>
      <div>${{renderRecorrenciasHtml(chamadosRecorrentesDoMes(RESOLVED_MONTH))}}</div>
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
  // So exclui do SLA os chamados reabertos INDEVIDAMENTE (integracao do Azure, apos ja estarem
  // Resolvido/Fechado) — reaberturas legitimas (cliente/agente) continuam contando normalmente.
  const comSla = items.filter(r => r.slaSolutionDate && !reaberturaIndevidaAzure(r) && !aguardouOrgaoGovernamental(r));
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
      kpiTileStatic(corPorFaixa(bouncingTecnico, 0, 5), bouncingTecnico, 'Aging atual (>2 dias)', 'situacao ao vivo, nao e do periodo') +
      kpiTileStatic(corPorFaixa(naoAtualizadosTecnico, 0, 5), naoAtualizadosTecnico, 'Nao atualizados hoje', 'situacao ao vivo, nao e do periodo');

    // Metas — melhoria de 10% ao mes sobre a media dos ultimos 3 meses do proprio tecnico.
    // Aging/nao-atualizados sao indicadores ao vivo (sem serie mensal), entao continuam com meta fixa de zero.
    const metaMttrTec = metaMelhoria10(m3.mttrH, true);
    const metaSlaTec = metaMelhoria10(m3.pctSla, false);
    const metaPrimeiraTec = metaMelhoria10(m3.pctPrimeira, false);
    const mttrBateMetaTec = bateMeta(ind.mttrH, metaMttrTec, true);
    const slaBateMetaTec = bateMeta(ind.pctSla, metaSlaTec, false);
    const primeiraBateMetaTec = bateMeta(pctPrimeira, metaPrimeiraTec, false);
    document.getElementById('kpiOneOnOneMetas').innerHTML =
      kpiTileStatic(bouncingTecnico === 0 ? 'ok' : 'danger', bouncingTecnico === 0 ? 'Meta batida' : 'Meta nao batida', 'Meta: 0 aging', `atual: ${{bouncingTecnico}} chamado(s) em aging`) +
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
          kpiTileStatic('neutral', n2.pctTask !== null ? `${{n2.pctTask}}%` : '-', '% com task associada (fila de dev)', 'de chamados tecnicos que geraram task de dev') +
          kpiTileStatic('warn', n2.devopsMedio !== null ? fmtH(n2.devopsMedio) : '-', 'Tempo medio devops / abertura task', `devops: ${{n2.devopsMedio !== null ? fmtH(n2.devopsMedio) : '-'}} · abertura task: ${{n2.validacaoMedio !== null ? fmtH(n2.validacaoMedio) : '-'}}`);
      }} else {{
        document.getElementById('kpiOneOnOneN2').innerHTML =
          kpiTileStatic('neutral', '-', 'Indicadores tecnicos (N2)', 'so disponivel para o mes corrente (o historico de status nao e mantido para meses anteriores)');
      }}
    }} else {{
      // Indicador N1 — tempo desde a abertura ate o repasse pro status 'Em atendimento - N2', nos
      // mesmos chamados tecnicos (Bug/Melhoria/Servicos). So' calculavel no mes corrente.
      const n1 = computeN1Metrics(tecnico, periodoKey);
      document.getElementById('kpiOneOnOneN2').style.display = '';
      if (n1) {{
        document.getElementById('kpiOneOnOneN2').innerHTML =
          kpiTileStatic('neutral', n1.total, 'Chamados tecnicos (Bug/Melhoria/Servicos)', 'atribuidos ao tecnico no mes corrente') +
          kpiTileStatic('neutral', n1.qtdAcionouN2, "Repassados p/ 'Em atendimento - N2'", `de ${{n1.total}} chamados tecnicos`) +
          kpiTileStatic('warn', n1.tempoAteAcionarN2Medio !== null ? fmtH(n1.tempoAteAcionarN2Medio) : '-', 'Tempo de repasse - N1', "tempo util (exclui Aguardando Cliente) da abertura ate 'Em atendimento - N2'");
      }} else {{
        document.getElementById('kpiOneOnOneN2').innerHTML =
          kpiTileStatic('neutral', '-', 'Indicadores tecnicos (N1)', 'so disponivel para o mes corrente (o historico de status nao e mantido para meses anteriores)');
      }}
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

// ============================================================
// Aba Reuniao Mensal — protegida por senha. Chamados fechados por categoria/mes + SLA mensal.
// Cobre somente os ultimos 3 meses (statusHistories/serie mensal completa nao esta disponivel
// para meses mais antigos que isso no pipeline atual).
// ============================================================
const REUNIAO_MENSAL_PASSWORD = '3300';
function checkReuniaoMensalPassword() {{
  const val = document.getElementById('reuniaoMensalPassInput').value;
  if (val === REUNIAO_MENSAL_PASSWORD) {{
    document.getElementById('reuniaoMensalGate').style.display = 'none';
    document.getElementById('reuniaoMensalContent').style.display = 'block';
    sessionStorage.setItem('reuniaoMensalUnlocked', '1');
    initReuniaoMensal();
  }} else {{
    document.getElementById('reuniaoMensalError').style.display = 'block';
  }}
}}
document.getElementById('reuniaoMensalPassInput').addEventListener('keydown', e => {{ if (e.key === 'Enter') checkReuniaoMensalPassword(); }});
if (sessionStorage.getItem('reuniaoMensalUnlocked') === '1') {{
  document.getElementById('reuniaoMensalGate').style.display = 'none';
  document.getElementById('reuniaoMensalContent').style.display = 'block';
}}

const REUNIAO_MENSAL_CATEGORIAS = ['Bloqueio Sistema', 'Bug', 'Dúvida', 'Melhoria', 'Erro Operacional', 'Terceiros', 'Serviços', 'GNRE Pagamento'];
// Meta de duvidas: baseline historico de 61% (media de ~7 meses, 3535 chamados de duvida) — a meta
// e reduzir 20% desse percentual (nao 20 pontos percentuais, e sim 20% de reducao relativa ao baseline).
const META_DUVIDAS_BASELINE_PCT = 61;
const META_DUVIDAS_REDUCAO_ALVO_PCT = 20;
function reducaoDuvidas(pctAtual) {{
  return Math.round((META_DUVIDAS_BASELINE_PCT - pctAtual) / META_DUVIDAS_BASELINE_PCT * 100);
}}
let reuniaoMensalInited = false;
function initReuniaoMensal() {{
  if (reuniaoMensalInited) return;
  reuniaoMensalInited = true;

  const mesesOrdenados = Object.keys(MONTH_LABELS).sort((a,b) => Number(b) - Number(a)); // offset 2,1,0 (mais antigo primeiro)

  const linhas = mesesOrdenados.map(k => {{
    const items = RESOLVED_MONTHS[k] || [];
    const porCategoria = {{}};
    let outros = 0;
    items.forEach(r => {{
      const cat = r.category || 'Sem categoria';
      if (REUNIAO_MENSAL_CATEGORIAS.indexOf(cat) !== -1) {{
        porCategoria[cat] = (porCategoria[cat] || 0) + 1;
      }} else {{
        outros++;
      }}
    }});
    const total = items.length;
    const duvidas = porCategoria['Dúvida'] || 0;
    const pctDuvidas = total ? Math.round(duvidas / total * 100) : 0;
    const stats = statsForMonth(items);
    return {{ mesKey: k, label: MONTH_LABELS[k], porCategoria, outros, total, pctDuvidas, reducaoDuvidas: reducaoDuvidas(pctDuvidas), pctSla: stats.pctSla }};
  }});

  // KPIs de SLA mensal (um por mes, mais recente primeiro)
  const linhasParaKpi = linhas.slice().reverse();
  document.getElementById('kpiReuniaoMensalSla').innerHTML = linhasParaKpi.map(l =>
    kpiTileStatic(l.pctSla !== null && l.pctSla < 70 ? 'danger' : 'ok', `${{l.pctSla}}%`, `SLA no prazo — ${{l.label}}`, `${{l.total}} chamados fechados no mes`)
  ).join('');

  // Tabela de categorias por mes (mesmo layout da planilha de reuniao)
  const totalGeral = {{}};
  REUNIAO_MENSAL_CATEGORIAS.forEach(c => totalGeral[c] = 0);
  let totalGeralOutros = 0, totalGeralFechados = 0;
  const todosItensPeriodo = [];
  linhas.forEach(l => {{
    REUNIAO_MENSAL_CATEGORIAS.forEach(c => totalGeral[c] += (l.porCategoria[c] || 0));
    totalGeralOutros += l.outros;
    totalGeralFechados += l.total;
    todosItensPeriodo.push(...(RESOLVED_MONTHS[l.mesKey] || []));
  }});
  const statsGeral = statsForMonth(todosItensPeriodo);

  // Meta de duvidas: baseline 61% (media historica de ~7 meses/3535 chamados), meta = reduzir 20% desse valor
  const pctDuvidasTotalKpi = totalGeralFechados ? Math.round((totalGeral['Dúvida']||0)/totalGeralFechados*100) : 0;
  const reducaoTotalKpi = reducaoDuvidas(pctDuvidasTotalKpi);
  const metaBatida = reducaoTotalKpi >= META_DUVIDAS_REDUCAO_ALVO_PCT;
  document.getElementById('kpiReuniaoMensalMeta').innerHTML =
    kpiTileStatic(metaBatida ? 'ok' : (reducaoTotalKpi >= 0 ? 'warn' : 'danger'),
      `${{reducaoTotalKpi > 0 ? '-' : (reducaoTotalKpi < 0 ? '+' : '')}}${{Math.abs(reducaoTotalKpi)}}%`,
      'Meta de duvidas: reduzir 20% (baseline 61%)',
      `% duvidas atual no periodo: ${{pctDuvidasTotalKpi}}% · baseline: ${{META_DUVIDAS_BASELINE_PCT}}% · ${{metaBatida ? 'meta batida' : 'meta nao batida'}}`);

  const headerCols = REUNIAO_MENSAL_CATEGORIAS.map(c => `<th>${{esc(c)}}</th>`).join('') + '<th>Outros</th><th>Total Fechados</th><th>% Duvidas</th><th>Reducao vs meta (baseline 61%)</th><th>% SLA no prazo</th>';
  const bodyRows = linhas.map(l => {{
    const cols = REUNIAO_MENSAL_CATEGORIAS.map(c => `<td style="text-align:center">${{l.porCategoria[c] || 0}}</td>`).join('');
    const corReducao = l.reducaoDuvidas >= META_DUVIDAS_REDUCAO_ALVO_PCT ? 'var(--ok)' : (l.reducaoDuvidas >= 0 ? 'var(--warn)' : 'var(--danger)');
    return `<tr>
      <td style="font-weight:600">${{esc(l.label)}}</td>
      ${{cols}}
      <td style="text-align:center">${{l.outros}}</td>
      <td style="text-align:center; font-weight:700">${{l.total}}</td>
      <td style="text-align:center">${{l.pctDuvidas}}%</td>
      <td style="text-align:center; font-weight:700; color:${{corReducao}}">${{l.reducaoDuvidas > 0 ? '-' : (l.reducaoDuvidas < 0 ? '+' : '')}}${{Math.abs(l.reducaoDuvidas)}}%</td>
      <td style="text-align:center">${{l.pctSla !== null ? l.pctSla+'%' : '-'}}</td>
    </tr>`;
  }}).join('');
  const pctDuvidasTotal = pctDuvidasTotalKpi;
  const reducaoTotal = reducaoTotalKpi;
  const corReducaoTotal = reducaoTotal >= META_DUVIDAS_REDUCAO_ALVO_PCT ? 'var(--ok)' : (reducaoTotal >= 0 ? 'var(--warn)' : 'var(--danger)');
  const totalRow = `<tr style="border-top:2px solid var(--panel-border); font-weight:700;">
    <td>Total</td>
    ${{REUNIAO_MENSAL_CATEGORIAS.map(c => `<td style="text-align:center">${{totalGeral[c]}}</td>`).join('')}}
    <td style="text-align:center">${{totalGeralOutros}}</td>
    <td style="text-align:center">${{totalGeralFechados}}</td>
    <td style="text-align:center">${{pctDuvidasTotal}}%</td>
    <td style="text-align:center; color:${{corReducaoTotal}}">${{reducaoTotal > 0 ? '-' : (reducaoTotal < 0 ? '+' : '')}}${{Math.abs(reducaoTotal)}}%</td>
    <td style="text-align:center">${{statsGeral.pctSla !== null ? statsGeral.pctSla+'%' : '-'}}</td>
  </tr>`;

  document.getElementById('tabelaReuniaoMensal').innerHTML = `
    <table><thead><tr><th>Mes</th>${{headerCols}}</tr></thead>
      <tbody>${{bodyRows}}${{totalRow}}</tbody></table>
  `;
}}

// ============================================================
// Aba Fluxograma — fluxo de atendimento (Entrada -> Triagem -> N1 -> N2 -> Task/Dev -> Validacao
// cliente -> Encerramento), com filtro por mes+cliente pros dados gerais, busca de chamado por numero
// (mostra em qual etapa esta, proximos passos clicaveis e linha do tempo por status), e paineis de
// Entrada (por canal) e Desenvolvimento (por categoria) — tudo interativo (clique abre a lista).
// ============================================================
const FLOW_MAIN_STAGES = [
  {{ key: 'entrada', title: 'Entrada', sub: 'E-mail, WhatsApp/chat ou portal Movidesk' }},
  {{ key: 'triagem', title: 'Triagem inicial', sub: 'Vendas / Implantacao / Suporte' }},
  {{ key: 'n1', title: 'N1', sub: 'Analise inicial — apoio do N3 (Multiplicador) quando necessario' }},
  {{ key: 'n2', title: 'N2', sub: "Repasse tecnico ('Em atendimento - N2')" }},
  {{ key: 'task_dev', title: 'Task / Desenvolvimento', sub: "Fila de dev ('Aguardando Desenvolvimento')" }},
  {{ key: 'validacao_cliente', title: 'Validacao do cliente', sub: "Chamado 'Resolvido', aguardando confirmacao" }},
  {{ key: 'encerrado', title: 'Encerramento', sub: 'Manual (cliente confirma) ou automatico em 3 dias' }},
];
const FLOW_SECONDARY_STAGE = {{ key: 'pendente_usuario', title: 'Pendente Usuario', sub: "'Aguardando Cliente' — volta ao N1 quando o cliente responde, ou encerra em 3 dias sem resposta" }};
// Cor de cada etapa — usada tanto nas etiquetas quanto na barra de linha do tempo (gantt) do chamado.
const STAGE_COLORS = {{
  entrada: '#82829C', triagem: '#F87171', n1: '#ED6DA2', n2: '#F59E0B',
  task_dev: '#8B5CF6', pendente_usuario: '#38BDF8', validacao_cliente: '#34D399', encerrado: '#6B7280',
}};
// Mapeamento aproximado do codigo "origin" do Movidesk pra um rotulo legivel — o unico 100% confirmado
// no codigo e o 24 (Chat, ja usado nas metricas de chat existentes); os demais seguem a documentacao
// publica do Movidesk. Editar aqui caso algum codigo apareca com o rotulo errado.
const ORIGIN_LABELS = {{ 1: 'E-mail', 2: 'Portal', 3: 'Telefone', 9: 'WhatsApp', 10: 'Rede social', 24: 'Chat' }};
function originLabel(origin) {{
  if (origin === null || origin === undefined) return 'Nao informado';
  return ORIGIN_LABELS[origin] || `Outro (codigo ${{origin}})`;
}}

// Mapeia o status atual do Movidesk pra uma etapa do fluxo (aproximado — o Movidesk nao tem um campo
// proprio de "etapa do fluxo", so status; alguns status de espera especificos, tipo Aguardando
// Terceiros/Sefaz-ANTT/Squad GNRE, ficam agrupados dentro da etapa tecnica corrente por simplicidade).
function stageOfStatus(status) {{
  if (status === 'Novo') return 'triagem';
  if (status === 'Em atendimento') return 'n1';
  if (status === 'Aguardando Cliente') return 'pendente_usuario';
  if (status === N2_HANDOFF_STATUS) return 'n2';
  if (isDevQueueStatus(status)) return 'task_dev';
  if (status === 'Resolvido') return 'validacao_cliente';
  if (status === 'Fechado' || status === 'Cancelado') return 'encerrado';
  if (status === 'Em atendimento - CS') return 'triagem';
  return 'n1';
}}

// Proximas opcoes possiveis a partir de cada ETAPA (nao status) — usadas tanto no texto quanto nos
// pills clicaveis (cada pill abre a lista de chamados que estao hoje na etapa de destino).
const FLOW_NEXT_OPTIONS = {{
  triagem: [['n1', 'N1 (Suporte)']],
  n1: [['n2', 'N2'], ['pendente_usuario', 'Pendente Usuario'], ['validacao_cliente', 'Resolver (Validacao cliente)']],
  pendente_usuario: [['n1', 'Volta ao N1'], ['encerrado', 'Encerramento automatico (3 dias)']],
  n2: [['n1', 'Resolve e devolve ao N1'], ['task_dev', 'Abre task (Desenvolvimento)']],
  task_dev: [['n2', 'Volta ao N2 (validacao/impedimento)']],
  validacao_cliente: [['encerrado', 'Encerramento']],
  encerrado: [],
}};

function proximosPassosTexto(status) {{
  if (status === 'Novo') {{
    return "Chamado na fila, aguardando o N1 iniciar a analise (ou o N3 apoiar, se necessario).";
  }}
  if (status === 'Em atendimento') {{
    return "O N1 pode: <b>resolver diretamente</b> (o chamado segue para validacao do cliente), <b>colocar Aguardando Cliente</b> (Pendente Usuario, quando falta informacao do cliente), ou <b>repassar para 'Em atendimento - N2'</b> quando o caso exige um nivel tecnico mais aprofundado. O N3 (Multiplicador) pode apoiar o N1 em qualquer uma dessas etapas.";
  }}
  if (status === 'Aguardando Cliente') {{
    return "Se o cliente responder, o chamado volta para o N1 (status 'Em atendimento'). Se nao houver resposta, o chamado e <b>encerrado automaticamente em 3 dias corridos</b>.";
  }}
  if (status === N2_HANDOFF_STATUS) {{
    return "O N2 pode: <b>resolver diretamente</b>, informar o cliente e devolver o chamado ao N1 (fila 'Em atendimento'), ou <b>abrir task para o desenvolvimento</b> ('Aguardando Desenvolvimento') — nesse caso o N2 assume tanto o chamado quanto a task.";
  }}
  if (isDevQueueStatus(status)) {{
    return "A task pode retornar ao N2 de 3 formas: <b>Em validacao</b> (o N2 testa a entrega e pede ao cliente para validar), <b>Em impedimento</b> (o N2 trata o motivo antes de prosseguir), ou <b>de volta para 'A Fazer'</b> se a task nao tiver a analise de negocio e a resolucao do problema claras (o desenvolvedor responsavel e mencionado no comentario do Azure DevOps para reforco).";
  }}
  if (status === 'Resolvido') {{
    return "Chamado aguardando validacao do cliente: se o cliente confirmar a solucao, o chamado e <b>encerrado manualmente</b>; se nao houver resposta, e <b>encerrado automaticamente apos 3 dias corridos</b>.";
  }}
  if (status === 'Fechado' || status === 'Cancelado') {{
    return "Fluxo encerrado — nao ha proximos passos.";
  }}
  if (isGovWaitStatus(status)) {{
    return "Aguardando retorno de orgao governamental (SEFAZ/ANTT/Portal Nacional da GNRE) — por contrato, o SLA fica pausado enquanto o chamado estiver neste status. Ao retomar, o chamado volta pro atendimento (N1/N2).";
  }}
  if (status === 'Em atendimento - CS') {{
    return "Chamado em atendimento pelo time de Implantacao/CS (fora do fluxo de Suporte).";
  }}
  return `Aguardando retorno de terceiro ou etapa intermediaria ('${{esc(status || '-')}}') antes de prosseguir no fluxo de atendimento tecnico.`;
}}

// Tempo medio (por visita ao status) em um status especifico — direto do historico de status.
function avgTimeInStatus(items, status) {{
  const durs = [];
  items.forEach(r => (r.statusHistories || []).forEach(h => {{
    if (h.status === status && h.permanencyTimeFullTime) durs.push(h.permanencyTimeFullTime / 3600);
  }}));
  return avg(durs);
}}

// --- Filtros de mes/cliente para os dados GERAIS da aba (times/contagens agregadas) ---
const selMesFluxo = document.getElementById('selMesFluxo');
const selClienteFluxo = document.getElementById('selClienteFluxo');
populateSelect(selMesFluxo, Object.keys(MONTH_LABELS).map(k => [k, MONTH_LABELS[k]]));

function fluxoResolvedScope() {{
  const items = RESOLVED_MONTHS[selMesFluxo.value] || [];
  return selClienteFluxo.value ? items.filter(r => r.clientOrg === selClienteFluxo.value) : items;
}}
function fluxoOpenScope() {{
  return selClienteFluxo.value ? TICKETS.filter(t => t.clientOrg === selClienteFluxo.value) : TICKETS;
}}
function refreshClienteFluxoOptions() {{
  const clientes = new Set([
    ...(RESOLVED_MONTHS[selMesFluxo.value] || []).map(r => r.clientOrg),
    ...TICKETS.map(t => t.clientOrg),
  ].filter(Boolean));
  const clientesList = Array.from(clientes).sort((a,b) => a.localeCompare(b));
  const prev = selClienteFluxo.value;
  populateSelect(selClienteFluxo, [['', 'Todos os clientes'], ...clientesList.map(c => [c, c])]);
  if (clientesList.indexOf(prev) !== -1) selClienteFluxo.value = prev;
}}

// Contagem AO VIVO (respeitando o filtro de cliente) de chamados abertos em cada etapa — clicar abre a lista.
function ticketsNaEtapa(key) {{
  return fluxoOpenScope().filter(t => stageOfStatus(t.status) === key);
}}
function abrirModalEtapaFluxo(key, titulo) {{
  renderModal(`${{titulo}} — chamados abertos agora`, ticketsNaEtapa(key), 'open');
}}
const FLOW_CLICKAVEL = ['n1', 'n2', 'task_dev', 'pendente_usuario', 'validacao_cliente', 'encerrado', 'triagem'];

function renderFlowDiagram(currentKey, stageTimes) {{
  const boxHtml = (s) => {{
    const clickavel = FLOW_CLICKAVEL.indexOf(s.key) !== -1;
    const tempo = stageTimes[s.key];
    const qtd = clickavel ? ticketsNaEtapa(s.key).length : null;
    const attrs = clickavel ? `tabindex="0" role="button" onclick="abrirModalEtapaFluxo(${{jsStr(s.key)}}, ${{jsStr(s.title)}})" onkeydown="if(event.key==='Enter')abrirModalEtapaFluxo(${{jsStr(s.key)}}, ${{jsStr(s.title)}})"` : '';
    return `<div class="flow-box ${{s.key === currentKey ? 'flow-current' : ''}} ${{clickavel ? 'flow-clickable' : ''}}" id="flowbox-${{s.key}}" ${{attrs}} style="border-top: 3px solid ${{STAGE_COLORS[s.key]}};">
      <div class="flow-title">${{esc(s.title)}}</div>
      <div class="flow-sub">${{esc(s.sub)}}</div>
      ${{tempo !== undefined && tempo !== null ? `<div class="flow-time">⏱ media: ${{fmtH(tempo)}}</div>` : ''}}
      ${{qtd !== null ? `<div class="flow-count">${{qtd}} agora</div>` : ''}}
    </div>`;
  }};
  const mainRow = FLOW_MAIN_STAGES.map((s,i) => boxHtml(s) + (i < FLOW_MAIN_STAGES.length - 1 ? '<div class="flow-arrow">→</div>' : '')).join('');
  document.getElementById('flowDiagram').innerHTML = `
    <div class="flow-row">${{mainRow}}</div>
    <div class="flow-row" style="max-width:280px;">${{boxHtml(FLOW_SECONDARY_STAGE)}}</div>
  `;
}}

// Barras clicaveis genericas (reaproveita o estilo .bar-row ja usado em outras abas).
function fluxoBarsHtml(grupos, onclickFor) {{
  if (!grupos.length) return '<div class="empty-msg">Sem dados no periodo/cliente selecionado</div>';
  const top = Math.max(...grupos.map(([,items]) => items.length), 1);
  return grupos.map(([label, items]) => `
    <div class="bar-row" onclick="${{onclickFor(label, items)}}">
      <div class="bar-label" style="width:auto; flex:1;">${{esc(label)}}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${{(items.length/top*100).toFixed(0)}}%"></div></div>
      <div class="bar-value">${{items.length}}</div>
    </div>`).join('');
}}

// ---- Renderiza os dados GERAIS da aba (nada selecionado) — respeitando mes+cliente ----
function renderFluxoAgregado() {{
  const resolvedScope = fluxoResolvedScope();
  const openScope = fluxoOpenScope();
  const comHistorico = resolvedScope.filter(r => (r.statusHistories || []).length);
  const ciclos = comHistorico.map(calcularCicloAtendimentoTecnico).filter(Boolean);
  const stageTimes = {{
    triagem: avgTimeInStatus(comHistorico, 'Novo'),
    n1: avg(ciclos.filter(c => c.tempoRepasseN1H !== null).map(c => c.tempoRepasseN1H)),
    n2: avg(ciclos.filter(c => c.tempoAberturaTaskH !== null).map(c => c.tempoAberturaTaskH)),
    task_dev: avg(ciclos.filter(c => c.devopsH !== null).map(c => c.devopsH)),
    pendente_usuario: avgTimeInStatus(comHistorico, 'Aguardando Cliente'),
    encerrado: avgTimeInStatus(comHistorico, 'Resolvido'),
  }};
  renderFlowDiagram(null, stageTimes);

  // Entrada por canal — AO VIVO (backlog atual), respeitando o filtro de cliente.
  const porOrigem = {{}};
  openScope.forEach(t => {{ const l = originLabel(t.origin); (porOrigem[l] = porOrigem[l] || []).push(t); }});
  const gruposOrigem = Object.entries(porOrigem).sort((a,b) => b[1].length - a[1].length);
  document.getElementById('fluxoEntradaSub').textContent = `${{openScope.length}} chamados abertos agora, por forma de abertura`;
  document.getElementById('fluxoEntradaBars').innerHTML = fluxoBarsHtml(gruposOrigem,
    (label) => `renderModal(${{jsStr(label + ' — chamados abertos agora')}}, TICKETS.filter(t=>originLabel(t.origin)===${{jsStr(label)}}${{selClienteFluxo.value ? ' && t.clientOrg===' + jsStr(selClienteFluxo.value) : ''}}), 'open')`);

  // Em desenvolvimento por categoria — AO VIVO, respeitando o filtro de cliente.
  const emDev = ticketsNaEtapa('task_dev');
  const porCategoria = {{}};
  emDev.forEach(t => {{ const c = (t.category || 'Sem categoria').toUpperCase(); (porCategoria[c] = porCategoria[c] || []).push(t); }});
  const gruposCategoria = Object.entries(porCategoria).sort((a,b) => b[1].length - a[1].length);
  document.getElementById('fluxoDevBars').innerHTML = fluxoBarsHtml(gruposCategoria,
    (label) => `renderModal(${{jsStr(label + ' em desenvolvimento')}}, ticketsNaEtapa('task_dev').filter(t=>(t.category||'Sem categoria').toUpperCase()===${{jsStr(label)}}), 'open')`);

  // SLA de repasse N2 — tempo medio observado (repasse N1) por classificacao, no escopo selecionado.
  const slaLinhas = [
    {{ nome: 'Urgente', prazo: '15 minutos', obs: 'Atendimento imediato', filtro: r => r.urgency === 'Urgente' }},
    {{ nome: 'Bug alto', prazo: '1 hora', obs: 'Atendimento prioritario', filtro: r => r.category === 'Bug' && r.urgency === 'Alta' }},
    {{ nome: 'Bug medio', prazo: '8 horas', obs: 'Desde que fornecida solucao de contorno ao usuario', filtro: r => r.category === 'Bug' && r.urgency === 'Média' }},
  ];
  document.getElementById('fluxoSlaTbody').innerHTML = slaLinhas.map(l => {{
    const subset = ciclos.filter((c,i) => l.filtro(comHistorico[i]) && c.tempoRepasseN1H !== null);
    const media = avg(subset.map(c => c.tempoRepasseN1H));
    return `<tr><td>${{l.nome}}</td><td>${{l.prazo}}</td><td>${{media !== null ? fmtH(media) + ` (${{subset.length}})` : '-'}}</td><td>${{l.obs}}</td></tr>`;
  }}).join('');
}}

function findTicketByProtocol(protocol) {{
  protocol = String(protocol || '').trim();
  if (!protocol) return null;
  let t = TICKETS.find(x => String(x.protocol) === protocol);
  if (t) return t;
  for (const k of ['0', '1', '2']) {{
    t = (RESOLVED_MONTHS[k] || []).find(x => String(x.protocol) === protocol);
    if (t) return t;
  }}
  t = RESOLVED_TODAY.find(x => String(x.protocol) === protocol);
  if (t) return t;
  return null;
}}

// Barra colorida (gantt) com o tempo em cada etapa do historico de status do chamado.
function renderFluxoGantt(hist) {{
  if (!hist.length) {{ document.getElementById('fluxoGantt').innerHTML = ''; return; }}
  const now = new Date();
  const dursH = hist.map((h,i) => {{
    if (h.permanencyTimeFullTime) return h.permanencyTimeFullTime / 3600;
    if (i === hist.length - 1) return Math.max(0.1, (now - new Date(h.changedDate)) / 3600000);
    return 0.1;
  }});
  const total = dursH.reduce((s,v) => s+v, 0) || 1;
  const segs = hist.map((h,i) => {{
    const key = stageOfStatus(h.status);
    const pct = (dursH[i] / total * 100).toFixed(2);
    return `<div class="flow-gantt-seg" style="width:${{pct}}%; background:${{STAGE_COLORS[key] || '#82829C'}};" title="${{esc(h.status)}} — ${{fmtH(dursH[i])}}"></div>`;
  }}).join('');
  const legendKeys = Array.from(new Set(hist.map(h => stageOfStatus(h.status))));
  const legend = legendKeys.map(k => {{
    const def = [...FLOW_MAIN_STAGES, FLOW_SECONDARY_STAGE].find(s => s.key === k);
    return `<div class="flow-gantt-legend-item"><span class="flow-gantt-swatch" style="background:${{STAGE_COLORS[k]}};"></span>${{esc(def ? def.title : k)}}</div>`;
  }}).join('');
  document.getElementById('fluxoGantt').innerHTML = `<div class="flow-gantt">${{segs}}</div><div class="flow-gantt-legend">${{legend}}</div>`;
}}

function carregarChamadoFluxo(ticket) {{
  if (!ticket) return;
  document.getElementById('fluxoErro').style.display = 'none';
  document.getElementById('fluxoLimparBusca').style.display = '';
  const curStage = stageOfStatus(ticket.status);
  const stageTimesVazio = {{}};
  renderFlowDiagram(curStage, stageTimesVazio);
  const catTag = ['Bug','Melhoria','Serviços'].indexOf(ticket.category) !== -1 ? `<span class="flow-stage-tag">${{esc(ticket.category)}}</span>` : '';
  const hist = (ticket.statusHistories || []).slice().sort((a,b) => new Date(a.changedDate) - new Date(b.changedDate));
  const tempoNaEtapaAtualH = hist.length ? (new Date() - new Date(hist[hist.length-1].changedDate)) / 3600000 : null;
  document.getElementById('fluxoChamadoInfo').innerHTML =
    `Chamado <b>${{ticketLink(ticket.id, ticket.protocol)}}</b> — ${{esc(ticket.subject || '')}} · categoria: ${{esc(ticket.category || '-')}}${{catTag}} · status atual: <b>${{esc(ticket.status || '-')}}</b>${{tempoNaEtapaAtualH !== null ? ` (ha ${{fmtH(tempoNaEtapaAtualH)}} nesta etapa)` : ''}} · tecnico: ${{esc(ticket.ownerName || '-')}} · cliente: ${{esc(ticket.clientOrg || '-')}} · entrada: ${{esc(originLabel(ticket.origin))}}`;

  const opcoes = FLOW_NEXT_OPTIONS[curStage] || [];
  const pillsHtml = opcoes.length ? `<div class="flow-next-options">${{opcoes.map(([key, label]) => `<span class="flow-next-pill" onclick="abrirModalEtapaFluxo(${{jsStr(key)}}, ${{jsStr(label)}})">→ ${{esc(label)}}</span>`).join('')}}</div>` : '';
  document.getElementById('fluxoProximosPassos').innerHTML = `<div class="flow-next-steps">${{proximosPassosTexto(ticket.status)}}</div>${{pillsHtml}}`;

  if (hist.length) {{
    renderFluxoGantt(hist);
    document.getElementById('fluxoTimelineSub').textContent = 'Historico de status e tempo em cada etapa (tempo corrido)';
    document.getElementById('fluxoTimeline').innerHTML = hist.map((h,i) => {{
      const durH = (h.permanencyTimeFullTime || 0) / 3600;
      const isLast = i === hist.length - 1;
      return `<div class="flow-timeline-item ${{isLast ? 'is-last' : ''}}">
        <div class="flow-timeline-status">${{esc(h.status)}}</div>
        <div class="flow-timeline-dur">desde ${{new Date(h.changedDate).toLocaleString('pt-BR')}} · ${{durH > 0 ? fmtH(durH) : (isLast ? 'em andamento' : '-')}}</div>
      </div>`;
    }}).join('');
  }} else {{
    document.getElementById('fluxoGantt').innerHTML = '';
    document.getElementById('fluxoTimelineSub').textContent = 'Historico detalhado de status nao disponivel para este chamado (so e mantido para chamados abertos e resolvidos no mes corrente)';
    document.getElementById('fluxoTimeline').innerHTML = `<div class="flow-timeline-item is-last">
        <div class="flow-timeline-status">${{esc(ticket.status || '-')}}</div>
        <div class="flow-timeline-dur">criado em ${{ticket.createdDate ? new Date(ticket.createdDate).toLocaleString('pt-BR') : '-'}}${{ticket.resolvedIn ? (' · resolvido em ' + new Date(ticket.resolvedIn).toLocaleString('pt-BR')) : ''}}</div>
      </div>`;
  }}
}}

function limparBuscaFluxo() {{
  document.getElementById('fluxoBuscaProtocolo').value = '';
  document.getElementById('fluxoErro').style.display = 'none';
  document.getElementById('fluxoLimparBusca').style.display = 'none';
  document.getElementById('fluxoChamadoInfo').textContent = 'Cada etapa mostra o tempo medio do periodo/cliente selecionado e quantos chamados estao nela agora — clique numa etapa pra ver a lista, ou busque um chamado especifico pelo numero.';
  document.getElementById('fluxoProximosPassos').innerHTML = '<div class="empty-msg">Nenhum chamado selecionado — dados gerais acima</div>';
  document.getElementById('fluxoGantt').innerHTML = '';
  document.getElementById('fluxoTimelineSub').textContent = 'Busque um chamado para ver a linha do tempo por status';
  document.getElementById('fluxoTimeline').innerHTML = '';
  renderFluxoAgregado();
}}

function buscarChamadoFluxoPorProtocolo() {{
  const val = document.getElementById('fluxoBuscaProtocolo').value;
  const found = findTicketByProtocol(val);
  const erroEl = document.getElementById('fluxoErro');
  if (!found) {{
    erroEl.style.display = '';
    erroEl.textContent = `Chamado "${{val}}" nao encontrado (busca entre chamados abertos e resolvidos nos ultimos 3 meses).`;
    return;
  }}
  carregarChamadoFluxo(found);
}}
document.getElementById('fluxoBuscaProtocolo').addEventListener('keydown', (e) => {{ if (e.key === 'Enter') buscarChamadoFluxoPorProtocolo(); }});
selMesFluxo.addEventListener('change', () => {{ refreshClienteFluxoOptions(); renderFluxoAgregado(); }});
selClienteFluxo.addEventListener('change', renderFluxoAgregado);
refreshClienteFluxoOptions();
renderFluxoAgregado();

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
