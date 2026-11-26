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
  const porMes = {}; pm.forEach(m => { porMes[m.mes] = m; });
  const pct = (a, b) => b ? (a >= b ? '+' : '') + ((a - b) * 100 / b).toFixed(1).replace('.', ',') + '%' : null;
  const cor = (a, b) => !b ? '' : (a >= b ? 'var(--success, #16a34a)' : 'var(--danger, #dc2626)');
  const sub = (txt, a, b) => txt ? '<div style="font-size:11px; margin-top:4px; opacity:.9; color:' + cor(a, b) + ';">' + txt + '</div>' : '';
  const kpi = (v, t, extra) => '<div class="kpi"><div class="value">' + v + '</div><div class="kpi-label">' + t + '</div>' + (extra || '') + '</div>';
  // Mesmo mes do ano anterior
  const anoAnt = (parseInt(FAT_MES.slice(0, 4), 10) - 1) + FAT_MES.slice(4), mAA = porMes[anoAnt];
  const cDocs = kpi(FAT_N(atual.docs), 'Total de documentos', mAA ? sub(pct(atual.docs, mAA.docs) + ' vs ' + fatRotuloMes(anoAnt) + ' (' + FAT_N(mAA.docs) + ')', atual.docs, mAA.docs) : sub('sem dados de ' + fatRotuloMes(anoAnt)));
  // Media mensal do trimestre do mes escolhido x trimestre anterior (meses que tem dados)
  const ano = parseInt(FAT_MES.slice(0, 4), 10), mes = parseInt(FAT_MES.slice(5), 10), tri = Math.floor((mes - 1) / 3);
  const doTri = (a, t) => [1, 2, 3].map(i => a + '-' + String(t * 3 + i).padStart(2, '0')).filter(k => porMes[k] && k <= FAT_MES);
  const triAnt = tri === 0 ? [ano - 1, 3] : [ano, tri - 1];
  const kA = doTri(ano, tri), kP = doTri(triAnt[0], triAnt[1]);
  const media = ks => ks.length ? ks.reduce((s, k) => s + porMes[k].docs, 0) / ks.length : 0;
  const mediaA = media(kA), mediaP = media(kP);
  const cTri = kpi(FAT_N(Math.round(mediaA)), 'Média/mês do ' + (tri + 1) + 'º tri/' + ano + (kA.length < 3 ? ' (' + kA.length + ' mês' + (kA.length > 1 ? 'es' : '') + ')' : ''),
    mediaP ? sub(pct(mediaA, mediaP) + ' vs ' + (triAnt[1] + 1) + 'º tri/' + triAnt[0] + ' (média ' + FAT_N(Math.round(mediaP)) + ')', mediaA, mediaP) : sub('sem trimestre anterior'));
  // Emissoes por chamado: (CT-e + NFS-e + Sistemico + GNRE) / chamados abertos do mes (mesma regra da Reuniao Mensal)
  const emis = m => m ? m.cte + m.nfse + m.sist + m.gnre : 0;
  const chamDe = k => (typeof CHAMADOS_ABERTOS !== 'undefined' && CHAMADOS_ABERTOS[k]) || 0;
  const chA = chamDe(FAT_MES), chB = chamDe(anoAnt);
  const razA = chA ? emis(atual) / chA : 0, razB = chB && mAA ? emis(mAA) / chB : 0;
  const cChamado = kpi(chA ? FAT_N(Math.round(razA)) : '-', 'Emissões por chamado',
    chA ? sub(FAT_N(emis(atual)) + ' emissões ÷ ' + FAT_N(chA) + ' chamados abertos' + (razB ? '<br>' + pct(razA, razB) + ' vs ' + fatRotuloMes(anoAnt) + ' (' + FAT_N(Math.round(razB)) + ')' : ''), razA, razB) : sub('sem chamados deste mês'));
  const opts = (FAT.meses || []).slice().reverse().map(m => '<option value="' + m + '"' + (m === FAT_MES ? ' selected' : '') + '>' + fatRotuloMes(m) + '</option>').join('');
  const quando = FAT.atualizado_em ? new Date(FAT.atualizado_em).toLocaleString('pt-BR') : '-';
  const legenda = FAT_TIPOS.map(t => '<span style="display:inline-flex; align-items:center; gap:4px; margin-right:12px; font-size:12px;"><i style="width:10px; height:10px; background:' + t[2] + '; display:inline-block; border-radius:2px;"></i>' + t[1] + '</span>').join('');
  box.innerHTML =
    '<div class="panel-sub" style="margin-bottom:12px;">Dados do painel de faturamento do EmiteAí, mês a mês desde jan/2025. Atualizado automaticamente todo dia às 09:00 · última atualização: <b>' + esc(quando) + '</b>. O mês corrente é acumulado até d-1.</div>' +
    '<div class="panel"><div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;"><b>Mês:</b><select id="fatMes" class="itil-select" onchange="FAT_MES=this.value; fatRender();">' + opts + '</select><button type="button" class="export-btn" onclick="fatCarrega()">Recarregar</button></div></div>' +
    '<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); margin-top:14px;">' + kpi(FAT_N(atual.clientes), 'Clientes') + cDocs + cTri + cChamado + FAT_TIPOS.map(t => kpi(FAT_N(atual[t[0]]), t[1])).join('') + kpi(FAT_N(atual.sist), 'Sistêmico') + '</div>' +
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
    '.fat-ativo{background:#2563eb !important; color:#fff !important;}';
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
