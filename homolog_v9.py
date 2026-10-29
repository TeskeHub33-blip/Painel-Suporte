# -*- coding: utf-8 -*-
"""Homologacao v9: movimento que mostra mudanca de estado nos fluxogramas (melhorias e bugs).

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Segue as boas praticas da skill motion (Motion, ex-Framer Motion): so' transform/opacity/stroke, 150-400 ms,
movimento so' como resposta a uma acao da pessoa (selecionar uma etapa), respeitando prefers-reduced-motion.
Sem biblioteca externa: CSS animations + getTotalLength() do SVG.
"""

V9_CSS = """
/* ===== HOMOLOGACAO v9: movimento ao selecionar uma etapa ===== */
@keyframes hfEntra { from { opacity: 0; transform: translateX(10px); } }
@keyframes hfDesenha { from { stroke-dashoffset: var(--len); } to { stroke-dashoffset: 0; } }
.hf-detalhe.entra { animation: hfEntra .24s cubic-bezier(.2, .7, .2, 1) both; }
.hf-edge.on.anim { stroke-dasharray: var(--len); animation: hfDesenha .38s cubic-bezier(.3, .1, .2, 1) both; }
@media (prefers-reduced-motion: reduce) { .hf-detalhe.entra, .hf-edge.on.anim { animation: none; } }
"""

V9_JS = r"""
// ===== HOMOLOGACAO v9: movimento ao selecionar uma etapa =====
function hfAnima(raiz) {
  const el = document.querySelector(raiz); if (!el) return;
  el.querySelectorAll('.hf-edge.on').forEach((p, i) => {
    try { p.style.setProperty('--len', p.getTotalLength()); p.style.animationDelay = (i * 70) + 'ms'; p.classList.add('anim'); } catch (e) {}
  });
  const det = el.querySelector('.hf-detalhe'); if (det) det.classList.add('entra');
}
const _v9Rgm = renderGmFluxo;
renderGmFluxo = function() {
  const mudou = hfSel !== window._hfAntSel; window._hfAntSel = hfSel;
  _v9Rgm();
  if (mudou && hfSel) hfAnima('#gmFluxo');
};
const _v9Rgb = hfbRender;
hfbRender = function() {
  const mudou = HFB.sel !== window._hfbAntSel; window._hfbAntSel = HFB.sel;
  _v9Rgb();
  if (mudou && HFB.sel) hfAnima('#gbFluxo');
};
"""
