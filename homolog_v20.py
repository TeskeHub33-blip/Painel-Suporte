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
/* modo TV: sem botao de tema; botao do modo TV so' na aba Painel Diario (Ao Vivo) */
html.tv #hmlTema { display: none !important; }
html:not(.aba-live) #hmlTv { display: none !important; }
/* cards: tudo centralizado, sem as linhas de contagem sob o nome, e distribuidos pela largura (e pela altura da tela) */
html.tv #tabLive .kpi .hint { display: none !important; }
html.tv #tabLive .kpi { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: clamp(4px, .5vw, 10px); }
html.tv #tabLive .kpi .value { font-size: clamp(34px, 3.6vw, 76px); line-height: 1; text-align: center; }
html.tv #tabLive .kpi .kpi-label, html.tv #tabLive .kpi .label, html.tv #tabLive .kpi > *:not(.value):not(.hint) { font-size: clamp(14px, 1.25vw, 26px); text-align: center; }
html.tv #kpiRow, html.tv #kpiRow2 { grid-template-columns: repeat(5, 1fr) !important; gap: clamp(10px, 1vw, 20px); margin-top: 0 !important; }
html.tv #tabLive .kpi { padding: clamp(14px, 1.6vh, 30px) clamp(10px, 1vw, 24px); min-height: clamp(90px, 14vh, 180px); }
html.tv.inc-on #tabLive .kpi { padding: clamp(8px, 1vh, 16px) clamp(8px, .8vw, 18px); min-height: clamp(60px, 8vh, 96px); }
html.tv.inc-on #tabLive .kpi .value { font-size: clamp(28px, 2.8vw, 58px); }
html.tv.inc-on #tabLive { min-height: 0; }
html.tv.inc-on #gridChatsLive .esc-tab { padding: 8px 16px; }
html.tv.inc-on #gridChatsLive .esc-card { padding-top: 7px; padding-bottom: 6px; gap: 3px; }
html.tv.inc-on #gridChatsLive .esc-grupo { margin-top: 6px; }
html.tv.inc-on #gridChatsLive .esc-c-prox { padding-top: 3px; }
html.tv.inc-on #gridChatsLive .esc-grade { margin-top: 8px; gap: 8px; }
html.tv #tabLive { display: flex; flex-direction: column; min-height: calc(100vh - 78px - 14px - var(--inc-h, 0px)); }
html.tv #tabLive #gridChatsLive { flex: 1 1 auto; }
"""

V20_JS = r"""
// ===== Modo TV =====
// Mantem a tela da TV acesa: Screen Wake Lock (Chrome/Edge). A pagina recarrega sozinha a cada 5 min e isso solta o bloqueio,
// entao ele e' pedido de novo a cada carga, ao voltar para a aba e a cada 2 minutos enquanto o modo TV estiver ligado.
let _tvWake = null;
function tvEmModoTv() { return document.documentElement.classList.contains('tv'); }
// Segundo metodo, para navegadores sem Wake Lock (ex.: TV LG webOS): um video mudo e quase invisivel, gerado de um canvas, fica
// tocando; em TVs e celulares, video em reproducao impede a tela de descanso/economia de energia.
let _tvVideo = null, _tvCanvas = null, _tvQuadro = 0;
function tvVideoAcesa() {
  try {
    if (!tvEmModoTv()) { if (_tvVideo) { _tvVideo.pause(); _tvVideo.remove(); _tvVideo = null; } return; }
    if (!_tvVideo) {
      _tvCanvas = document.createElement('canvas'); _tvCanvas.width = 16; _tvCanvas.height = 16;
      const v = document.createElement('video');
      v.muted = true; v.defaultMuted = true; v.loop = true;
      v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.setAttribute('aria-hidden', 'true');
      v.style.cssText = 'position:fixed;right:0;bottom:0;width:2px;height:2px;opacity:.01;pointer-events:none;z-index:-1';
      const nz = window.TV_NOSLEEP;
      if (nz) v.innerHTML = '<source src="' + nz.webm + '" type="video/webm"><source src="' + nz.mp4 + '" type="video/mp4">';
      else if (_tvCanvas.captureStream) v.srcObject = _tvCanvas.captureStream(5);
      else return;
      document.body.appendChild(v); _tvVideo = v;
    }
    const c = _tvCanvas.getContext('2d'); _tvQuadro++;
    c.fillStyle = (_tvQuadro % 2) ? '#000' : '#020202'; c.fillRect(0, 0, 16, 16);   // muda o quadro para o video nao "congelar"
    if (_tvVideo.paused) { const p = _tvVideo.play(); if (p && p.catch) p.catch(() => {}); }
  } catch (e) {}
}
setInterval(tvVideoAcesa, 2000);
async function tvMantemAcesa() {
  tvVideoAcesa();
  try {
    if (!tvEmModoTv()) { if (_tvWake) { await _tvWake.release(); _tvWake = null; } return; }
    if (!('wakeLock' in navigator) || document.visibilityState !== 'visible') return;
    if (_tvWake && !_tvWake.released) return;
    _tvWake = await navigator.wakeLock.request('screen');
    _tvWake.addEventListener('release', () => { _tvWake = null; });
  } catch (e) { _tvWake = null; }
}
setInterval(tvMantemAcesa, 2 * 60 * 1000);
document.addEventListener('visibilitychange', tvMantemAcesa);
document.addEventListener('fullscreenchange', tvMantemAcesa);
function tvAplica(liga) {
  document.documentElement.classList.toggle('tv', liga);
  tvMantemAcesa();
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
  showTab = function(name, skip) {
    const alvo = document.documentElement.classList.contains('tv') ? 'live' : name;
    _s4(alvo, skip);
    document.documentElement.classList.toggle('aba-live', alvo === 'live');
  };
  document.documentElement.classList.add('aba-live');    // a pagina abre no Painel Diario (Ao Vivo)
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && document.documentElement.classList.contains('tv')) tvAlterna(); });
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
