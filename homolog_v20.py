# -*- coding: utf-8 -*-
"""Modo TV: botao no cabecalho (ao lado do tema) que deixa o Ao Vivo so' com os indicadores e a escala, sem menu
lateral e com letras maiores, para exibir numa TV. A escolha fica salva no navegador (o painel recarrega sozinho)."""

V20_CSS = """
/* ===== Modo TV ===== */
#hmlTv { margin-right: 8px; }
html.tv .tabs, html.tv .hml-busca-global { display: none !important; }
html.tv .dashboard-root { padding: 78px 24px 12px 24px !important; }
html.tv #hdrMenu, html.tv .header .hdr-sep, html.tv .header .hdr-crumb, html.tv .header .hml-badge { display: none; }
html.tv .header-right .clock { font-size: clamp(20px, 1.7vw, 34px); }
html.tv #tabLive > *:not(#kpiRow):not(#kpiRow2):not(#gridChatsLive) { display: none !important; }
html.tv #tabLive .kpi { padding: clamp(10px, .8vw, 18px) clamp(16px, 1.3vw, 28px); }
html.tv #tabLive .kpi-row { margin-bottom: 10px; }
html.tv #tabLive .kpi .value { font-size: clamp(26px, 2.3vw, 48px); line-height: 1.1; }
html.tv #tabLive .kpi .kpi-label, html.tv #tabLive .kpi .label { font-size: clamp(13px, 1vw, 20px); }
html.tv #tabLive .kpi .hint { font-size: clamp(10px, .7vw, 14px); }
html.tv #gridChatsLive { margin-top: 10px !important; }
html.tv #gridChatsLive .esc-grupo { margin-top: 12px; }
html.tv #gridChatsLive .esc-tab { padding: clamp(14px, 1vw, 22px) clamp(16px, 1.3vw, 28px); }
html.tv #gridChatsLive .esc-tab h2 { font-size: clamp(15px, 1.2vw, 24px); }
html.tv #gridChatsLive .esc-tab .panel-sub, html.tv #gridChatsLive .panel-menu, html.tv #gridChatsLive .resize-handle, html.tv #gridChatsLive [class*="resize-handle"], html.tv #gridChatsLive .drag-handle { display: none; }
html.tv #gridChatsLive .esc-hora { font-size: clamp(26px, 2.4vw, 48px); }
html.tv #gridChatsLive .esc-pill { font-size: clamp(12px, .95vw, 19px); padding: 4px 14px; }
html.tv #gridChatsLive .esc-g-tit { font-size: clamp(11px, .85vw, 16px); }
html.tv #gridChatsLive .esc-grade { gap: clamp(12px, 1vw, 22px); }
html.tv #gridChatsLive .esc-card { padding: clamp(12px, .85vw, 18px) clamp(12px, 1vw, 20px) clamp(10px, .75vw, 16px) clamp(16px, 1.3vw, 28px); gap: clamp(6px, .55vw, 12px); }
html.tv #gridChatsLive .esc-c-res { min-height: 0; }
html.tv #gridChatsLive .esc-c-prox { padding-top: 6px; }
html.tv #gridChatsLive .esc-c-atv { font-size: clamp(12px, .95vw, 19px); }
html.tv #gridChatsLive .esc-c-det { font-size: clamp(11px, .75vw, 15px); }
html.tv #gridChatsLive .esc-c-av { width: clamp(36px, 2.7vw, 54px); height: clamp(36px, 2.7vw, 54px); font-size: clamp(13px, 1vw, 20px); }
html.tv #gridChatsLive .esc-c-nome { font-size: clamp(18px, 1.6vw, 32px); }
html.tv #gridChatsLive .esc-c-chip, html.tv #gridChatsLive .esc-c-prox { font-size: clamp(12px, 1vw, 20px); }
html.tv #gridChatsLive .esc-c-prox span { font-size: clamp(11px, .9vw, 18px); }
html.tv #gridChatsLive .esc-c-vazio { font-size: clamp(14px, 1.2vw, 24px); }
html.tv #gridChatsLive .esc-rodape { display: none; }
html.tv .footer-note { display: none; }
"""

V20_JS = r"""
// ===== Modo TV =====
function tvAplica(liga) {
  document.documentElement.classList.toggle('tv', liga);
  const b = document.getElementById('hmlTv'), t = document.getElementById('hmlTvTxt');
  if (b) b.setAttribute('aria-pressed', liga ? 'true' : 'false');
  if (t) t.textContent = liga ? 'Sair do modo TV' : 'Modo TV';
  if (liga) { showTab('live', true); window.scrollTo(0, 0); }
}
function tvAlterna() {
  const liga = !document.documentElement.classList.contains('tv');
  tvAplica(liga);
  try { localStorage.setItem('hmlModoTv', liga ? '1' : '0'); } catch (e) {}
  // tela cheia quando o navegador permitir; se recusar, o modo TV funciona do mesmo jeito (use F11)
  try {
    if (liga && document.documentElement.requestFullscreen && !document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
    else if (!liga && document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(() => {});
  } catch (e) {}
}
{
  let salvo = false; try { salvo = localStorage.getItem('hmlModoTv') === '1'; } catch (e) {}
  if (salvo) tvAplica(true);
  // no modo TV o painel fica sempre no Ao Vivo, mesmo se algo tentar trocar de aba
  const _s4 = showTab;
  showTab = function(name, skip) { _s4(document.documentElement.classList.contains('tv') ? 'live' : name, skip); };
}
"""

BOTAO = ('<button type="button" class="hml-tema" id="hmlTv" onclick="tvAlterna()" aria-pressed="false" title="Mostra só os indicadores e a escala, em letras grandes">'
         '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="4" width="20" height="13" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
         '<span id="hmlTvTxt">Modo TV</span></button>\n      ')


def aplicar_v20(html):
    alvo = '<button type="button" class="hml-tema" id="hmlTema"'
    if alvo in html:
        html = html.replace(alvo, BOTAO + alvo, 1)
    return html
