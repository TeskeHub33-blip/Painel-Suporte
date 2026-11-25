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
  const SUBS = [['hist', 'Histórico'], ['reuniao', 'Reunião Mensal'], ['melhorias', 'Gestão Semanal - Melhorias'], ['bugs', 'Gestão Semanal - Bugs'], ['fat', 'Faturamento']];
  const botoes = ativa => SUBS.map(s => '<button type="button"' + (s[0] === ativa ? ' class="active"' : '') + ' data-sub="' + s[0] + '" onclick="kpiIr(\'' + s[0] + '\')">' + s[1] + '</button>').join('');
  const th = document.getElementById('tabHist');
  if (th && !document.getElementById('kpiNavHist')) th.insertAdjacentHTML('afterbegin', '<div class="gi-nav" id="kpiNavHist" role="tablist">' + botoes('hist') + '</div>');
  if (th && !document.getElementById('tabFaturamento')) {
    th.insertAdjacentHTML('afterend', '<div class="tab-panel" id="tabFaturamento"><div class="gi-nav" id="kpiNavFat" role="tablist">' + botoes('fat') + '</div><div id="fatCorpo"></div></div>');
  }
  const gn = document.getElementById('giNav');
  if (gn && !gn.querySelector('[data-sub="hist"]')) gn.insertAdjacentHTML('afterbegin', '<button type="button" data-sub="hist" onclick="kpiIr(\'hist\')">Histórico</button>');

  // 4) o item do menu fica ativo em qualquer uma das sub-abas
  const _s23 = showTab;
  showTab = function (name, skip) {
    _s23(name === 'fat' ? 'hist' : name, true);
    const pf = document.getElementById('tabFaturamento');
    if (name === 'fat') {
      document.getElementById('tabHist').classList.remove('active');
      if (pf) pf.classList.add('active');
      if (!skip) { try { localStorage.setItem('activeTab', 'fat'); } catch (e) {} }
      fatAbre();
    } else {
      if (pf) pf.classList.remove('active');
      if (!skip) { try { localStorage.setItem('activeTab', name); } catch (e) {} }
    }
    const dentro = name === 'hist' || name === 'reuniaoMensal' || name === 'gestaoMelhorias' || name === 'fat';
    if (bh) bh.classList.toggle('active', dentro);
    if (typeof v18Crumb === 'function') v18Crumb();
  };
  try { const a = localStorage.getItem('activeTab'); if (a === 'hist' || a === 'reuniaoMensal' || a === 'fat') showTab(a, true); } catch (e) {}
}
function kpiIr(sub) {
  if (sub === 'hist') { showTab('hist'); return; }
  if (sub === 'fat') { showTab('fat'); return; }
  showTab('reuniaoMensal');
  setGiSub(sub);
}

// --- Faturamento (view faturamento_det_v, lida pela funcao /api/faturamento; nada fica salvo no git) ---
var FAT = null, FAT_MES = '', FAT_FILTRO = '';
var FAT_N = v => Number(v || 0).toLocaleString('pt-BR');
var FAT_COLS = [['nome', 'Cliente'], ['cnpj', 'CNPJ'], ['municipio', 'Município'], ['uf', 'UF'], ['cte_total', 'CT-e'], ['nfse_total', 'NFS-e'], ['gnre_total', 'GNRE'], ['mdfe_total', 'MDF-e'], ['ciot_total', 'CIOT']];
function fatTelaSenha(msg) {
  document.getElementById('fatCorpo').innerHTML = '<div class="panel" style="max-width:380px; margin:30px auto; text-align:center;"><h2>Faturamento protegido</h2>' +
    '<div class="panel-sub" style="margin-bottom:14px;">Informe a senha para ver o faturamento por cliente.</div>' +
    '<input id="fatSenha" type="password" class="itil-select" style="width:100%; text-align:center; margin-bottom:10px;" placeholder="Senha" autocomplete="current-password" onkeydown="if(event.key===\'Enter\')fatEntrar()">' +
    '<div><button type="button" class="export-btn" style="padding:8px 22px; font-size:13px;" onclick="fatEntrar()">Entrar</button></div>' +
    '<div id="fatErro" style="color:var(--danger); font-size:12px; margin-top:10px; min-height:16px;">' + (msg ? esc(msg) : '') + '</div></div>';
  const i = document.getElementById('fatSenha'); if (i) i.focus();
}
async function fatEntrar() {
  const i = document.getElementById('fatSenha'), er = document.getElementById('fatErro'); if (!i) return;
  er.textContent = 'Verificando...';
  try {
    const r = await fetch('/api/auth', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ senha: i.value }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { er.textContent = d.erro || 'Não foi possível validar a senha.'; i.value = ''; return; }
    cfgGuardaToken(d.token); fatCarrega();
  } catch (e) { er.textContent = 'Falha de conexão com o servidor.'; }
}
function fatAbre() {
  if (!/\.vercel\.app$/.test(location.hostname)) { document.getElementById('fatCorpo').innerHTML = '<div class="panel"><div class="panel-sub">O faturamento só está disponível no endereço do painel na Vercel.</div></div>'; return; }
  if (!cfgToken()) { fatTelaSenha(''); return; }
  if (!FAT) fatCarrega(); else fatRender();
}
async function fatCarrega(mes) {
  const box = document.getElementById('fatCorpo');
  box.innerHTML = '<div class="panel"><div class="panel-sub">Carregando o faturamento...</div></div>';
  try {
    const r = await fetch('/api/faturamento' + (mes ? '?mes=' + encodeURIComponent(mes) : ''), { headers: { 'Authorization': 'Bearer ' + cfgToken() } });
    const d = await r.json().catch(() => ({}));
    if (r.status === 401) { cfgGuardaToken(''); fatTelaSenha(d.erro || ''); return; }
    if (!r.ok) { box.innerHTML = '<div class="panel"><div class="panel-sub" style="color:var(--danger);">' + esc(d.erro || 'Não foi possível carregar o faturamento.') + '</div><div style="margin-top:10px;"><button type="button" class="export-btn" onclick="fatCarrega()">Tentar de novo</button></div></div>'; return; }
    FAT = d; FAT_MES = d.mes || ''; fatRender();
  } catch (e) { box.innerHTML = '<div class="panel"><div class="panel-sub" style="color:var(--danger);">Falha de conexão ao carregar o faturamento.</div></div>'; }
}
function fatLinhas() {
  const t = (FAT_FILTRO || '').toLowerCase().trim(), dig = t.replace(/\D/g, '');
  return (FAT.dados || []).filter(r => {
    if (!t) return true;
    const txt = [r.nome, r.cnpj, r.cnpj_matriz, r.municipio, r.uf].join(' ').toLowerCase();
    return txt.indexOf(t) !== -1 || (dig.length >= 3 && String(r.cnpj || '').replace(/\D/g, '').indexOf(dig) !== -1);
  });
}
function fatRender() {
  if (!FAT) return;
  const ex = FAT.execucao, ate = ex && ex.dt_fim ? ex.dt_fim.split('-').reverse().join('/') : '-';
  const lin = fatLinhas(), soma = k => lin.reduce((s, r) => s + Number(r[k] || 0), 0);
  const clientes = new Set(lin.map(r => r.corp)).size;
  const kpi = (v, t) => '<div class="kpi"><div class="value">' + v + '</div><div class="kpi-label">' + t + '</div></div>';
  const opts = (FAT.meses || []).map(m => '<option value="' + m + '"' + (m === FAT_MES ? ' selected' : '') + '>' + m.slice(5) + '/' + m.slice(0, 4) + '</option>').join('');
  const cab = FAT_COLS.map(c => '<th' + (c[0].indexOf('_total') !== -1 ? ' style="text-align:right;"' : '') + '>' + c[1] + '</th>').join('');
  const corpo = lin.map(r => '<tr>' + FAT_COLS.map(c => { const v = r[c[0]]; return c[0].indexOf('_total') !== -1 ? '<td style="text-align:right;">' + FAT_N(v) + '</td>' : '<td>' + esc(v == null ? '' : String(v)) + '</td>'; }).join('') + '</tr>').join('') || '<tr><td colspan="' + FAT_COLS.length + '" class="empty-msg">Nenhum registro.</td></tr>';
  document.getElementById('fatCorpo').innerHTML =
    '<div class="panel-sub" style="margin-bottom:12px;">Acumulado do mês até <b>' + ate + '</b> (d-1). O banco recalcula uma vez por dia, às 02:00' + (ex && ex.status ? ' · última execução: ' + esc(ex.status) + (ex.qtd_erro ? ' (' + ex.qtd_erro + ' empresa(s) com erro)' : '') : '') + '.</div>' +
    '<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">' + kpi(FAT_N(clientes), 'Clientes') + kpi(FAT_N(soma('cte_total')), 'CT-e') + kpi(FAT_N(soma('nfse_total')), 'NFS-e') + kpi(FAT_N(soma('gnre_total')), 'GNRE') + kpi(FAT_N(soma('mdfe_total')), 'MDF-e') + kpi(FAT_N(soma('ciot_total')), 'CIOT') + '</div>' +
    '<div class="panel" style="margin-top:18px;"><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:10px;">' +
    '<select id="fatMes" class="itil-select" onchange="fatCarrega(this.value)">' + opts + '</select>' +
    '<input id="fatFiltro" type="text" class="itil-select" style="min-width:240px;" placeholder="Filtrar por nome / CNPJ" value="' + esc(FAT_FILTRO) + '" oninput="FAT_FILTRO=this.value; fatRenderTabela();">' +
    '<button type="button" class="export-btn" onclick="fatCsv()">Exportar CSV</button><button type="button" class="export-btn" onclick="fatCarrega(FAT_MES)">Atualizar</button></div>' +
    '<div style="overflow:auto; max-height:60vh;"><table><thead><tr>' + cab + '</tr></thead><tbody>' + corpo + '</tbody></table></div></div>';
}
function fatRenderTabela() {
  const sel = document.getElementById('fatFiltro'), pos = sel ? sel.selectionStart : 0;
  fatRender();
  const i = document.getElementById('fatFiltro'); if (i) { i.focus(); try { i.setSelectionRange(pos, pos); } catch (e) {} }
}
function fatCsv() {
  if (!FAT || !FAT.colunas) return;
  const aspas = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const csv = [FAT.colunas.map(aspas).join(';')].concat(fatLinhas().map(r => FAT.colunas.map(c => aspas(r[c])).join(';'))).join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'faturamento_' + FAT_MES + '.csv'; document.body.appendChild(a); a.click(); a.remove();
}
"""
