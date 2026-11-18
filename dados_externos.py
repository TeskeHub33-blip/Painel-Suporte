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

CARREGADOR = r"""
<style>#carregandoDados{position:fixed;left:50%;top:70px;transform:translateX(-50%);z-index:99999;padding:10px 18px;border-radius:8px;background:#1d2b4f;color:#fff;font:600 14px Inter,Arial,sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.3)}#carregandoDados.erro{background:#b3261e}</style>
<div id="carregandoDados">Carregando dados do painel...</div>
<script>
(function () {
  var URL_DADOS = '__URL__';
  var aviso = document.getElementById('carregandoDados');
  function mostra(txt, erro) { if (!aviso) return; aviso.textContent = txt; aviso.className = erro ? 'erro' : ''; aviso.style.display = ''; }
  function inicia(d) {
    window.__DADOS = d;
    var e = document.createElement('script');
    e.type = 'application/json'; e.id = 'escalaDados';
    e.textContent = JSON.stringify(d.escala || {}).replace(/<\//g, '<\/');
    document.body.appendChild(e);
    var el = document.getElementById('dadosEm'); if (el) el.textContent = d.now_br || '-';
    if (aviso) aviso.style.display = 'none';
    var nos = document.querySelectorAll('script[data-app]');
    for (var i = 0; i < nos.length; i++) {          // mesma ordem e mesmo escopo global de antes
      var s = document.createElement('script');
      s.text = nos[i].textContent;
      document.head.appendChild(s);
    }
  }
  function carrega(tentativa) {
    fetch(URL_DADOS + '?t=' + Math.floor(Date.now() / 60000), { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(inicia)
      .catch(function (err) {
        mostra('Nao foi possivel carregar os dados (' + err.message + '). Tentando de novo em 30 s...', true);
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
    return html + CARREGADOR.replace('__URL__', DADOS_URL)


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
