# -*- coding: utf-8 -*-
"""Versao de HOMOLOGACAO do painel (v2).

O build_dashboard.py continua gerando o painel atual; com HOMOLOG=1 ele passa o HTML por aqui e grava em
dashboard_homolog.html (publicado em /homolog/). Nada neste arquivo e' usado na versao de producao.

O que muda na v2:
  - Tema claro no padrao visual EmiteAi (fundo cinza #EBEDEF, cards brancos com sombra, navy/rosa como acento).
  - Titulos e abas sem emojis (visual mais limpo, menos 'cara de gerado por IA').
  - Aba 'Gestao Semanal - Melhorias' ganha a visao 'Fluxo' (interativo e animado, com os numeros ao vivo).
"""
import re

from homolog_gestao import NAV_CSS, NAV_JS, BUGS_JS, reestruturar_navegacao
from homolog_v2 import V2_CSS, V2_JS, DARK_CSS, TEMA_JS, aplicar_tema
from homolog_v3 import V3_CSS, V3_JS, aplicar_v3
from homolog_v4 import V4_CSS

TEMA_CLARO_CSS = """
/* ===== HOMOLOGACAO v2: tema claro EmiteAi ===== */
:root {
  --navy: #24243E; --navy-lt: #595974;
  --bg: #EBEDEF; --panel: #FFFFFF; --panel-border: rgba(135,135,153,0.25); --surface2: #F7F8FA;
  --text: #1A1A2C; --text-dim: #595974; --text3: #878799;
  --pink-dim: rgba(237,109,162,0.12);
  --ok: #1E8E5A; --ok-dim: rgba(30,142,90,0.10); --ok-bord: rgba(30,142,90,0.30);
  --warn: #B7791F; --warn-solid: #E0A100; --warn-dim: rgba(224,161,0,0.12); --warn-bord: rgba(183,121,31,0.30);
  --danger: #D64545; --danger-dim: rgba(214,69,69,0.10); --danger-bord: rgba(214,69,69,0.30);
  --shadow: rgba(36,36,62,0.10) 0px 1px 4px 0px; --shadow2: rgba(36,36,62,0.18) 0px 6px 18px 0px;
}
.panel, .kpi, .emis-card { border: none !important; box-shadow: var(--shadow); }
.gm-col, .gm-card { background: #fff; }
.gm-col { background: var(--surface2); border: none; box-shadow: none; }
.gm-card { box-shadow: var(--shadow); border-top: none; border-right: none; border-bottom: none; }
.hml-badge { display: inline-block; vertical-align: middle; margin-left: 12px; padding: 2px 10px; border-radius: 6px;
  background: var(--pink); color: #fff; font-size: 11px; font-weight: 700; letter-spacing: .8px; }
.tab-btn.active { background: var(--navy); color: #fff; border-color: var(--navy); }

/* ===== Fluxo de melhorias (interativo) ===== */
.fl-wrap { display: flex; flex-direction: column; gap: 18px; }
.fl-lane { background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); padding: 14px 18px 18px; }
.fl-lane h3 { margin: 0 0 12px 0; font-size: 12px; font-weight: 600; letter-spacing: .8px; text-transform: uppercase; color: var(--text3); }
.fl-row { display: flex; align-items: stretch; gap: 0; overflow-x: auto; padding: 4px 2px 8px; }
.fl-node { position: relative; min-width: 168px; max-width: 200px; flex: 1 0 168px; background: var(--surface2); border-radius: 8px;
  padding: 12px 14px; cursor: pointer; border: 1.5px solid transparent; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  animation: flIn .45s ease both; }
.fl-node:hover, .fl-node:focus-visible { transform: translateY(-3px); box-shadow: var(--shadow2); border-color: var(--pink); outline: none; }
.fl-node .fl-t { font-size: 12.5px; font-weight: 600; color: var(--text); line-height: 1.25; min-height: 32px; }
.fl-node .fl-n { font-size: 30px; font-weight: 700; letter-spacing: -.5px; color: var(--navy); margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.fl-node .fl-s { font-size: 11px; color: var(--text3); line-height: 1.35; }
.fl-node .fl-bar { height: 4px; border-radius: 2px; background: var(--ok); margin-top: 8px; transition: background .2s; }
.fl-node.fl-warn .fl-bar { background: var(--warn-solid); }
.fl-node.fl-danger .fl-bar { background: var(--danger); }
.fl-node.fl-danger .fl-n { color: var(--danger); }
.fl-node.fl-ponto { background: var(--navy); }
.fl-node.fl-ponto .fl-t, .fl-node.fl-ponto .fl-n { color: #fff; }
.fl-node.fl-ponto .fl-s { color: #B8B8D0; }
.fl-node.fl-dec { background: var(--pink-dim); border-color: var(--pink); }
.fl-node.fl-fim { background: #E4E5EA; }
.fl-node.fl-pulse::after { content: ''; position: absolute; top: 8px; right: 8px; width: 9px; height: 9px; border-radius: 50%;
  background: var(--danger); animation: flPulse 1.6s ease-out infinite; }
.fl-arrow { flex: 0 0 38px; align-self: center; position: relative; height: 2px; margin: 0 2px;
  background: repeating-linear-gradient(90deg, var(--navy-lt) 0 6px, transparent 6px 11px); background-size: 22px 2px; animation: flFlow 1s linear infinite; }
.fl-arrow::after { content: ''; position: absolute; right: -2px; top: -4px; border-left: 7px solid var(--navy-lt); border-top: 5px solid transparent; border-bottom: 5px solid transparent; }
.fl-arrow span { position: absolute; top: -17px; left: 0; right: 0; text-align: center; font-size: 10px; font-weight: 600; color: var(--pink); white-space: nowrap; }
.fl-legenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: 11.5px; color: var(--text3); }
.fl-legenda i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
@keyframes flIn { from { opacity: 0; transform: translateY(8px); } }
@keyframes flFlow { to { background-position: 22px 0; } }
@keyframes flPulse { 0% { box-shadow: 0 0 0 0 rgba(214,69,69,.55); } 100% { box-shadow: 0 0 0 10px rgba(214,69,69,0); } }
@media (prefers-reduced-motion: reduce) { .fl-node { animation: none; opacity: 1; transform: none; } .fl-arrow, .fl-node.fl-pulse::after { animation: none; } }
"""

FLUXO_JS = r"""
// ===== HOMOLOGACAO v2: visao 'Fluxo' da aba Gestao Semanal - Melhorias =====
const _gmSetSubOriginal = setGmSub;
setGmSub = function(sub) {
  if (sub !== 'fluxo') { const f = document.getElementById('gmFluxo'); if (f) f.style.display = 'none'; _gmSetSubOriginal(sub); document.querySelectorAll('#gmSubToggle button').forEach(b => b.classList.toggle('active', b.dataset.sub === sub)); return; }
  gmSub = 'fluxo';
  document.querySelectorAll('#gmSubToggle button').forEach(b => b.classList.toggle('active', b.dataset.sub === 'fluxo'));
  document.getElementById('gmAcomp').style.display = 'none';
  document.getElementById('gmIndic').style.display = 'none';
  document.getElementById('gmFluxo').style.display = '';
  renderGmFluxo();
};
function gmContaAnima(el, alvo) {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = alvo; return; }
  const ini = performance.now(), dur = 700;
  (function passo(ts) { const p = Math.min(1, (ts - ini) / dur); el.textContent = Math.round(alvo * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(passo); })(ini);
}
function gmAbreLista(titulo, ids) {
  const set = new Set(ids);
  renderModal(titulo, TICKETS.filter(t => set.has(t.id)), 'update');
}
function renderGmFluxo() {
  const todas = gmMelhorias();
  todas.forEach(t => { t._gmE = gmEtapa(t); });
  const por = k => todas.filter(t => t._gmE === k);
  const po = por('refina').filter(t => gmTagTem(t, 'aprovado po'));
  const refinaSemPO = por('refina').filter(t => !gmTagTem(t, 'aprovado po'));
  const dev = todas.filter(t => t.status === GM_ST_DEV);
  const devSem = dev.filter(t => !t._sla);
  const aguardandoCliente = todas.filter(t => t.status === 'Aguardando Cliente');
  let delay = 0;
  const FL_CHAVES = {'Em atendimento N1': 'n1', 'Aguardando validação do N2': 'n2', 'Aguardando reunião de alinhamento': 'refina', 'Aprovado PO · aguardando data': 'po',
    'Aguardando estimativa técnica': 'tec', 'Aguardando orçamento': 'orc', 'Aguardando resposta do cliente': 'cliente'};
  const node = (titulo, itens, sub, extra) => {
    const chave = (extra || '').indexOf('fl-fimdev') !== -1 ? 'dev1' : (titulo === 'Aguardando Desenvolvimento' ? 'dev2' : (FL_CHAVES[titulo] || ''));
    const parado = itens.length ? gmMedia(itens.map(gmDiasParado)) : 0;
    const cls = (extra || '') + (itens.length && parado > 15 ? ' fl-danger' : itens.length && parado > 7 ? ' fl-warn' : '');
    const ids = itens.map(t => t.id).join(',');
    const pulso = itens.some(t => gmDiasParado(t) > 30) ? ' fl-pulse' : '';
    delay += 70;
    return `<div class="fl-node ${cls}${pulso}" data-k="${chave}" style="animation-delay:${delay}ms" tabindex="0" role="button"
        onclick="gmAbreLista(${jsStr(titulo)}, [${ids}])" onkeydown="if(event.key==='Enter')this.click()">
      <div class="fl-t">${titulo}</div><div class="fl-n" data-alvo="${itens.length}">0</div>
      <div class="fl-s">${sub}${itens.length ? ' · média parado ' + gmDias(parado) : ''}</div><div class="fl-bar"></div></div>`;
  };
  const fixo = (titulo, texto, extra) => { delay += 70; return `<div class="fl-node ${extra || ''}" style="animation-delay:${delay}ms; cursor:default;"><div class="fl-t">${titulo}</div><div class="fl-s" style="margin-top:6px;">${texto}</div></div>`; };
  const seta = (rot) => `<div class="fl-arrow">${rot ? '<span>' + rot + '</span>' : ''}</div>`;

  document.getElementById('gmFluxo').innerHTML = `<div class="fl-wrap">
    <div class="panel-sub">Clique em uma etapa para ver os chamados. A barra e a cor mostram há quanto tempo, em média, os chamados estão sem atualização (verde até 7 dias, amarelo até 15, vermelho acima). O ponto vermelho piscando indica chamado parado há mais de 30 dias.</div>
    <div class="fl-lane"><h3>Entrada e análise</h3><div class="fl-row">
      ${fixo('Cliente solicita melhoria', 'Chamado de categoria Melhoria, preenchido no padrão', 'fl-ponto')}${seta()}
      ${node('Em atendimento N1', por('n1'), 'Status Em atendimento')}${seta()}
      ${node('Aguardando validação do N2', por('n2'), 'Status Em atendimento - N2')}${seta('se for melhoria')}
      ${node('Aguardando reunião de alinhamento', refinaSemPO, 'Refinamento Suporte Melhoria · quarta 14:00')}${seta()}
      ${fixo('Produto decide', 'Gratuita (roadmap) ou cobrada (estimativa e orçamento)', 'fl-dec')}
    </div></div>
    <div class="fl-lane"><h3>Caminho gratuito — roadmap</h3><div class="fl-row">
      ${node('Aprovado PO · aguardando data', po, 'Tag Aprovado PO · task já associada')}${seta('data recebida')}
      ${node('Aguardando Desenvolvimento', dev, devSem.length + ' sem Previsão de solução', 'fl-fimdev')}
    </div></div>
    <div class="fl-lane"><h3>Caminho cobrado — estimativa e orçamento</h3><div class="fl-row">
      ${node('Aguardando estimativa técnica', por('tec'), 'Refinamento + tag Estimativa Técnica + previsão')}${seta()}
      ${node('Aguardando orçamento', por('orc'), 'Em atendimento - CS + tags Técnica e Comercial')}${seta('proposta enviada')}
      ${node('Aguardando resposta do cliente', aguardandoCliente, 'Status Aguardando Cliente')}${seta('aprovou')}
      ${node('Aguardando Desenvolvimento', dev, 'Previsão de solução preenchida', '')}
    </div></div>
    <div class="fl-legenda"><span><i style="background:var(--ok)"></i>até 7 dias parado</span><span><i style="background:var(--warn-solid)"></i>8 a 15 dias</span><span><i style="background:var(--danger)"></i>mais de 15 dias</span><span><i style="background:var(--navy)"></i>início do fluxo</span><span><i style="background:var(--pink)"></i>decisão</span></div>
  </div>`;
  document.querySelectorAll('#gmFluxo .fl-n').forEach(el => gmContaAnima(el, Number(el.dataset.alvo)));
  if (typeof hmlDestacaEtapa === 'function') hmlDestacaEtapa();
}
"""

_EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿][️‍]*\\s?')


def _sem_emoji_titulos(html):
    """Tira emojis so' de linhas de titulo/aba (nunca dos dados embutidos em JSON)."""
    out = []
    for ln in html.split('\n'):
        if len(ln) < 2000 and ('<h2' in ln or '<h3' in ln or 'tab-btn' in ln):
            ln = _EMOJI.sub('', ln)
        out.append(ln)
    return '\n'.join(out)


def aplicar_homologacao(html, badge=True):
    """badge=True: versao de homologacao (etiqueta e titulo proprios). badge=False: mesmo visual e abas, sem a etiqueta (producao)."""
    # 1) tema claro (depois de todo o CSS existente, pra sobrescrever)
    html = html.replace('</style>', TEMA_CLARO_CSS + NAV_CSS + V2_CSS + DARK_CSS + V3_CSS + V4_CSS + '</style>', 1)
    # 2) identificacao visual da versao
    if badge:
        html = html.replace('<h1>Painel Diario</h1>', '<h1>Painel Diario <span class="hml-badge">HOMOLOGAÇÃO v2</span></h1>', 1)
    if badge:
        html = re.sub(r'<title>[^<]*</title>', '<title>Painel Diario — Homologação v2</title>', html, count=1)
    # 3) visao Fluxo na aba Gestao Semanal - Melhorias
    html = html.replace('<button type="button" data-sub="indic" onclick="setGmSub(\'indic\')">Indicadores</button>',
                        '<button type="button" data-sub="indic" onclick="setGmSub(\'indic\')">Indicadores</button>\n'
                        '        <button type="button" data-sub="fluxo" onclick="setGmSub(\'fluxo\')">Fluxo</button>', 1)
    html = html.replace('<div id="gmIndic" style="display:none;"></div>',
                        '<div id="gmIndic" style="display:none;"></div>\n    <div id="gmFluxo" style="display:none;"></div>', 1)
    html = html.replace('renderGestaoMelhorias();\n\nfunction tick()', FLUXO_JS + NAV_JS + BUGS_JS + V2_JS + TEMA_JS + V3_JS + '\nrenderGestaoMelhorias();\n\nfunction tick()', 1)
    html = reestruturar_navegacao(html)
    html = aplicar_tema(html)
    html = aplicar_v3(html)
    # 4) sem emojis nos titulos
    html = _sem_emoji_titulos(html)
    # titulos dentro de templates JS (linhas longas) tambem perdem o emoji logo apos <h2>
    return re.sub(r'(<h2[^>]*>)[ ]*' + _EMOJI.pattern, r'', html)
