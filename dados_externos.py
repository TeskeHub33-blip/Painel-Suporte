# -*- coding: utf-8 -*-
"""Separa os dados do HTML do painel.

externalizar(html): tira os dados de dentro da pagina. Os <script> comuns viram texto inerte (data-app) e um carregador
no fim da pagina busca o dados.json, recria o bloco da escala e so' entao executa o codigo, na mesma ordem de antes.
montar_dados(...): monta o conteudo do dados.json que o carregador entrega para a pagina (variavel __DADOS).

O HTML gerado aqui NAO pode depender dos dados: se mudar a cada rodada do robo, a Vercel volta a fazer deploy toda hora.
"""
import json
import os
import re

# Onde a pagina busca os dados (branch "dados" do repositorio; a Vercel nao faz deploy dessa branch).
DADOS_URL = 'https://raw.githubusercontent.com/TeskeHub33-blip/Painel-Suporte/dados/dados.json'

# Tela de carregamento (caminhao da EmiteAi). Fica no INICIO da pagina para aparecer no primeiro quadro.
# Nos recarregamentos automaticos (URL com ?t=) ela nao aparece, para nao piscar na TV.
CAMINHAO = r"""<style>
#carregandoDados{position:fixed;inset:0;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;background:radial-gradient(ellipse at 50% 40%,#25376a 0%,#141f3f 70%);color:#fff;font-family:Inter,Arial,sans-serif;text-align:center;padding:24px;transition:opacity .45s ease}
#carregandoDados.some{opacity:0;pointer-events:none}
html.sem-caminhao #carregandoDados{display:none}
#carregandoDados .cd-cena{position:relative;width:min(460px,86vw);height:150px;overflow:hidden}
#carregandoDados .cd-estrada{position:absolute;left:0;right:0;bottom:14px;height:4px;border-radius:2px;background:rgba(255,255,255,.18)}
#carregandoDados .cd-faixa{position:absolute;left:0;bottom:15px;width:200%;height:2px;background:repeating-linear-gradient(90deg,rgba(255,255,255,.75) 0 26px,transparent 26px 58px);animation:cdFaixa .7s linear infinite}
#carregandoDados .cd-caminhao{position:absolute;left:50%;bottom:18px;width:230px;margin-left:-115px;animation:cdBalanca .5s ease-in-out infinite}
#carregandoDados .cd-roda{transform-box:fill-box;transform-origin:center;animation:cdRoda .55s linear infinite}
#carregandoDados .cd-vento{animation:cdVento 1s linear infinite}
#carregandoDados h2{margin:0;font-size:clamp(18px,2.4vw,26px);font-weight:700;letter-spacing:-.2px}
#carregandoDados p{margin:0;font-size:clamp(13px,1.5vw,16px);opacity:.75}
#carregandoDados .cd-pontos span{display:inline-block;animation:cdPonto 1.2s infinite both}
#carregandoDados .cd-pontos span:nth-child(2){animation-delay:.2s}
#carregandoDados .cd-pontos span:nth-child(3){animation-delay:.4s}
#carregandoDados.erro h2{color:#ffb4ab}
@keyframes cdFaixa{from{transform:translateX(0)}to{transform:translateX(-58px)}}
@keyframes cdBalanca{0%,100%{transform:translateY(0)}50%{transform:translateY(-2.5px)}}
@keyframes cdRoda{to{transform:rotate(360deg)}}
@keyframes cdVento{0%{transform:translateX(18px);opacity:0}30%{opacity:.9}100%{transform:translateX(-26px);opacity:0}}
@keyframes cdPonto{0%,80%,100%{opacity:.2}40%{opacity:1}}
@media (prefers-reduced-motion:reduce){#carregandoDados *{animation-duration:3s!important}}
</style>
<script>if(location.search.indexOf('t=')>-1)document.documentElement.classList.add('sem-caminhao');</script>
<div id="carregandoDados" role="status" aria-live="polite">
  <div class="cd-cena" aria-hidden="true">
    <div class="cd-estrada"></div><div class="cd-faixa"></div>
    <svg class="cd-caminhao" viewBox="0 0 230 110" xmlns="http://www.w3.org/2000/svg">
      <g class="cd-vento" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".6"><line x1="6" y1="34" x2="30" y2="34"/><line x1="0" y1="50" x2="22" y2="50"/><line x1="10" y1="66" x2="34" y2="66"/></g>
      <rect x="36" y="10" width="124" height="68" rx="6" fill="#fff"/>
      <rect x="36" y="58" width="124" height="9" fill="#ed6da2"/>
      <text x="98" y="42" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="800" font-size="19" fill="#1d2b4f">emitea&iacute;</text>
      <path d="M164 28h28q8 0 13 8l15 20q3 4 3 9v13h-59z" fill="#ed6da2"/>
      <path d="M172 36h17q4 0 6 3l10 14h-33z" fill="#cfe3ff"/>
      <rect x="36" y="78" width="184" height="8" rx="3" fill="#1d2b4f" stroke="#fff" stroke-opacity=".25"/>
      <g><circle class="cd-roda" cx="70" cy="90" r="13" fill="#10182f" stroke="#fff" stroke-width="3"/><line class="cd-roda" x1="70" y1="80" x2="70" y2="100" stroke="#fff" stroke-width="2.5"/></g>
      <g><circle class="cd-roda" cx="120" cy="90" r="13" fill="#10182f" stroke="#fff" stroke-width="3"/><line class="cd-roda" x1="120" y1="80" x2="120" y2="100" stroke="#fff" stroke-width="2.5"/></g>
      <g><circle class="cd-roda" cx="196" cy="90" r="13" fill="#10182f" stroke="#fff" stroke-width="3"/><line class="cd-roda" x1="196" y1="80" x2="196" y2="100" stroke="#fff" stroke-width="2.5"/></g>
    </svg>
  </div>
  <h2 id="cdTitulo">Estamos trazendo novas informa&ccedil;&otilde;es para a sua tela<span class="cd-pontos"><span>.</span><span>.</span><span>.</span></span></h2>
  <p id="cdTexto">Um instante, o painel j&aacute; vai aparecer.</p>
</div>
"""

CARREGADOR = r"""
<script>
(function () {
  var URL_DADOS = '__URL__';
  var aviso = document.getElementById('carregandoDados');
  var inicio = Date.now();
  var MIN_MS = document.documentElement.classList.contains('sem-caminhao') ? 0 : 1400;   // deixa o caminhao andar um pouco
  function mostra(txt) {
    if (!aviso) return;
    aviso.className = 'erro'; aviso.style.display = '';
    var t = document.getElementById('cdTitulo'), x = document.getElementById('cdTexto');
    if (t) t.textContent = 'Não foi possível carregar os dados';
    if (x) x.textContent = txt;
  }
  function escondeAviso() {
    if (!aviso) return;
    aviso.className = 'some';
    setTimeout(function () { aviso.style.display = 'none'; }, 500);
  }
  function inicia(d) {
    window.__DADOS = d;
    var e = document.createElement('script');
    e.type = 'application/json'; e.id = 'escalaDados';
    e.textContent = JSON.stringify(d.escala || {}).replace(/<\//g, '<\/');
    document.body.appendChild(e);
    var el = document.getElementById('dadosEm'); if (el) el.textContent = d.now_br || '-';
    var nos = document.querySelectorAll('script[data-app]');
    for (var i = 0; i < nos.length; i++) {          // mesma ordem e mesmo escopo global de antes
      var s = document.createElement('script');
      s.text = nos[i].textContent;
      document.head.appendChild(s);
    }
    setTimeout(escondeAviso, Math.max(0, MIN_MS - (Date.now() - inicio)));
  }
  function carrega(tentativa) {
    fetch(URL_DADOS + '?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(inicia)
      .catch(function (err) {
        mostra('Tentando de novo em 30 segundos (' + err.message + ').');
        setTimeout(function () { carrega(tentativa + 1); }, 30000);
      });
  }
  carrega(0);
})();
</script>
"""


def externalizar(html):
    # bloco da escala (recriado pelo carregador a partir do dados.json)
    html = re.sub(r'<script type="application/json" id="escalaDados">.*?</script>\s*', '', html, flags=re.S)
    n = html.count('<script>')
    html = html.replace('<script>', '<script type="text/plain" data-app>')
    assert n >= 1, 'nenhum <script> encontrado para externalizar'
    return CAMINHAO + html + CARREGADOR.replace('__URL__', DADOS_URL)


def montar_dados(valores, now_br, now_iso, base_dir):
    d = dict(valores)
    d['now_br'] = now_br
    d['now_iso'] = now_iso
    try:
        with open(os.path.join(base_dir, 'escala.json'), encoding='utf-8') as f:
            d['escala'] = json.load(f)
    except Exception:
        d['escala'] = {}
    return d
