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

// --- Faturamento mes a mes (dados enviados pela rotina diaria das 09:00 e guardados no Vercel Blob; nada fica no git) ---
var FAT = null, FAT_MES = '', FAT_FILTRO = '';
var FAT_N = v => Number(v || 0).toLocaleString('pt-BR');
var FAT_TIPOS = [['cte', 'CT-e', '#2563eb'], ['nfse', 'NFS-e', '#16a34a'], ['mdfe', 'MDF-e', '#f59e0b'], ['gnre', 'GNRE', '#9333ea'], ['ciot', 'CIOT', '#e11d48']];
var FAT_COLS = [['nome', 'Cliente'], ['cnpj', 'CNPJ matriz'], ['cte', 'CT-e'], ['nfse', 'NFS-e'], ['mdfe', 'MDF-e'], ['gnre', 'GNRE'], ['pix', 'GNRE PIX'], ['ciot', 'CIOT'], ['sist', 'Sistêmico'], ['docs', 'Total docs'], ['receb', 'Recebimentos']];
var FAT_NUM = {cte: 1, nfse: 1, mdfe: 1, gnre: 1, pix: 1, ciot: 1, sist: 1, docs: 1, receb: 1};
function fatRotuloMes(m) { return m ? m.slice(5) + '/' + m.slice(0, 4) : ''; }
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
async function fatCarrega() {
  const box = document.getElementById('fatCorpo');
  box.innerHTML = '<div class="panel"><div class="panel-sub">Carregando o faturamento...</div></div>';
  try {
    const r = await fetch('/api/faturamento', { headers: { 'Authorization': 'Bearer ' + cfgToken() } });
    const d = await r.json().catch(() => ({}));
    if (r.status === 401) { cfgGuardaToken(''); fatTelaSenha(d.erro || ''); return; }
    if (!r.ok) { box.innerHTML = '<div class="panel"><div class="panel-sub" style="color:var(--danger);">' + esc(d.erro || 'Não foi possível carregar o faturamento.') + '</div><div style="margin-top:10px;"><button type="button" class="export-btn" onclick="fatCarrega()">Tentar de novo</button></div></div>'; return; }
    FAT = d;
    const ms = d.meses || [];
    if (!FAT_MES || ms.indexOf(FAT_MES) === -1) FAT_MES = ms.length ? ms[ms.length - 1] : '';
    fatRender();
  } catch (e) { box.innerHTML = '<div class="panel"><div class="panel-sub" style="color:var(--danger);">Falha de conexão ao carregar o faturamento.</div></div>'; }
}
function fatPorMes() {
  const o = {};
  (FAT.dados || []).forEach(r => {
    const m = o[r.mes] = o[r.mes] || { mes: r.mes, clientes: 0, cte: 0, nfse: 0, mdfe: 0, gnre: 0, ciot: 0, sist: 0, docs: 0, receb: 0 };
    m.clientes++; ['cte', 'nfse', 'mdfe', 'gnre', 'ciot', 'sist', 'docs', 'receb'].forEach(k => { m[k] += Number(r[k] || 0); });
  });
  return (FAT.meses || []).map(m => o[m] || { mes: m, clientes: 0, cte: 0, nfse: 0, mdfe: 0, gnre: 0, ciot: 0, sist: 0, docs: 0, receb: 0 });
}
function fatLinhas() {
  const t = (FAT_FILTRO || '').toLowerCase().trim(), dig = t.replace(/\D/g, '');
  return (FAT.dados || []).filter(r => {
    if (r.mes !== FAT_MES) return false;
    if (!t) return true;
    return String(r.nome || '').toLowerCase().indexOf(t) !== -1 || (dig.length >= 3 && String(r.cnpj || '').replace(/\D/g, '').indexOf(dig) !== -1);
  });
}
// Grafico de barras empilhadas (SVG): documentos por tipo, mes a mes.
function fatGraficoMeses(pm) {
  const W = 900, H = 260, ml = 56, mr = 10, mt = 12, mb = 38, n = pm.length || 1;
  const tot = pm.map(m => FAT_TIPOS.reduce((s, t) => s + m[t[0]], 0)), max = Math.max.apply(null, tot.concat([1]));
  const passo = Math.pow(10, Math.floor(Math.log10(max))), topo = Math.ceil(max / passo) * passo;
  const bw = (W - ml - mr) / n, larg = Math.min(34, bw * 0.7);
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%; height:auto; display:block;" role="img" aria-label="Documentos por mês">';
  for (let g = 0; g <= 4; g++) {
    const y = mt + (H - mt - mb) * (1 - g / 4), v = topo * g / 4;
    s += '<line x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y + '" y2="' + y + '" stroke="currentColor" stroke-opacity=".12"/><text x="' + (ml - 6) + '" y="' + (y + 4) + '" text-anchor="end" font-size="10" fill="currentColor" fill-opacity=".65">' + (v >= 1e6 ? (v / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' mi' : v >= 1e3 ? Math.round(v / 1e3) + ' mil' : v) + '</text>';
  }
  pm.forEach((m, i) => {
    const x = ml + bw * i + (bw - larg) / 2; let acc = 0;
    FAT_TIPOS.forEach(t => {
      const h = (H - mt - mb) * m[t[0]] / topo; acc += h;
      if (h > 0) s += '<rect x="' + x + '" y="' + (H - mb - acc) + '" width="' + larg + '" height="' + h + '" fill="' + t[2] + '"><title>' + fatRotuloMes(m.mes) + ' · ' + t[1] + ': ' + FAT_N(m[t[0]]) + '</title></rect>';
    });
    if (n <= 12 || i % 2 === 0 || m.mes === FAT_MES) s += '<text x="' + (x + larg / 2) + '" y="' + (H - mb + 14) + '" text-anchor="middle" font-size="9.5" fill="currentColor" fill-opacity="' + (m.mes === FAT_MES ? 1 : .65) + '"' + (m.mes === FAT_MES ? ' font-weight="700"' : '') + '>' + m.mes.slice(5) + '/' + m.mes.slice(2, 4) + '</text>';
  });
  return s + '</svg>';
}
// Barras horizontais: maiores clientes do mes selecionado.
function fatGraficoTop(lin) {
  const top = lin.slice().sort((a, b) => b.docs - a.docs).slice(0, 10), max = Math.max.apply(null, top.map(r => r.docs).concat([1]));
  if (!top.length) return '<div class="empty-msg">Sem dados neste mês.</div>';
  return top.map(r => '<div style="display:flex; align-items:center; gap:8px; margin:5px 0; font-size:12px;"><div style="width:34%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="' + esc(r.nome) + '">' + esc(r.nome) + '</div>' +
    '<div style="flex:1; background:rgba(127,127,127,.15); border-radius:4px; height:14px;"><div style="width:' + (100 * r.docs / max) + '%; height:100%; background:#2563eb; border-radius:4px;"></div></div><div style="width:84px; text-align:right;">' + FAT_N(r.docs) + '</div></div>').join('');
}
function fatRender() {
  if (!FAT) return;
  const box = document.getElementById('fatCorpo');
  if (!(FAT.dados || []).length) { box.innerHTML = '<div class="panel"><div class="panel-sub">Ainda não há dados de faturamento. A rotina diária das 09:00 envia os dados; assim que ela rodar, eles aparecem aqui.</div></div>'; return; }
  const pm = fatPorMes(), atual = pm.find(m => m.mes === FAT_MES) || pm[pm.length - 1], lin = fatLinhas();
  const ant = pm[pm.indexOf(atual) - 1];
  const kpi = (v, t) => '<div class="kpi"><div class="value">' + v + '</div><div class="kpi-label">' + t + '</div></div>';
  const opts = (FAT.meses || []).slice().reverse().map(m => '<option value="' + m + '"' + (m === FAT_MES ? ' selected' : '') + '>' + fatRotuloMes(m) + '</option>').join('');
  const quando = FAT.atualizado_em ? new Date(FAT.atualizado_em).toLocaleString('pt-BR') : '-';
  const variacao = ant && ant.docs ? ' <span style="font-size:11px; opacity:.75;">(' + (atual.docs >= ant.docs ? '+' : '') + ((atual.docs - ant.docs) * 100 / ant.docs).toFixed(1).replace('.', ',') + '% vs mês anterior)</span>' : '';
  const legenda = FAT_TIPOS.map(t => '<span style="display:inline-flex; align-items:center; gap:4px; margin-right:12px; font-size:12px;"><i style="width:10px; height:10px; background:' + t[2] + '; display:inline-block; border-radius:2px;"></i>' + t[1] + '</span>').join('');
  const cabM = ['Mês', 'Clientes'].concat(FAT_TIPOS.map(t => t[1])).concat(['Sistêmico', 'Total docs']).map((c, i) => '<th' + (i ? ' style="text-align:right;"' : '') + '>' + c + '</th>').join('');
  const corpoM = pm.slice().reverse().map(m => '<tr' + (m.mes === FAT_MES ? ' style="font-weight:700;"' : '') + '><td>' + fatRotuloMes(m.mes) + '</td><td style="text-align:right;">' + FAT_N(m.clientes) + '</td>' + FAT_TIPOS.map(t => '<td style="text-align:right;">' + FAT_N(m[t[0]]) + '</td>').join('') + '<td style="text-align:right;">' + FAT_N(m.sist) + '</td><td style="text-align:right;">' + FAT_N(m.docs) + '</td></tr>').join('');
  const cab = FAT_COLS.map(c => '<th' + (FAT_NUM[c[0]] ? ' style="text-align:right;"' : '') + '>' + c[1] + '</th>').join('');
  const corpo = lin.map(r => '<tr>' + FAT_COLS.map(c => { const v = r[c[0]]; return FAT_NUM[c[0]] ? '<td style="text-align:right;">' + FAT_N(v) + '</td>' : '<td>' + esc(v == null ? '' : String(v)) + '</td>'; }).join('') + '</tr>').join('') || '<tr><td colspan="' + FAT_COLS.length + '" class="empty-msg">Nenhum registro.</td></tr>';
  box.innerHTML =
    '<div class="panel-sub" style="margin-bottom:12px;">Dados do painel de faturamento do EmiteAí, mês a mês desde jan/2025. Atualizado automaticamente todo dia às 09:00 · última atualização: <b>' + esc(quando) + '</b>. O mês corrente é acumulado até d-1.</div>' +
    '<div class="panel"><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;"><b>Mês:</b><select id="fatMes" class="itil-select" onchange="FAT_MES=this.value; fatRender();">' + opts + '</select><button type="button" class="export-btn" onclick="fatCarrega()">Recarregar</button></div></div>' +
    '<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); margin-top:14px;">' + kpi(FAT_N(atual.clientes), 'Clientes') + kpi(FAT_N(atual.docs) + variacao, 'Total de documentos') + FAT_TIPOS.map(t => kpi(FAT_N(atual[t[0]]), t[1])).join('') + kpi(FAT_N(atual.sist), 'Sistêmico') + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Documentos por mês</h2><div style="margin:6px 0 8px;">' + legenda + '</div>' + fatGraficoMeses(pm) + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Maiores clientes em ' + fatRotuloMes(FAT_MES) + '</h2>' + fatGraficoTop(fatLinhasMes()) + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Resumo mês a mês</h2><div style="overflow:auto;"><table><thead><tr>' + cabM + '</tr></thead><tbody>' + corpoM + '</tbody></table></div><div style="margin-top:10px;"><button type="button" class="export-btn" onclick="fatCsvMeses()">Exportar resumo (CSV)</button></div></div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Por cliente em ' + fatRotuloMes(FAT_MES) + '</h2><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 10px;">' +
    '<input id="fatFiltro" type="text" class="itil-select" style="min-width:240px;" placeholder="Filtrar por nome / CNPJ" value="' + esc(FAT_FILTRO) + '" oninput="FAT_FILTRO=this.value; fatRenderTabela();">' +
    '<button type="button" class="export-btn" onclick="fatCsv()">Exportar mês (CSV)</button><button type="button" class="export-btn" onclick="fatCsv(true)">Exportar tudo (CSV)</button></div>' +
    '<div style="overflow:auto; max-height:60vh;"><table><thead><tr>' + cab + '</tr></thead><tbody>' + corpo + '</tbody></table></div></div>';
}
function fatLinhasMes() { return (FAT.dados || []).filter(r => r.mes === FAT_MES); }
function fatRenderTabela() {
  const sel = document.getElementById('fatFiltro'), pos = sel ? sel.selectionStart : 0;
  fatRender();
  const i = document.getElementById('fatFiltro'); if (i) { i.focus(); try { i.setSelectionRange(pos, pos); } catch (e) {} }
}
function fatBaixa(nome, linhas) {
  const aspas = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const csv = linhas.map(l => l.map(aspas).join(';')).join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = nome; document.body.appendChild(a); a.click(); a.remove();
}
function fatCsv(tudo) {
  if (!FAT) return;
  const lista = tudo ? (FAT.dados || []) : fatLinhas();
  fatBaixa('faturamento_' + (tudo ? 'completo' : FAT_MES) + '.csv', [['Mês'].concat(FAT_COLS.map(c => c[1]))].concat(lista.map(r => [r.mes].concat(FAT_COLS.map(c => r[c[0]])))));
}
function fatCsvMeses() {
  if (!FAT) return;
  fatBaixa('faturamento_mes_a_mes.csv', [['Mês', 'Clientes'].concat(FAT_TIPOS.map(t => t[1])).concat(['Sistêmico', 'Total docs'])].concat(fatPorMes().map(m => [m.mes, m.clientes].concat(FAT_TIPOS.map(t => m[t[0]])).concat([m.sist, m.docs]))));
}
"""
