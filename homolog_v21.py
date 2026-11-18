# -*- coding: utf-8 -*-
"""Aba Configuracao: lista de clientes TMS Admin e em quais partes do painel eles ficam de fora.
Salva no GitHub (branch "config", arquivo painel_config.json) pela funcao /api/tms; todos os navegadores leem de la."""

V21_JS = r"""
// ===== Configuracao: clientes TMS Admin =====
let TMS_RASCUNHO = null;
function tmsClientesConhecidos() {
  const s = new Set();
  TICKETS_TODOS.forEach(t => { if (t.clientOrg) s.add(t.clientOrg); });
  Object.keys(RESOLVED_MONTHS_RAW).forEach(k => RESOLVED_MONTHS_RAW[k].forEach(r => { if (r.clientOrg) s.add(r.clientOrg); }));
  return Array.from(s).sort((a, b) => a.localeCompare(b));
}
function tmsRascunho() {
  if (!TMS_RASCUNHO) {
    const c = TMS.cfg || {};
    const ex = c.excluir || {};
    TMS_RASCUNHO = { clientes: (c.clientes || []).slice(), abertos: ex.abertos !== false, historico: ex.historico !== false };
  }
  return TMS_RASCUNHO;
}
function tmsCfgRender() {
  const root = document.getElementById('cfgCorpo'); if (!root || !root.firstChild) return;
  let box = document.getElementById('tmsCfg');
  if (!box) { box = document.createElement('div'); box.id = 'tmsCfg'; root.insertBefore(box, root.firstChild); }
  const r = tmsRascunho();
  box.innerHTML = `<div class="panel" style="margin-bottom:18px;"><h2>🏢 TMS Admin — clientes tratados à parte</h2>
    <div class="panel-sub">Os clientes desta lista <b>saem</b> dos números do painel nas partes marcadas abaixo e passam a aparecer só no card <b>TMS Admin</b> (aba Ao Vivo), com indicadores próprios. Pode ter mais de um. A lista fica salva no GitHub e vale para todos que abrirem o painel.</div>
    <div id="tmsLista" style="display:flex; flex-wrap:wrap; gap:8px; margin:10px 0;">${r.clientes.length ? r.clientes.map((c, i) => `<span class="and-selo" style="gap:10px;">${esc(c)} <button type="button" class="cfg-btn" style="padding:0 8px; border-radius:50%;" title="Remover" onclick="tmsRemove(${i})">✕</button></span>`).join('') : '<span class="panel-sub">Nenhum cliente na lista.</span>'}</div>
    <div class="cfg-acoes" style="align-items:center;"><input type="text" id="tmsNovo" list="tmsOpcoes" placeholder="Digite ou escolha o nome do cliente (como aparece no painel)" style="max-width:460px;" onkeydown="if(event.key==='Enter')tmsAdd()">
      <datalist id="tmsOpcoes">${tmsClientesConhecidos().map(c => `<option value="${esc(c)}">`).join('')}</datalist>
      <button type="button" class="cfg-btn" onclick="tmsAdd()">Adicionar</button></div>
    <div class="cfg-grid" style="margin-top:14px;">
      <label class="cfg-chave"><input type="checkbox" id="tmsAbertos" ${r.abertos ? 'checked' : ''} onchange="tmsRascunho().abertos=this.checked"> Tirar de <b>Ao Vivo</b>, Gestão de Melhorias e Fluxograma (chamados em aberto e resolvidos de hoje)</label>
      <label class="cfg-chave"><input type="checkbox" id="tmsHist" ${r.historico ? 'checked' : ''} onchange="tmsRascunho().historico=this.checked"> Tirar de <b>Histórico, Clientes, One-on-One, Gamificação e Reunião Mensal</b> (resolvidos e abertos por mês)</label>
    </div>
    <div class="cfg-acoes"><button type="button" class="cfg-btn" onclick="tmsSalva()">Salvar para todos</button><span id="tmsMsg" class="panel-sub" style="align-self:center;"></span></div>
    <div class="panel-sub" style="margin-top:6px;">O nome precisa ser igual ao do cliente no painel (acentos, maiúsculas e símbolos são ignorados). NPS e emissões não têm cliente por chamado e continuam inteiros.</div></div>`;
}
function tmsAdd() {
  const i = document.getElementById('tmsNovo'); if (!i) return;
  const v = i.value.trim(); if (!v) return;
  const r = tmsRascunho();
  if (!r.clientes.some(c => TMS.norm(c) === TMS.norm(v))) r.clientes.push(v);
  tmsCfgRender();
}
function tmsRemove(i) { tmsRascunho().clientes.splice(i, 1); tmsCfgRender(); }
async function tmsSalva() {
  const m = document.getElementById('tmsMsg'), r = tmsRascunho();
  const corpo = { clientes: r.clientes, excluir: { abertos: !!r.abertos, historico: !!r.historico } };
  m.textContent = 'Salvando...';
  try {
    const resp = await fetch('/api/tms', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + cfgToken() }, body: JSON.stringify(corpo) });
    const d = await resp.json().catch(() => ({}));
    if (!resp.ok) { m.textContent = d.erro || ('Não foi possível salvar (' + resp.status + ').'); return; }
    try { localStorage.setItem('painelCfgLocal', JSON.stringify({ salvo_em: d.salvo_em, tms_admin: corpo })); } catch (e) {}
    m.textContent = 'Salvo para todos. Recarregando o painel...';
    setTimeout(() => { location.href = location.pathname + '?t=' + Date.now(); }, 1200);
  } catch (e) { m.textContent = 'Falha de conexão ao salvar.'; }
}
{
  const _cr = cfgRender;
  cfgRender = function () { _cr(); tmsCfgRender(); };
}
"""
