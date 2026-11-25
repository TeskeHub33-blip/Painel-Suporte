# -*- coding: utf-8 -*-
"""v23: Historico + Gestao de Indicadores viram um so' item do menu (Operacao), "Acompanhamento - KPIs", sem senha.
Sub-abas: Historico | Reuniao Mensal | Gestao Semanal - Melhorias | Gestao Semanal - Bugs."""

V23_JS = r"""
// ===== v23: Acompanhamento - KPIs (Historico + Gestao de Indicadores, sem senha) =====
{
  // 1) sem senha: libera a Reuniao Mensal logo na carga (e nas proximas, na mesma sessao)
  try { sessionStorage.setItem('reuniaoMensalUnlocked', '1'); } catch (e) {}
  const g = document.getElementById('reuniaoMensalGate'), c = document.getElementById('reuniaoMensalContent');
  if (g) g.style.display = 'none';
  if (c) c.style.display = 'block';
  try { initReuniaoMensal(); } catch (e) {}

  // 2) menu: um unico item (o do Historico, renomeado); o botao da Gestao de Indicadores some
  const bh = document.getElementById('tabBtnHist'), br = document.getElementById('tabBtnReuniaoMensal');
  if (bh) {
    const sv = bh.querySelector('svg');
    bh.textContent = 'Acompanhamento - KPIs';
    if (sv) bh.insertAdjacentElement('afterbegin', sv);
    bh.title = 'Acompanhamento - KPIs';
  }
  if (br) br.style.display = 'none';

  // 3) sub-abas: mesma barra nas duas paginas
  const SUBS = [['hist', 'Histórico'], ['reuniao', 'Reunião Mensal'], ['melhorias', 'Gestão Semanal - Melhorias'], ['bugs', 'Gestão Semanal - Bugs']];
  const botoes = ativa => SUBS.map(s => '<button type="button"' + (s[0] === ativa ? ' class="active"' : '') + ' data-sub="' + s[0] + '" onclick="kpiIr(\'' + s[0] + '\')">' + s[1] + '</button>').join('');
  const th = document.getElementById('tabHist');
  if (th && !document.getElementById('kpiNavHist')) th.insertAdjacentHTML('afterbegin', '<div class="gi-nav" id="kpiNavHist" role="tablist">' + botoes('hist') + '</div>');
  const gn = document.getElementById('giNav');
  if (gn && !gn.querySelector('[data-sub="hist"]')) gn.insertAdjacentHTML('afterbegin', '<button type="button" data-sub="hist" onclick="kpiIr(\'hist\')">Histórico</button>');

  // 4) o item do menu fica ativo em qualquer uma das sub-abas
  const _s23 = showTab;
  showTab = function (name, skip) {
    _s23(name, skip);
    const dentro = name === 'hist' || name === 'reuniaoMensal' || name === 'gestaoMelhorias';
    if (bh) bh.classList.toggle('active', dentro);
    if (typeof v18Crumb === 'function') v18Crumb();
  };
  try { const a = localStorage.getItem('activeTab'); if (a === 'hist' || a === 'reuniaoMensal') showTab(a, true); } catch (e) {}
}
function kpiIr(sub) {
  if (sub === 'hist') { showTab('hist'); return; }
  showTab('reuniaoMensal');
  setGiSub(sub);
}
"""
