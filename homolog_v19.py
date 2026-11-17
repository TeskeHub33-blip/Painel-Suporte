# -*- coding: utf-8 -*-
"""Filtro por analista no detalhamento (janela que abre ao clicar num card ou numa barra).
Vale para as listas ao vivo e para as do historico. A exportacao para Excel respeita o filtro."""

V19_CSS = """
/* ===== Filtro por analista no detalhamento ===== */
#modalAnalista { min-width: 210px; max-width: 280px; font-size: 13px; padding: 7px 10px; }
"""

V19_JS = r"""
// ===== Filtro por analista no detalhamento =====
let MODAL_BASE = null;   // {itens, modo: 'live' | 'hist', campo}
function modalAnalistaOpcoes(itens) {
  const sel = document.getElementById('modalAnalista'); if (!sel) return;
  const cont = {};
  itens.forEach(t => { const n = t.ownerName || 'Sem tecnico'; cont[n] = (cont[n] || 0) + 1; });
  const nomes = Object.keys(cont).sort((a, b) => cont[b] - cont[a] || a.localeCompare(b, 'pt-BR'));
  sel.innerHTML = '<option value="">Todos os analistas (' + itens.length + ')</option>' + nomes.map(n => '<option value="' + esc(n) + '">' + esc(n) + ' (' + cont[n] + ')</option>').join('');
  sel.value = '';
  sel.style.display = nomes.length > 1 ? '' : 'none';
}
function modalFiltraAnalista() {
  const sel = document.getElementById('modalAnalista'); if (!sel || !MODAL_BASE) return;
  const nome = sel.value, b = MODAL_BASE;
  const itens = nome ? b.itens.filter(t => (t.ownerName || 'Sem tecnico') === nome) : b.itens;
  document.getElementById('modalTbody').innerHTML = b.modo === 'hist' ? tableHtmlHist(itens) : tableHtml(itens, b.campo, 200);
  document.getElementById('modalCount').textContent = itens.length + ' chamado(s)' + (nome ? ' de ' + nome + ' · ' + b.itens.length + ' no total' : '');
  CURRENT_MODAL_ITEMS = itens;   // o Excel exporta o que esta na tela
}
{
  const _rm = renderModal;
  renderModal = function(title, items, timeField) { _rm(title, items, timeField); MODAL_BASE = {itens: CURRENT_MODAL_ITEMS.slice(), modo: 'live', campo: timeField}; modalAnalistaOpcoes(MODAL_BASE.itens); };
  const _rh = renderModalHist;
  renderModalHist = function(title, items) { _rh(title, items); MODAL_BASE = {itens: CURRENT_MODAL_ITEMS.slice(), modo: 'hist'}; modalAnalistaOpcoes(MODAL_BASE.itens); };
}
"""


def aplicar_v19(html):
    alvo = '<span class="export-btn" title="Exportar para Excel (.txt)" onclick="exportCurrentModal()">'
    sel = '<select id="modalAnalista" class="itil-select" aria-label="Filtrar por analista" onchange="modalFiltraAnalista()"></select>\n        '
    i = html.find('id="modalOverlay"')          # a janela de detalhamento principal (ha outras janelas com o mesmo botao)
    j = html.find(alvo, i) if i != -1 else -1
    if j != -1:
        html = html[:j] + sel + alvo.replace('(.txt)', '(.csv)') + html[j + len(alvo):]
    return html
