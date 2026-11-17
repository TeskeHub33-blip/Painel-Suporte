# -*- coding: utf-8 -*-
"""Layout no padrao do sistema EmiteAi (skill emiteai-prototype-builder): cabecalho branco de 64px com o logo oficial e
breadcrumb, menu lateral navy de 240px (barra rosa de 3px no item ativo, icones de traco 1.75), conteudo sobre fundo cinza.
So' CSS + pequenos ajustes de HTML: as abas continuam sendo as mesmas (showTab)."""
import json
import re

V18_CSS = """
/* ===== Layout EmiteAi: cabecalho + menu lateral ===== */
:root { --sb-bg: #24243E; --sb-txt: rgba(255,255,255,.82); --sb-muted: rgba(255,255,255,.45); }
html[data-tema="dark"] { --sb-bg: #15152B; }
.dashboard-root { padding: 90px 26px 26px 266px; }
.dashboard-root > .header { position: fixed; top: 0; left: 0; right: 0; height: 64px; box-sizing: border-box; margin: 0; padding: 0 26px; border-radius: 0; z-index: 30; box-shadow: var(--shadow); }
.header .logo-img, .header .subtitle, .header h1 { display: none; }
.header-left { gap: 14px; }
.header .logo-svg { height: 34px; width: auto; flex: none; display: block; }
.header .marca { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; color: var(--text); }
.header .hdr-sep { width: 1px; height: 24px; background: var(--panel-border); }
.header .hdr-crumb { font-size: 13px; color: var(--text3); display: flex; align-items: center; gap: 8px; }
.header .hdr-crumb i { font-style: normal; color: var(--text3); }
.header .hdr-crumb b { color: var(--pink); font-weight: 600; }
.header-right { display: flex; align-items: center; gap: 16px; text-align: right; font-size: 12px; line-height: 1.3; }
.header-right .clock { font-size: 18px; }

.tabs { position: fixed; top: 64px; left: 0; bottom: 0; width: 240px; box-sizing: border-box; margin: 0; padding: 14px 12px 20px 12px; background: var(--sb-bg); display: flex; flex-direction: column; gap: 2px; overflow-y: auto; z-index: 20; transition: width .22s cubic-bezier(0.4,0,0.2,1); }
.tabs .tab-btn { display: flex; align-items: center; gap: 12px; width: 100%; box-sizing: border-box; text-align: left; background: transparent; border: 0; box-shadow: none; color: var(--sb-txt); font-size: 14px; font-weight: 400; padding: 10px 12px; border-radius: 8px; position: relative; transition: background .15s, color .15s; }
.tabs .tab-btn:hover { background: rgba(255,255,255,.07); color: #fff; border: 0; }
.tabs .tab-btn.active { background: rgba(255,255,255,.11) !important; color: #fff !important; font-weight: 600; border: 0 !important; box-shadow: none; }
.tabs .tab-btn.active::before { content: ''; position: absolute; left: -12px; top: 8px; bottom: 8px; width: 3px; background: var(--pink); border-radius: 0 3px 3px 0; }
.tabs .tab-btn svg { width: 18px; height: 18px; flex: none; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }
.tabs .tab-btn.active svg { stroke: var(--pink); }
.tabs .sb-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--sb-muted); padding: 16px 12px 6px 12px; }
.tabs .sb-label:first-child { padding-top: 4px; }

.header .hdr-menu { width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; background: transparent; border: 0; border-radius: 8px; cursor: pointer; color: var(--text-dim); padding: 0; }
.header .hdr-menu:hover { background: var(--surface2); color: var(--text); }
.header .hdr-menu svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; }
.dashboard-root { transition: padding-left .22s cubic-bezier(0.4,0,0.2,1); }
html.sb-min .dashboard-root { padding-left: 91px; }
html.sb-min .tabs { width: 65px; padding-left: 10px; padding-right: 10px; }
html.sb-min .tabs .tab-btn { font-size: 0; gap: 0; justify-content: center; padding: 11px 0; }
html.sb-min .tabs .tab-btn.active::before { left: -10px; }
html.sb-min .tabs .sb-label { height: 1px; padding: 0; margin: 8px 6px; overflow: hidden; background: rgba(255,255,255,.12); font-size: 0; }
html.sb-min .tabs .sb-label:first-child { display: none; }

@media (max-width: 1000px) {
  html.sb-min .dashboard-root { padding-left: 16px; }
  html.sb-min .tabs { display: none; }
  .dashboard-root { padding: 90px 16px 20px 16px; }
  .tabs { position: static; width: auto; flex-direction: row; flex-wrap: wrap; border-radius: 8px; margin-bottom: 14px; padding: 8px; }
  .tabs .tab-btn { width: auto; }
  .tabs .tab-btn.active::before { display: none; }
  .tabs .sb-label { display: none; }
  .header .hdr-crumb, .header-right > div:last-child { display: none; }
}
"""

ICONES = {
    'tabBtnLive': '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    'tabBtnHist': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    'tabBtnClientes': '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'tabBtnOneOnOne': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'tabBtnGamificacao': '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    'tabBtnReuniaoMensal': '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
    'tabBtnGestaoMelhorias': '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    'tabBtnFluxo': '<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    'tabBtnConfig': '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
}

V18_JS = r"""
// ===== Layout EmiteAi: icones do menu, secoes e breadcrumb =====
const V18_ICONES = __ICONES__;
function v18Menu() {
  const tabs = document.querySelector('.tabs'); if (!tabs || tabs.dataset.v18) return; tabs.dataset.v18 = '1';
  Object.keys(V18_ICONES).forEach(id => {
    const b = document.getElementById(id); if (!b || b.querySelector('svg')) return;
    b.insertAdjacentHTML('afterbegin', '<svg viewBox="0 0 24 24" aria-hidden="true">' + V18_ICONES[id] + '</svg>');
  });
  const secao = (idAntes, nome) => { const b = document.getElementById(idAntes); if (b) b.insertAdjacentHTML('beforebegin', '<div class="sb-label">' + nome + '</div>'); };
  secao('tabBtnLive', 'Operação'); secao('tabBtnOneOnOne', 'Liderança'); secao('tabBtnFluxo', 'Análise');
  if (typeof CFG_VERCEL !== 'undefined' && CFG_VERCEL) secao('tabBtnConfig', 'Sistema');
}
function v18AlternaMenu() {
  const min = document.documentElement.classList.toggle('sb-min');
  try { localStorage.setItem('hmlMenuMin', min ? '1' : '0'); } catch (e) {}
  const b = document.getElementById('hdrMenu'); if (b) b.setAttribute('aria-expanded', min ? 'false' : 'true');
}
function v18Crumb() {
  const a = document.querySelector('.tabs .tab-btn.active'), el = document.getElementById('hdrPag'); if (!a || !el) return;
  el.textContent = (a.textContent || '').trim();
}
{
  const _s3 = showTab;
  showTab = function(name, skip) { _s3(name, skip); v18Crumb(); };
  v18Menu(); v18Crumb();
  document.querySelectorAll('.tabs .tab-btn').forEach(b => { if (!b.title) b.title = (b.textContent || '').trim(); });   // dica ao passar o mouse com o menu recolhido
  try { if (localStorage.getItem('hmlMenuMin') === '1') document.documentElement.classList.add('sb-min'); } catch (e) {}
}
"""

V18_JS = V18_JS.replace('__ICONES__', json.dumps(ICONES))

LOGO = ('<svg class="logo-svg" viewBox="14.0 16.7 131.4 148.9" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EmiteAí">'
        '<path fill="#E8386D" d="M144.393,59.807 L83.485,93.792 L83.500,164.591 L144.393,128.419 L144.393,124.814 L105.392,135.177 L105.353,131.710 L144.393,108.689 Z"/>'
        '<path fill="#E8386D" d="M19.156,52.065 L79.504,86.997 L140.221,51.836 L140.184,51.810 L78.530,17.682 L75.411,19.489 L103.921,48.053 L100.940,49.825 L61.457,27.569 Z"/>'
        '<path fill="#E8386D" d="M75.447,93.760 L14.983,59.807 L14.983,115.958 L15.025,129.289 L75.447,164.591 L75.447,158.767 L36.445,124.821 L36.407,121.354 L75.447,142.642 Z"/></svg>')


def aplicar_v18(html):
    m = re.search(r'<div class="header-left">(.*?)</div>\s*</div>\s*<div class="header-right">', html, re.S)
    if not m:
        return html
    badge = re.search(r'<span class="hml-badge">[^<]*</span>', m.group(1))
    novo = (f'<div class="header-left"><button type="button" class="hdr-menu" id="hdrMenu" onclick="v18AlternaMenu()" aria-label="Mostrar ou esconder o menu lateral" aria-expanded="true" title="Mostrar ou esconder o menu"><svg viewBox="0 0 24 24" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>{LOGO}<span class="marca">emiteaí</span>{badge.group(0) if badge else ""}'
            '<span class="hdr-sep"></span><nav class="hdr-crumb" aria-label="Local">Painel Diário<i>/</i><b id="hdrPag">Ao Vivo</b></nav>\n    </div>\n    <div class="header-right">')
    return html[:m.start()] + novo + html[m.end():]
