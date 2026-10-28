# -*- coding: utf-8 -*-
"""Homologacao v2.1: refinamento visual e graficos em SVG puro (sem biblioteca externa).

Usado so' pelo homolog_extras.aplicar_homologacao (versao /homolog/); o painel atual nao usa nada daqui.
"""

V2_CSS = """
/* ===== HOMOLOGACAO v2.1: refinamento visual (menos 'cartoes iguais', mais hierarquia) ===== */
.panel { padding: 20px 24px; }
.panel h2 { font-size: 15px; font-weight: 600; letter-spacing: -.1px; margin-bottom: 2px; }
.panel .panel-sub { font-size: 12px; line-height: 1.5; max-width: 880px; }
.kpi::before { display: none !important; }
.kpi { padding: 16px 20px; }
.kpi .value { font-size: 32px; font-weight: 600; letter-spacing: -1.2px; line-height: 1.05; }
.kpi .label { font-size: 11px; font-weight: 500; letter-spacing: .3px; text-transform: none; color: var(--text3); margin-top: 6px; }
.kpi.danger .value { color: var(--danger); } .kpi.warn .value { color: var(--warn); }
th { background: transparent !important; color: var(--text3); font-size: 10.5px; font-weight: 600; letter-spacing: .7px; border-bottom: 1.5px solid var(--panel-border); padding: 8px 10px; }
td { border-bottom: 1px solid rgba(135,135,153,.14); padding: 10px; }
tbody tr:hover td { background: var(--surface2); }
.gm-selo { font-weight: 600; font-size: 10.5px; padding: 1px 8px; }
.gm-card { border-radius: 8px; box-shadow: none; border: 1px solid var(--panel-border); border-left-width: 3px; }
.gm-col { background: transparent; border: 1px solid var(--panel-border); }
.gm-col.gm-key { border-color: var(--pink); background: rgba(237,109,162,.04); }
.gm-col h3 em { background: var(--navy); }
.gi-nav button::before { content: ''; display: inline-block; width: 16px; height: 16px; margin-right: 8px; vertical-align: -3px; background: currentColor;
  -webkit-mask: var(--ic) center / contain no-repeat; mask: var(--ic) center / contain no-repeat; }
.gi-nav button[data-sub=reuniao] { --ic: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='16' rx='2'/%3E%3Cpath d='M16 3v4M8 3v4M3 11h18'/%3E%3C/svg%3E"); }
.gi-nav button[data-sub=melhorias] { --ic: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z'/%3E%3C/svg%3E"); }
.gi-nav button[data-sub=bugs] { --ic: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M8 8a4 4 0 0 1 8 0v6a4 4 0 0 1-8 0zM4 13h4M16 13h4M5 7l3 2M19 7l-3 2M5 19l3-2M19 19l-3-2'/%3E%3C/svg%3E"); }
.hml-graf svg { width: 100%; height: auto; display: block; }
.hml-graf .eixo { font-size: 10px; fill: var(--text3); }
.hml-graf .val { font-size: 9.5px; fill: var(--text-dim); font-weight: 600; }
.hml-leg { display: flex; gap: 16px; font-size: 11.5px; color: var(--text3); margin: 4px 0 6px; }
.hml-leg i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.hml-graf rect.barra { transition: opacity .15s; } .hml-graf rect.barra:hover { opacity: .75; }
"""

V2_JS = r"""
// ===== HOMOLOGACAO v2.1: graficos em SVG puro nos Indicadores =====
function hmlBarras(meses, series, extra) {
  const W = 760, H = 230, pl = 32, pr = 6, pt = 12, pb = extra ? 42 : 30;
  const max = Math.max(1, ...series.flatMap(s => s.v));
  const ih = H - pt - pb, bw = (W - pl - pr) / meses.length, gw = bw * 0.72, sw = gw / series.length;
  let g = '';
  for (let i = 0; i <= 4; i++) {
    const y = pt + ih * (1 - i / 4);
    g += `<line x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}" stroke="rgba(135,135,153,.2)"/><text class="eixo" x="${pl - 6}" y="${y + 3}" text-anchor="end">${Math.round(max * i / 4)}</text>`;
  }
  meses.forEach((m, i) => {
    series.forEach((s, j) => {
      const v = s.v[i] || 0, h = ih * v / max, x = pl + i * bw + (bw - gw) / 2 + j * sw;
      g += `<rect class="barra" x="${x.toFixed(1)}" y="${(pt + ih - h).toFixed(1)}" width="${(sw - 2).toFixed(1)}" height="${h.toFixed(1)}" rx="2" style="fill:${s.cor}"><title>${s.nome} · ${m}: ${v}</title></rect>`;
      if (v > 0 && bw > 34) g += `<text class="val" x="${(x + (sw - 2) / 2).toFixed(1)}" y="${(pt + ih - h - 4).toFixed(1)}" text-anchor="middle">${v}</text>`;
    });
    g += `<text class="eixo" x="${(pl + i * bw + bw / 2).toFixed(1)}" y="${H - (extra ? 20 : 10)}" text-anchor="middle">${m}</text>`;
    if (extra) g += `<text class="eixo" x="${(pl + i * bw + bw / 2).toFixed(1)}" y="${H - 6}" text-anchor="middle" style="font-weight:600">${extra[i]}</text>`;
  });
  const leg = series.map(s => `<span><i style="background:${s.cor}"></i>${s.nome}</span>`).join('');
  return `<div class="hml-leg">${leg}</div><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg>`;
}
function hmlMesesAbrev(yms) { const N = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']; return yms.map(ym => N[Number(ym.slice(5)) - 1] + '/' + ym.slice(2, 4)); }
function hmlGraficoMensal(cat) {
  const abertas = {};
  TICKETS.filter(t => t.category === cat).forEach(t => { const ym = brasiliaDateStr(t._created).slice(0, 7); abertas[ym] = (abertas[ym] || 0) + 1; });
  const res = {}, prazo = {};
  Object.keys(MONTH_YM).forEach(k => {
    const its = (RESOLVED_MONTHS[k] || []).filter(r => r.category === cat), ym = MONTH_YM[k];
    res[ym] = its.length;
    const cs = its.filter(r => r.slaSolutionDate && r.resolvedIn);
    prazo[ym] = cs.length ? Math.round(cs.filter(r => parseDt(r.resolvedIn) <= parseDt(r.slaSolutionDate)).length / cs.length * 100) + '%' : '–';
  });
  const yms = Array.from(new Set(Object.keys(abertas).concat(Object.keys(res)))).sort().filter(ym => ym >= '2025-07').slice(-12);
  const series = [{nome: 'Resolvidas no mês', cor: 'var(--navy)', v: yms.map(y => res[y] || 0)}];
  if (cat === 'Melhoria') series.unshift({nome: 'Abertas (ainda em aberto) por mês de criação', cor: 'var(--pink)', v: yms.map(y => abertas[y] || 0)});
  return hmlBarras(hmlMesesAbrev(yms), series, cat === 'Bug' ? yms.map(y => prazo[y]) : null);
}
function hmlInsereGrafico(boxId, cat, titulo, sub) {
  const box = document.getElementById(boxId); if (!box) return;
  const antigo = box.querySelector('.hml-graf'); if (antigo) antigo.remove();
  const alvo = box.querySelector('.kpi-row'); if (!alvo) return;
  alvo.insertAdjacentHTML('afterend', `<div class="panel hml-graf" style="margin-top:18px;"><h2>${titulo}</h2><div class="panel-sub">${sub}</div>${hmlGraficoMensal(cat)}</div>`);
}
const _hmlRgm = renderGestaoMelhorias;
renderGestaoMelhorias = function() { _hmlRgm(); hmlInsereGrafico('gmIndic', 'Melhoria', 'Evolução mensal das melhorias', 'Barras rosa: melhorias criadas no mês e ainda em aberto. Barras navy: melhorias resolvidas no mês. Últimos 12 meses.'); };
const _hmlRgb = renderGestaoBugs;
renderGestaoBugs = function() { _hmlRgb(); hmlInsereGrafico('gbIndic', 'Bug', 'Bugs resolvidos por mês', 'Barras: bugs resolvidos no mês. Abaixo de cada mês, o % resolvido dentro do prazo de SLA (só bugs com SLA definido).'); };
"""


# ---------------------------------------------------------------- tema escuro / claro
DARK_CSS = """
/* ===== HOMOLOGACAO v2.1: opcao de tema escuro (paleta original do painel) ===== */
html[data-tema="dark"] {
  --navy: #EAEAF2; --navy-lt: #B8B8D0;
  --bg: #1B1B33; --panel: #242444; --panel-border: rgba(255,255,255,0.10); --surface2: #2D2D52;
  --text: #EAEAF2; --text-dim: #A5A5BD; --text3: #82829C;
  --pink-dim: rgba(237,109,162,0.14);
  --ok: #34D399; --ok-dim: rgba(16,185,129,0.15); --ok-bord: rgba(52,211,153,0.35);
  --warn: #FBBF24; --warn-solid: #F59E0B; --warn-dim: rgba(245,158,11,0.15); --warn-bord: rgba(251,191,36,0.35);
  --danger: #F87171; --danger-dim: rgba(239,68,68,0.15); --danger-bord: rgba(248,113,113,0.35);
  --shadow: rgba(0,0,0,0.35) 0px 2px 8px 0px; --shadow2: rgba(0,0,0,0.5) 0px 6px 18px 0px;
  color-scheme: dark;
}
html[data-tema="dark"] .tab-btn.active { background: var(--pink-dim); color: var(--pink); border-color: rgba(232,56,109,0.3); }
html[data-tema="dark"] .gm-card { background: var(--surface2); }
html[data-tema="dark"] .gm-col.gm-key { background: rgba(237,109,162,.07); }
html[data-tema="dark"] .gm-col h3 em { background: var(--pink); }
html[data-tema="dark"] .fl-node.fl-ponto { background: #3A3A66; }
html[data-tema="dark"] .fl-node.fl-fim { background: var(--surface2); }
html[data-tema="dark"] .gi-nav button.active { color: var(--text); }
.hml-tema { display: inline-flex; align-items: center; gap: 6px; margin-right: 14px; padding: 5px 12px; border-radius: 6px; cursor: pointer;
  background: transparent; border: 1.25px solid var(--panel-border); color: var(--text-dim); font: 600 12px inherit; font-family: inherit; }
.hml-tema:hover { color: var(--text); border-color: var(--text3); }
.hml-tema svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }
.hml-tema .i-sol { display: none; } html[data-tema="dark"] .hml-tema .i-sol { display: inline; } html[data-tema="dark"] .hml-tema .i-lua { display: none; }
"""

TEMA_BOTAO = (
    '<button type="button" class="hml-tema" id="hmlTema" onclick="hmlAlternaTema()" aria-label="Alternar tema claro e escuro">'
    '<svg class="i-lua" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
    '<svg class="i-sol" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
    '<span id="hmlTemaTxt">Tema escuro</span></button>\n      '
)

TEMA_JS = r"""
// ===== HOMOLOGACAO v2.1: alternancia de tema (lembra a escolha; sem escolha, segue o sistema) =====
function hmlAplicaTema(t) {
  document.documentElement.setAttribute('data-tema', t);
  const el = document.getElementById('hmlTemaTxt'); if (el) el.textContent = t === 'dark' ? 'Tema claro' : 'Tema escuro';
}
function hmlAlternaTema() {
  const novo = document.documentElement.getAttribute('data-tema') === 'dark' ? 'light' : 'dark';
  hmlAplicaTema(novo);
  try { localStorage.setItem('hmlTema', novo); } catch (e) {}
}
(function () {
  let t = null;
  try { t = localStorage.getItem('hmlTema'); } catch (e) {}
  if (t !== 'dark' && t !== 'light') t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
  hmlAplicaTema(t);
})();
"""


def aplicar_tema(html):
    html = html.replace('<div class="header-right">', '<div class="header-right">\n      ' + TEMA_BOTAO, 1)
    return html
