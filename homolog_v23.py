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
var FAT_NUM = {clientes: 1, cte: 1, nfse: 1, mdfe: 1, gnre: 1, pix: 1, ciot: 1, sist: 1, docs: 1, receb: 1};
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
  fatEstilo();
  const box = document.getElementById('fatCorpo');
  if (!(FAT.dados || []).length) { box.innerHTML = '<div class="panel"><div class="panel-sub">Ainda não há dados de faturamento. A rotina diária das 09:00 envia os dados; assim que ela rodar, eles aparecem aqui.</div></div>'; return; }
  const pm = fatPorMes(), atual = pm.find(m => m.mes === FAT_MES) || pm[pm.length - 1], lin = fatLinhas();
  const kpi = (v, t) => '<div class="kpi"><div class="value">' + v + '</div><div class="kpi-label">' + t + '</div></div>';
  const opts = (FAT.meses || []).slice().reverse().map(m => '<option value="' + m + '"' + (m === FAT_MES ? ' selected' : '') + '>' + fatRotuloMes(m) + '</option>').join('');
  const quando = FAT.atualizado_em ? new Date(FAT.atualizado_em).toLocaleString('pt-BR') : '-';
  const legenda = FAT_TIPOS.map(t => '<span style="display:inline-flex; align-items:center; gap:4px; margin-right:12px; font-size:12px;"><i style="width:10px; height:10px; background:' + t[2] + '; display:inline-block; border-radius:2px;"></i>' + t[1] + '</span>').join('');
  box.innerHTML =
    '<div class="panel-sub" style="margin-bottom:12px;">Dados do painel de faturamento do EmiteAí, mês a mês desde jan/2025. Atualizado automaticamente todo dia às 09:00 · última atualização: <b>' + esc(quando) + '</b>. O mês corrente é acumulado até d-1.</div>' +
    '<div class="panel"><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;"><b>Mês:</b><select id="fatMes" class="itil-select" onchange="FAT_MES=this.value; fatRender();">' + opts + '</select><button type="button" class="export-btn" onclick="fatCarrega()">Recarregar</button></div></div>' +
    '<div style="margin-top:14px;">' + fatHeroHtml(pm, atual) + '</div>' +
    '<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); margin-top:14px;">' + kpi(FAT_N(atual.clientes), 'Clientes') + FAT_TIPOS.map(t => kpi(FAT_N(atual[t[0]]), t[1])).join('') + kpi(FAT_N(atual.sist), 'Sistêmico') + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Documentos por mês</h2><div style="margin:6px 0 8px;">' + legenda + '</div>' + fatGraficoMeses(pm) + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Maiores clientes em ' + fatRotuloMes(FAT_MES) + '</h2>' + fatGraficoTop(fatLinhasMes()) + '</div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Resumo mês a mês</h2><div id="fatTabM">' + fatTabelaHtml('m', FAT_MCOLS, pm) + '</div><div style="margin-top:10px;"><button type="button" class="export-btn" onclick="fatCsvMeses()">Exportar resumo (CSV)</button></div></div>' +
    '<div class="panel" style="margin-top:18px;"><h2>Por cliente em ' + fatRotuloMes(FAT_MES) + '</h2><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 10px;">' +
    '<input id="fatFiltro" type="text" class="itil-select" style="min-width:240px;" placeholder="Filtrar por nome / CNPJ" value="' + esc(FAT_FILTRO) + '" oninput="FAT_FILTRO=this.value; fatRedesenha(\'c\');">' +
    '<button type="button" class="export-btn" onclick="fatCsv()">Exportar mês (CSV)</button><button type="button" class="export-btn" onclick="fatCsv(true)">Exportar tudo (CSV)</button></div>' +
    '<div id="fatTabC">' + fatTabelaHtml('c', FAT_COLS, lin) + '</div></div>';
}
function fatLinhasMes() { return (FAT.dados || []).filter(r => r.mes === FAT_MES); }
// --- Tabelas do Faturamento: ordenar clicando no titulo, modo ranking (medalhas, barras, animacoes), titulos centralizados ---
var FAT_ORD = { c: { col: 'docs', dir: -1 }, m: { col: 'mes', dir: -1 } }, FAT_RANK = { c: false, m: false };
var FAT_TEXTO = { nome: 1, cnpj: 1, mes: 1 };
var FAT_MCOLS = [['mes', 'Mês'], ['clientes', 'Clientes'], ['cte', 'CT-e'], ['nfse', 'NFS-e'], ['mdfe', 'MDF-e'], ['gnre', 'GNRE'], ['ciot', 'CIOT'], ['sist', 'Sistêmico'], ['docs', 'Total docs']];
function fatEstilo() {
  if (document.getElementById('fatEstilo')) return;
  const st = document.createElement('style'); st.id = 'fatEstilo';
  st.textContent =
    '.fat-tab{width:100%; border-collapse:collapse;}' +
    '.fat-tab th,.fat-tab td{text-align:center; vertical-align:middle; padding:9px 14px; white-space:nowrap;}' +
    '.fat-tab th.fat-esq,.fat-tab td.fat-esq{text-align:left;}' +
    '.fat-tab th.fat-ord{cursor:pointer; user-select:none; transition:background .15s;}' +
    '.fat-tab th.fat-ord:hover{background:rgba(37,99,235,.12);}' +
    '.fat-seta{display:inline-block; width:12px; margin-left:5px; font-size:10px; opacity:.3;}' +
    '.fat-tab th.fat-on .fat-seta{opacity:1; color:#2563eb;}' +
    '.fat-tab tbody tr{transition:background .15s;}' +
    '.fat-tab tbody tr:hover{background:rgba(37,99,235,.08);}' +
    '.fat-rk tbody tr{animation:fatEntra .45s ease both;}' +
    '@keyframes fatEntra{from{opacity:0; transform:translateY(8px);}to{opacity:1; transform:none;}}' +
    '.fat-pos{display:inline-flex; align-items:center; justify-content:center; min-width:30px; height:30px; border-radius:50%; font-weight:700; font-size:12px; background:rgba(127,127,127,.18);}' +
    '.fat-pos.p1{background:linear-gradient(135deg,#fde047,#f59e0b); color:#422006; font-size:16px; animation:fatPulso 1.8s infinite;}' +
    '.fat-pos.p2{background:linear-gradient(135deg,#e5e7eb,#9ca3af); color:#111827; font-size:16px;}' +
    '.fat-pos.p3{background:linear-gradient(135deg,#fdba74,#c2410c); color:#fff; font-size:16px;}' +
    '@keyframes fatPulso{0%{box-shadow:0 0 0 0 rgba(245,158,11,.55);}70%{box-shadow:0 0 0 9px rgba(245,158,11,0);}100%{box-shadow:0 0 0 0 rgba(245,158,11,0);}}' +
    '.fat-rk tr.r1 td{background:rgba(245,158,11,.13);}.fat-rk tr.r2 td{background:rgba(156,163,175,.14);}.fat-rk tr.r3 td{background:rgba(194,65,12,.10);}' +
    '.fat-rk tr.r1 td,.fat-rk tr.r2 td,.fat-rk tr.r3 td{font-weight:700;}' +
    '.fat-cel{position:relative;}.fat-cel>span{position:relative;}' +
    '.fat-bar{position:absolute; left:0; top:18%; bottom:18%; width:var(--w); background:linear-gradient(90deg,rgba(37,99,235,.34),rgba(37,99,235,.06)); border-radius:0 6px 6px 0; transform-origin:left; animation:fatCresce .9s ease both; pointer-events:none;}' +
    '@keyframes fatCresce{from{transform:scaleX(0);}to{transform:scaleX(1);}}' +
    '.fat-ativo{background:#2563eb !important; color:#fff !important;}' +
    '.fat-hero-topo{display:flex; flex-wrap:wrap; gap:22px; align-items:center; justify-content:space-between;}' +
    '.fat-hero-t{font-size:12px; letter-spacing:.06em; text-transform:uppercase; opacity:.7; font-weight:700;}' +
    '.fat-hero-v{font-size:64px; line-height:1.05; font-weight:800; margin:4px 0 8px; background:linear-gradient(135deg,#2563eb,#9333ea); -webkit-background-clip:text; background-clip:text; color:transparent; animation:fatPop .6s ease both;}' +
    '@keyframes fatPop{from{opacity:0; transform:scale(.85);}to{opacity:1; transform:none;}}' +
    '.fat-pill{display:inline-block; padding:4px 12px; border-radius:999px; font-size:13px; font-weight:700; background:rgba(127,127,127,.18);}' +
    '.fat-pill.sobe{background:rgba(22,163,74,.16); color:#16a34a;}.fat-pill.desce{background:rgba(220,38,38,.14); color:#dc2626;}' +
    '.fat-hero-dir{display:grid; grid-template-columns:repeat(2,minmax(150px,1fr)); gap:10px; flex:1; max-width:520px;}' +
    '.fat-mini{border:1px solid rgba(127,127,127,.25); border-radius:12px; padding:10px 14px;}' +
    '.fat-mini-v{font-size:22px; font-weight:800;}.fat-mini-t{font-size:12px; font-weight:600; opacity:.85;}.fat-mini-s{font-size:10.5px; opacity:.6; margin-top:2px;}' +
    '.fat-barh{height:100%; border-radius:6px; transform-origin:left; animation:fatCresce .9s ease both;}' +
    '.fat-barra{transform-box:fill-box; transform-origin:bottom; animation:fatSobe .7s ease both;}' +
    '@keyframes fatSobe{from{transform:scaleY(0);}to{transform:scaleY(1);}}';
  document.head.appendChild(st);
}
function fatOrdena(lista, tab) {
  const o = FAT_ORD[tab], d = o.dir, col = o.col;
  return lista.slice().sort((a, b) => {
    const x = a[col], y = b[col];
    const r = FAT_TEXTO[col] ? String(x == null ? '' : x).localeCompare(String(y == null ? '' : y), 'pt-BR', { numeric: true }) : Number(x || 0) - Number(y || 0);
    return r * d || String(a.nome || a.mes).localeCompare(String(b.nome || b.mes), 'pt-BR');
  });
}
function fatTabelaHtml(tab, cols, lista) {
  const o = FAT_ORD[tab], rk = FAT_RANK[tab], metrica = FAT_TEXTO[o.col] ? 'docs' : o.col;
  const ord = fatOrdena(lista, tab), pos = new Map();
  lista.slice().sort((a, b) => Number(b[metrica] || 0) - Number(a[metrica] || 0)).forEach((r, i) => pos.set(r, i + 1));
  const maxv = Math.max.apply(null, lista.map(r => Number(r[metrica] || 0)).concat([1]));
  const medalha = ['', '🥇', '🥈', '🥉'];
  const cab = (rk ? '<th>#</th>' : '') + cols.map(c => {
    const on = o.col === c[0];
    return '<th class="fat-ord' + (on ? ' fat-on' : '') + (c[0] === 'nome' ? ' fat-esq' : '') + '" onclick="fatClicaCol(\'' + tab + '\',\'' + c[0] + '\')" title="Ordenar por ' + esc(c[1]) + '">' + esc(c[1]) + '<span class="fat-seta">' + (on ? (o.dir > 0 ? '▲' : '▼') : '↕') + '</span></th>';
  }).join('');
  const corpo = ord.map((r, i) => {
    const p = pos.get(r), cls = rk && p <= 3 ? ' class="r' + p + '"' : '';
    const dest = tab === 'm' && r.mes === FAT_MES ? ' style="outline:2px solid rgba(37,99,235,.45); outline-offset:-2px;"' : '';
    const atraso = rk ? ' style="animation-delay:' + Math.min(i, 24) * 35 + 'ms;"' : '';
    const tds = cols.map(c => {
      const v = r[c[0]];
      if (c[0] === 'nome') return '<td class="fat-esq">' + esc(v == null ? '' : String(v)) + '</td>';
      if (c[0] === 'mes') return '<td>' + fatRotuloMes(v) + '</td>';
      if (c[0] === 'cnpj') return '<td>' + esc(v == null ? '' : String(v)) + '</td>';
      if (rk && c[0] === metrica) return '<td class="fat-cel"><i class="fat-bar" style="--w:' + (100 * Number(v || 0) / maxv).toFixed(1) + '%"></i><span>' + FAT_N(v) + '</span></td>';
      return '<td>' + FAT_N(v) + '</td>';
    }).join('');
    const est = (rk ? 'animation-delay:' + Math.min(i, 24) * 35 + 'ms;' : '') + (tab === 'm' && r.mes === FAT_MES ? 'outline:2px solid rgba(37,99,235,.45); outline-offset:-2px;' : '');
    return '<tr' + (rk && p <= 3 ? ' class="r' + p + '"' : '') + (est ? ' style="' + est + '"' : '') + '>' + (rk ? '<td><span class="fat-pos' + (p <= 3 ? ' p' + p : '') + '">' + (p <= 3 ? medalha[p] : p) + '</span></td>' : '') + tds + '</tr>';
  }).join('') || '<tr><td colspan="' + (cols.length + 1) + '" class="empty-msg">Nenhum registro.</td></tr>';
  return '<div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:0 0 10px;">' +
    '<button type="button" id="fatRk' + tab + '" class="export-btn' + (rk ? ' fat-ativo' : '') + '" onclick="fatRanking(\'' + tab + '\',!FAT_RANK.' + tab + ')">🏆 Ranking' + (rk ? ' (ligado)' : '') + '</button>' +
    '<span style="font-size:12px; opacity:.75;">Clique no título da coluna para ordenar (crescente ↔ decrescente).' + (rk ? ' Ranking pela coluna <b>' + esc((cols.find(c => c[0] === metrica) || [0, metrica])[1]) + '</b>.' : '') + '</span></div>' +
    '<div style="overflow:auto;' + (tab === 'c' ? ' max-height:60vh;' : '') + '"><table class="fat-tab' + (rk ? ' fat-rk' : '') + '"><thead><tr>' + cab + '</tr></thead><tbody>' + corpo + '</tbody></table></div>';
}
function fatClicaCol(tab, col) {
  const o = FAT_ORD[tab];
  if (o.col === col) o.dir = -o.dir; else { o.col = col; o.dir = FAT_TEXTO[col] ? 1 : -1; }
  fatRedesenha(tab);
}
function fatRanking(tab, on) { FAT_RANK[tab] = on; fatRedesenha(tab); }
function fatRedesenha(tab) {
  const el = document.getElementById(tab === 'c' ? 'fatTabC' : 'fatTabM'); if (!el || !FAT) return;
  el.innerHTML = tab === 'c' ? fatTabelaHtml('c', FAT_COLS, fatLinhas()) : fatTabelaHtml('m', FAT_MCOLS, fatPorMes());
}
// --- Indicador Emissoes por chamado: card visual + comparativo por periodo (mensal, trimestral, anual) contra o mesmo periodo do ano anterior ---
var FAT_PER = 'm';
function fatEmis(m) { return m ? m.cte + m.nfse + m.sist + m.gnre : 0; }
function fatCham(k) { return (typeof CHAMADOS_ABERTOS !== 'undefined' && CHAMADOS_ABERTOS[k]) || 0; }
function fatAnoAnt(k) { return (parseInt(k.slice(0, 4), 10) - 1) + k.slice(4); }
function fatPct(a, b) { return b ? (a >= b ? '+' : '') + ((a - b) * 100 / b).toFixed(1).replace('.', ',') + '%' : null; }
// Agrupa os meses por mes / trimestre / ano e calcula emissoes por chamado (soma de emissoes / soma de chamados) e o mesmo periodo do ano anterior.
function fatSerieRazao(per) {
  const pm = fatPorMes(), por = {}; pm.forEach(m => { por[m.mes] = m; });
  const grupos = [], idx = {};
  pm.forEach(m => {
    const a = m.mes.slice(0, 4), mm = parseInt(m.mes.slice(5), 10), t = Math.floor((mm - 1) / 3) + 1;
    const k = per === 'm' ? m.mes : per === 't' ? a + 'T' + t : a;
    const l = per === 'm' ? m.mes.slice(5) + '/' + a.slice(2) : per === 't' ? t + 'º tri/' + a.slice(2) : a;
    if (!(k in idx)) { idx[k] = grupos.length; grupos.push({ k: k, l: l, meses: [], max: per === 'm' ? 1 : per === 't' ? 3 : 12 }); }
    grupos[idx[k]].meses.push(m.mes);
  });
  const calc = meses => {
    let e = 0, c = 0;
    meses.forEach(k => { if (por[k] && fatCham(k)) { e += fatEmis(por[k]); c += fatCham(k); } });
    return c ? { v: e / c, e: e, c: c } : null;
  };
  return grupos.map(g => {
    const a = calc(g.meses), p = calc(g.meses.map(fatAnoAnt));
    return { l: g.l, a: a, p: p, parcial: g.meses.length < g.max };
  }).filter(g => g.a);
}
function fatGraficoRazao(ser) {
  if (!ser.length) return '<div class="empty-msg">Sem dados de chamados para montar o comparativo.</div>';
  const W = 900, H = 300, ml = 52, mr = 10, mt = 22, mb = 52, n = ser.length;
  const max = Math.max.apply(null, ser.map(g => Math.max(g.a.v, g.p ? g.p.v : 0)).concat([1]));
  const passo = Math.pow(10, Math.floor(Math.log10(max))), topo = Math.ceil(max / passo) * passo;
  const bw = (W - ml - mr) / n, larg = Math.min(26, bw * 0.38), esc2 = v => (H - mt - mb) * v / topo;
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%; height:auto; display:block;" role="img" aria-label="Emissões por chamado">';
  for (let g = 0; g <= 4; g++) {
    const y = mt + (H - mt - mb) * (1 - g / 4);
    s += '<line x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y + '" y2="' + y + '" stroke="currentColor" stroke-opacity=".12"/><text x="' + (ml - 6) + '" y="' + (y + 4) + '" text-anchor="end" font-size="10" fill="currentColor" fill-opacity=".65">' + FAT_N(Math.round(topo * g / 4)) + '</text>';
  }
  ser.forEach((g, i) => {
    const cx = ml + bw * i + bw / 2, ha = esc2(g.a.v), hp = g.p ? esc2(g.p.v) : 0;
    const sobe = g.p ? g.a.v >= g.p.v : true, corA = g.p ? (sobe ? '#16a34a' : '#dc2626') : '#2563eb';
    const tit = g.l + (g.parcial ? ' (parcial)' : '') + ': ' + FAT_N(Math.round(g.a.v)) + ' emissões/chamado (' + FAT_N(g.a.e) + ' ÷ ' + FAT_N(g.a.c) + ')' + (g.p ? ' · ano anterior: ' + FAT_N(Math.round(g.p.v)) + ' (' + fatPct(g.a.v, g.p.v) + ')' : '');
    if (g.p) s += '<rect x="' + (cx - larg - 1) + '" y="' + (H - mb - hp) + '" width="' + larg + '" height="' + hp + '" rx="3" fill="#9ca3af" fill-opacity=".55"><title>' + esc(tit) + '</title></rect>';
    s += '<rect class="fat-barra" style="animation-delay:' + Math.min(i, 24) * 30 + 'ms" x="' + (g.p ? cx + 1 : cx - larg / 2) + '" y="' + (H - mb - ha) + '" width="' + larg + '" height="' + ha + '" rx="3" fill="' + corA + '"' + (g.parcial ? ' fill-opacity=".6" stroke="' + corA + '" stroke-dasharray="3 2"' : '') + '><title>' + esc(tit) + '</title></rect>';
    if (n <= 14) s += '<text x="' + (g.p ? cx + 1 + larg / 2 : cx) + '" y="' + (H - mb - ha - 5) + '" text-anchor="middle" font-size="10" font-weight="700" fill="currentColor">' + FAT_N(Math.round(g.a.v)) + '</text>';
    s += '<text x="' + cx + '" y="' + (H - mb + 15) + '" text-anchor="middle" font-size="10" fill="currentColor" fill-opacity=".75">' + g.l + (g.parcial ? '*' : '') + '</text>';
    if (g.p && n <= 14) s += '<text x="' + cx + '" y="' + (H - mb + 29) + '" text-anchor="middle" font-size="10" font-weight="700" fill="' + corA + '">' + (sobe ? '▲ ' : '▼ ') + fatPct(g.a.v, g.p.v).replace('+', '') + '</text>';
  });
  return s + '</svg>';
}
function fatRazaoHtml() {
  const btn = (p, t) => '<button type="button" class="export-btn fat-per' + (FAT_PER === p ? ' fat-ativo' : '') + '" onclick="fatPeriodo(\'' + p + '\')">' + t + '</button>';
  const ser = fatSerieRazao(FAT_PER);
  const nota = FAT_PER === 'm' ? 'Cada mês contra o mesmo mês do ano anterior.' : FAT_PER === 't' ? 'Cada trimestre contra o mesmo trimestre do ano anterior. * = trimestre incompleto (compara com os mesmos meses do ano anterior).' : 'Cada ano contra o ano anterior. * = ano em andamento (compara com os mesmos meses do ano anterior).';
  return '<div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:14px 0 6px;">' + btn('m', 'Mensal') + btn('t', 'Trimestral') + btn('a', 'Anual') +
    '<span style="margin-left:8px; font-size:12px; opacity:.75;">' + nota + '</span></div>' +
    '<div style="margin:2px 0 6px; font-size:12px;"><span style="display:inline-flex; align-items:center; gap:4px; margin-right:14px;"><i style="width:10px; height:10px; background:#9ca3af; opacity:.7; display:inline-block; border-radius:2px;"></i>Ano anterior</span>' +
    '<span style="display:inline-flex; align-items:center; gap:4px; margin-right:14px;"><i style="width:10px; height:10px; background:#16a34a; display:inline-block; border-radius:2px;"></i>Período atual acima</span>' +
    '<span style="display:inline-flex; align-items:center; gap:4px;"><i style="width:10px; height:10px; background:#dc2626; display:inline-block; border-radius:2px;"></i>Período atual abaixo</span></div>' + fatGraficoRazao(ser);
}
function fatPeriodo(per) { FAT_PER = per; const el = document.getElementById('fatRazao'); if (el) el.innerHTML = fatRazaoHtml(); }
// Card grande do indicador, do mes escolhido.
function fatHeroHtml(pm, atual) {
  const por = {}; pm.forEach(m => { por[m.mes] = m; });
  const ant = fatAnoAnt(FAT_MES), mAA = por[ant], chA = fatCham(FAT_MES), chB = fatCham(ant);
  const razA = chA ? fatEmis(atual) / chA : 0, razB = chB && mAA ? fatEmis(mAA) / chB : 0;
  const delta = razB && razA ? fatPct(razA, razB) : null, sobe = razA >= razB;
  const maxv = Math.max(razA, razB, 1);
  const mini = (t, v, sub) => '<div class="fat-mini"><div class="fat-mini-v">' + v + '</div><div class="fat-mini-t">' + t + '</div>' + (sub ? '<div class="fat-mini-s">' + sub + '</div>' : '') + '</div>';
  const barra = (t, v, cor) => '<div style="display:flex; align-items:center; gap:8px; margin:5px 0; font-size:12px;"><div style="width:96px;">' + t + '</div><div style="flex:1; background:rgba(127,127,127,.16); border-radius:6px; height:12px; overflow:hidden;"><div class="fat-barh" style="width:' + (100 * v / maxv).toFixed(1) + '%; background:' + cor + ';"></div></div><div style="width:56px; text-align:right; font-weight:700;">' + FAT_N(Math.round(v)) + '</div></div>';
  return '<div class="panel fat-hero"><div class="fat-hero-topo"><div class="fat-hero-esq">' +
    '<div class="fat-hero-t">Emissões por chamado · ' + fatRotuloMes(FAT_MES) + '</div>' +
    '<div class="fat-hero-v">' + (chA ? FAT_N(Math.round(razA)) : '-') + '</div>' +
    (delta ? '<span class="fat-pill ' + (sobe ? 'sobe' : 'desce') + '">' + (sobe ? '▲' : '▼') + ' ' + delta.replace('+', '') + ' vs ' + fatRotuloMes(ant) + '</span>' : '<span class="fat-pill">' + (chA ? 'sem ' + fatRotuloMes(ant) + ' para comparar' : 'sem chamados deste mês') + '</span>') +
    '</div><div class="fat-hero-dir">' + mini('Emissões', FAT_N(fatEmis(atual)), 'CT-e + NFS-e + Sistêmico + GNRE') + mini('Chamados abertos', chA ? FAT_N(chA) : '-', 'Suporte, sem cancelados') + '</div></div>' +
    (razA ? '<div style="margin-top:14px; max-width:520px;">' + barra(fatRotuloMes(FAT_MES), razA, sobe || !razB ? '#16a34a' : '#dc2626') + (razB ? barra(fatRotuloMes(ant), razB, '#9ca3af') : '') + '</div>' : '') +
    '<h2 style="margin-top:18px;">Comparativo de emissões por chamado</h2><div id="fatRazao">' + fatRazaoHtml() + '</div></div>';
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
