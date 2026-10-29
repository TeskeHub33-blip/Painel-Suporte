# -*- coding: utf-8 -*-
"""Homologacao v11: ao selecionar um chamado, a parte do fluxo que ele ainda nao alcancou fica menos colorida.

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.
Vale para os tres fluxogramas: atendimento (aba Fluxograma), melhorias e bugs.
"""

V11_CSS = """
/* ===== HOMOLOGACAO v11: o que o chamado ainda nao alcancou fica apagado ===== */
.hf-node { transition: opacity .2s, filter .2s, box-shadow .15s; }
.hf-node.pendente { opacity: .5; filter: saturate(.15); }
.hf-node.pendente .hf-v { color: var(--text3); }
.hf-node.pendente.sel { opacity: .85; filter: saturate(.6); }
.hf-edge.pendente, .hf-seta.pendente { opacity: .18; }
.hf-edge.on.pendente, .hf-seta.on.pendente { opacity: .55; }
"""

V11_JS = r"""
// ===== HOMOLOGACAO v11: apaga o que o chamado ainda nao alcancou =====
function hmlAplicaPendente(raiz, alcancadas) {
  const el = document.querySelector(raiz); if (!el) return;
  el.querySelectorAll('.hf-node').forEach(n => n.classList.toggle('pendente', !!alcancadas && !alcancadas.has(n.dataset.k)));
  el.querySelectorAll('[data-e]').forEach(p => { const [a, b] = p.dataset.e.split('>'); p.classList.toggle('pendente', !!alcancadas && !(alcancadas.has(a) && alcancadas.has(b))); });
}
// melhorias: caminho gratuito, cobrado ou o trecho comum enquanto o Produto ainda nao decidiu
function hmlAlcancadasMel(t) {
  const k = gmEtapa(t);
  const tec = gmTagTem(t, 'estimativa t'), com = gmTagTem(t, 'estimativa c'), apr = gmTagTem(t, 'aprovado');
  let caminho;
  if (apr || ['aprov', 'n2apr'].indexOf(k) !== -1) caminho = ['n1', 'n2', 'refina', 'aprov', 'n2apr', 'prev', 'agend'];
  else if (tec || com || ['tec', 'aprcom', 'orc', 'assin', 'n2com'].indexOf(k) !== -1) caminho = ['n1', 'n2', 'refina', 'tec', 'aprcom', 'orc', 'assin', 'n2com', 'prev', 'agend'];
  else caminho = ['n1', 'n2', 'refina', 'decide'];
  if (k === 'info') return new Set(['cliente', 'n1', 'n2', 'info']);
  const idx = k ? caminho.indexOf(k) : -1; if (idx === -1) return null;
  const s = new Set(['cliente'].concat(caminho.slice(0, idx + 1))); if (idx >= 3) s.add('decide');
  return s;
}
// bugs: tronco ate a etapa atual; as laterais (cliente, terceiros) e o desvio devops so' quando for o caso
function hfbAlcancadas(t) {
  const k = hfbEtapa(t); if (!k) return null;
  const ordem = ['cliente', 'n1', 'repasse', 'n2', 'dev', 'valid', 'reacao', 'fim'];
  if (k === 'cli' || k === 'terc') return new Set(['cliente', 'n1', 'repasse', 'n2', k]);
  if (k === 'imped') return new Set(['cliente', 'n1', 'repasse', 'n2', 'dev', 'imped']);
  const i = ordem.indexOf(k); return i === -1 ? null : new Set(ordem.slice(0, i + 1));
}
{
  const _d = hmlDestacaEtapa;
  hmlDestacaEtapa = function() {
    _d();
    const entrada = document.getElementById('gmBuscaInput');
    if (entrada && !entrada.value.trim()) hmlMelhoriaSel = null;       // resultado fechado: volta ao fluxo completo
    hmlAplicaPendente('#gmFluxo', hmlMelhoriaSel ? hmlAlcancadasMel(hmlMelhoriaSel) : null);
  };
  const _b = hfbDestaca;
  hfbDestaca = function() {
    _b();
    const entrada = document.getElementById('gbBuscaInput');
    if (entrada && !entrada.value.trim()) hfbMarcado = null;
    hmlAplicaPendente('#gbFluxo', hfbMarcado ? hfbAlcancadas(hfbMarcado) : null);
  };
}
"""
