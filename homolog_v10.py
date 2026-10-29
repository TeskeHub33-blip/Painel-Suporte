# -*- coding: utf-8 -*-
"""Homologacao v10: visual em todo o painel, busca de chamado por pagina e Fluxograma completo e interativo.

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

1) Busca global: uma caixa em todas as abas (exceto onde ja existe a propria) e o resultado muda conforme a pagina.
2) Visual EmiteAi em todo o painel: faixa de KPIs, botoes, campos e tabelas no mesmo padrao das abas de Gestao.
3) Fluxograma (atendimento) em arvore interativa: clique na etapa, proximos passos, indicadores, chamados e o caminho do chamado buscado.
4) Efeitos (inspirados em ideias do React Bits, de David Haz, MIT + Commons Clause — reimplementados em CSS/JS simples, sem copiar codigo):
   contagem dos numeros (CountUp), fundo em grade de pontos (DotGrid), brilho na etapa selecionada (BorderGlow) e lista com entrada em sequencia (AnimatedList).
"""

V10_CSS = """
/* ===== HOMOLOGACAO v10 ===== */
/* --- visual EmiteAi em todo o painel --- */
.kpi-row { display: grid; gap: 0 !important; background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); overflow: hidden; }
.kpi-row .kpi { background: transparent; border-radius: 0; box-shadow: inset 1px 0 0 var(--panel-border); padding: 16px 20px; }
.kpi-row .kpi:first-child { box-shadow: none; }
.kpi-row .kpi::before { display: none !important; }
.kpi-row .kpi .value { font-size: 26px; font-weight: 600; letter-spacing: -.6px; font-variant-numeric: tabular-nums; }
.kpi-row .kpi .label { text-transform: none; letter-spacing: 0; font-size: 12.5px; font-weight: 400; }
.kpi-row .kpi:hover { background: rgba(36,36,62,.02); }
html[data-tema="dark"] .kpi-row .kpi:hover { background: rgba(255,255,255,.03); }
.export-btn { background: transparent !important; color: var(--navy) !important; border: 1.25px solid #878799 !important; border-radius: 6px !important; font-weight: 600; transition: background .15s, border-color .15s; }
.export-btn:hover { background: rgba(36,36,62,.05) !important; border-color: var(--navy) !important; }
html[data-tema="dark"] .export-btn:hover { background: rgba(255,255,255,.06) !important; }
.itil-select, select.itil-select, input.itil-select { border: .625px solid rgba(135,135,153,.7); border-radius: 6px; background: var(--panel); color: var(--text); font-family: inherit; outline: none; transition: border-color .15s; }
.itil-select:focus { border: 1.5px solid var(--navy); }
.panel table:not(.flow-sla-table) th { background: var(--surface2); color: var(--text-dim); text-transform: none; letter-spacing: 0; font-size: 12px; font-weight: 600; }
#tabelaEmissoes .emis-card table th { background: transparent !important; }
.panel table tbody tr:hover td { background: rgba(36,36,62,.02); }
html[data-tema="dark"] .panel table tbody tr:hover td { background: rgba(255,255,255,.03); }
.bar-track { border-radius: 6px; }
.bar-fill { border-radius: 6px; }
.panel .panel-sub { color: var(--text3); }

/* --- busca global --- */
.hml-busca-global { margin: 0 0 14px 0; }
.hml-busca-global .hml-aba-atual { font-size: 12.5px; color: var(--text3); }
.hml-busca-global .hml-aba-atual b { color: var(--text-dim); font-weight: 600; }
.hml-pag-nota { font-size: 12.5px; color: var(--text3); margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--panel-border); line-height: 1.5; }
.hml-lista-mini { margin: 6px 0 0 0; padding: 0; list-style: none; font-size: 12.5px; line-height: 1.7; }

/* --- efeitos (CountUp / DotGrid / BorderGlow / AnimatedList), so' como resposta a uma acao --- */
.hf-diagrama { background-image: radial-gradient(var(--panel-border) 1px, transparent 1.2px); background-size: 22px 22px; background-position: 11px 11px; }
@keyframes hfBrilho { 0%, 100% { box-shadow: 0 0 0 2px var(--pink), 0 0 12px rgba(237,109,162,.35); } 50% { box-shadow: 0 0 0 2px var(--pink), 0 0 26px rgba(237,109,162,.7); } }
.hf-node.sel { animation: hfBrilho 2.4s ease-in-out infinite; }
@keyframes hfLinha { from { opacity: 0; transform: translateY(6px); } }
.hf-detalhe.entra .hf-lista tr { animation: hfLinha .28s cubic-bezier(.2, .7, .2, 1) both; }
.hf-detalhe.entra .hf-lista tr:nth-child(1) { animation-delay: 60ms; } .hf-detalhe.entra .hf-lista tr:nth-child(2) { animation-delay: 100ms; }
.hf-detalhe.entra .hf-lista tr:nth-child(3) { animation-delay: 140ms; } .hf-detalhe.entra .hf-lista tr:nth-child(4) { animation-delay: 180ms; }
.hf-detalhe.entra .hf-lista tr:nth-child(5) { animation-delay: 220ms; } .hf-detalhe.entra .hf-lista tr:nth-child(6) { animation-delay: 260ms; }
.hf-detalhe.entra .hf-lista tr:nth-child(7) { animation-delay: 300ms; } .hf-detalhe.entra .hf-lista tr:nth-child(8) { animation-delay: 340ms; }
@media (prefers-reduced-motion: reduce) { .hf-node.sel, .hf-detalhe.entra .hf-lista tr { animation: none; } }

/* --- Fluxograma de atendimento em arvore --- */
#flowDiagram .hf-wrap { margin-top: 4px; }
.hf-edge.volta { stroke-dasharray: 5 5; opacity: .45; }
.hf-edge.volta.on { opacity: 1; }
.hf-edge.taken { stroke: var(--ok); opacity: 1; stroke-width: 2.5; }
.hf-seta.taken { fill: var(--ok); opacity: 1; }
.hf-node.feito { box-shadow: var(--shadow), inset 3px 0 0 var(--ok); }
.hf-node.bloq { background: var(--danger-dim); box-shadow: var(--shadow), inset 3px 0 0 var(--danger); }
.hf-pills { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 14px 0; }
.hf-pill { font: 600 12px inherit; font-family: inherit; padding: 5px 11px; border-radius: 6px; cursor: pointer; background: transparent; color: var(--navy); border: 1.25px solid #878799; transition: background .15s, border-color .15s; }
.hf-pill:hover { background: var(--pink-dim); border-color: var(--pink); }
.hf-pill.feito { background: var(--ok-dim); border-color: var(--ok); color: var(--ok); }
.hf-sub { font-size: 12px; color: var(--text3); margin: 0 0 6px 0; }
"""

V10_JS = r"""
// ===== HOMOLOGACAO v10 =====
// ---------- CountUp (ideia do React Bits): o numero conta ate o valor novo quando a pessoa troca o indicador
function hfContaTexto(el) {
  const m = /^(-?\d+(?:[.,]\d+)?)(.*)$/.exec((el.textContent || '').trim()); if (!m) return;
  const alvo = parseFloat(m[1].replace(',', '.')), suf = m[2];
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const ini = performance.now(), dur = 600;
  (function passo(ts) { const p = Math.min(1, (ts - ini) / dur); el.textContent = Math.round(alvo * (1 - Math.pow(1 - p, 3))) + suf; if (p < 1) requestAnimationFrame(passo); })(ini);
}
function hfContaTudo(sel) { document.querySelectorAll(sel + ' .hf-v').forEach(hfContaTexto); }
{
  const _rgm = renderGmFluxo; let _sigM = null;
  renderGmFluxo = function() { _rgm(); if (_sigM !== hfModo) { _sigM = hfModo; hfContaTudo('#gmFluxo'); } };
  const _rgb = hfbRender; let _sigB = null;
  hfbRender = function() { _rgb(); if (_sigB !== HFB.modo) { _sigB = HFB.modo; hfContaTudo('#gbFluxo'); } };
}

// ---------- Busca global: o resultado muda conforme a pagina
const HML_ABAS = {live: 'Ao Vivo', hist: 'Histórico', clientes: 'Clientes', oneOnOne: 'One-on-One', gamificacao: 'Gamificação', reuniaoMensal: 'Reunião Mensal', fluxo: 'Fluxograma'};
window._hmlAba = 'live'; window._hmlSub = 'reuniao'; window._glTicket = null;
function hmlBarraVisivel() {
  const a = window._hmlAba;
  if (a === 'fluxo' || (a === 'reuniaoMensal' && (window._hmlSub === 'melhorias' || window._hmlSub === 'bugs'))) return false;
  if (a === 'oneOnOne' || a === 'gamificacao' || a === 'reuniaoMensal') { try { return sessionStorage.getItem(a + 'Unlocked') === '1'; } catch (e) { return false; } }   // abas com senha: so' depois de liberadas
  return true;
}
function hmlAtualizaBarra() {
  const bar = document.getElementById('hmlBuscaGlobal'); if (!bar) return;
  bar.style.display = hmlBarraVisivel() ? '' : 'none';
  const lbl = document.getElementById('glAba'); if (lbl) lbl.innerHTML = 'Informações para a página <b>' + (window._hmlAba === 'reuniaoMensal' ? 'Reunião Mensal' : (HML_ABAS[window._hmlAba] || '')) + '</b>';
  if (window._glTicket && hmlBarraVisivel()) hmlMostraGlobal(window._glTicket);
}
{
  const _show = showTab; showTab = function(name, skip) { _show(name, skip); window._hmlAba = name; hmlAtualizaBarra(); if (name === 'fluxo' && typeof hfxRender === 'function') hfxRender(); };
  const _gi = setGiSub; setGiSub = function(s) { _gi(s); window._hmlSub = s; hmlAtualizaBarra(); };
}
function hmlSlaTxt(t) {
  if (!t.slaSolutionDate) return 'sem SLA definido';
  const alvo = parseDt(t.slaSolutionDate);
  if (t.resolvedIn) return hmlDt(t.slaSolutionDate) + (parseDt(t.resolvedIn) <= alvo ? ' · cumprido' : ' · estourado');
  const h = (alvo - NOW) / 36e5; return hmlDt(t.slaSolutionDate) + (h < 0 ? ' · vencido há ' + fmtH(-h) : ' · vence em ' + fmtH(h));
}
function hmlEtapaFluxoTxt(t) {
  try { const k = effectiveStageForTicket(t), s = FLOW_MAIN_STAGES.concat([FLOW_SECONDARY_STAGE]).find(x => x.key === k); return s ? s.title : '–'; } catch (e) { return '–'; }
}
function hmlCamposPagina(t, aba) {
  const aberto = t._created !== undefined && !t.resolvedIn, resolvido = !!t.resolvedIn, nome = t.ownerName || '–';
  const idade = t.createdDate ? ((resolvido ? parseDt(t.resolvedIn) : NOW) - parseDt(t.createdDate)) / 36e5 : null;
  const C = [], N = [];
  const dono = esc(nome) + (t.ownerTeam ? ' <small>' + esc(t.ownerTeam) + '</small>' : '');
  if (aba === 'live') {
    if (!aberto) N.push('Este chamado já foi resolvido, então não aparece mais no Ao Vivo. O que aconteceu com ele está na página Histórico.');
    C.push(['Status atual', esc(t.status || '–')], ['Tempo no status', aberto ? 'há ' + gmDias(gmDiasNaEtapa(t)) : '–'], ['Última atualização', aberto ? 'há ' + fmtH(t._hoursSinceUpdate) : '–'],
      ['Aging (48h sem atualização)', aberto ? ((t._hoursSinceUpdate >= 48 && AGING_EQUIPES.indexOf(t.ownerTeam) !== -1 && AGING_STATUS.indexOf(t.status) !== -1) ? 'Sim' : 'Não') : '–'],
      ['SLA de solução', hmlSlaTxt(t)], ['Urgência', esc(t.urgency || '–')], ['Responsável', dono], ['Priorizado', aberto ? (t._isPriorizado ? esc(t.motivoPriorizacao || 'Sim') : 'Não') : '–'], ['Etapa no fluxo de atendimento', esc(hmlEtapaFluxoTxt(t))]);
  } else if (aba === 'hist') {
    if (aberto) N.push('Este chamado ainda está aberto. Ele entra no Histórico quando for resolvido, no mês da primeira resolução.');
    C.push(['Situação', resolvido ? 'Resolvido' : 'Aberto'], ['Resolvido em', resolvido ? hmlDt(t.resolvedIn) : '–'], ['Tempo até resolver', resolvido && idade !== null ? fmtH(idade) : '–'],
      ['Resolvido na 1ª resposta', resolvido ? (t.resolvedInFirstCall ? 'Sim' : 'Não') : '–'], ['SLA de solução', hmlSlaTxt(t)], ['Reaberto', t.reopenedIn ? 'Sim, em ' + hmlDt(t.reopenedIn) : 'Não'], ['Categoria', esc(t.category || 'Sem categoria')], ['Responsável', dono]);
  } else if (aba === 'clientes') {
    const org = t.clientOrg, outros = org ? TICKETS.filter(x => x.clientOrg === org && x.id !== t.id) : [];
    const porCat = {}; outros.concat(aberto ? [t] : []).forEach(x => { const c = x.category || 'Sem categoria'; porCat[c] = (porCat[c] || 0) + 1; });
    C.push(['Cliente', esc(org || '–')], ['Chamados abertos do cliente', String(outros.length + (aberto ? 1 : 0))], ['Com SLA vencido', String(outros.filter(x => x._slaVencido).length + (aberto && t._slaVencido ? 1 : 0))],
      ['Por categoria', Object.keys(porCat).length ? Object.entries(porCat).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([c, n]) => esc(c) + ' (' + n + ')').join(', ') : '–']);
    if (outros.length) N.push('Outros chamados abertos deste cliente:<ul class="hml-lista-mini">' + outros.slice(0, 6).map(x => '<li>' + ticketLink(x.id, x.protocol) + ' ' + esc((x.subject || '').slice(0, 60)) + ' <small>' + esc(x.status) + '</small></li>').join('') + '</ul>');
  } else if (aba === 'oneOnOne' || aba === 'gamificacao') {
    const mes = (typeof RESOLVED_MONTH !== 'undefined' ? RESOLVED_MONTH : []).filter(r => r.ownerName === nome), pri = mes.filter(r => { try { return isPrimeiraResposta(r); } catch (e) { return false; } });
    const abertos = TICKETS.filter(x => x.ownerName === nome);
    C.push(['Responsável', dono], ['Chamados abertos com ele', String(abertos.length)], ['Resolvidos no mês', String(mes.length)], ['Resolvidos na 1ª resposta no mês', mes.length ? Math.round(pri.length / mes.length * 100) + '%' : '–'],
      ['Este chamado', esc(t.status || (resolvido ? 'Resolvido' : '–'))], ['Tempo deste chamado', idade !== null ? fmtH(idade) : '–'], ['Na 1ª resposta', resolvido ? (t.resolvedInFirstCall ? 'Sim' : 'Não') : '–']);
    N.push('Estes números são do mês corrente e valem para o responsável do chamado.');
  } else if (aba === 'reuniaoMensal') {
    const cat = t.category || 'Sem categoria', sim = b => b ? 'Sim' : 'Não';
    const mesKey = Object.keys(MONTH_YM).find(k => (RESOLVED_MONTHS[k] || []).some(r => String(r.protocol) === String(t.protocol)));
    C.push(['Categoria', esc(cat)], ['Mês de resolução', resolvido ? esc(MONTH_LABELS[mesKey] || hmlDt(t.resolvedIn).slice(3, 10)) : 'ainda aberto'], ['Entra no % SLA Suporte', sim(CATEGORIAS_EXCLUIDAS_SLA_SUPORTE.indexOf(cat) === -1)],
      ['Entra no % SLA EmiteAi', sim(CATEGORIAS_EXCLUIDAS_SLA_EMITEAI.indexOf(cat) === -1)], ['Entra no tempo total', sim(CATEGORIAS_EXCLUIDAS_TEMPO_TOTAL.indexOf(cat) === -1)], ['Resolvido na 1ª resposta', resolvido ? (t.resolvedInFirstCall ? 'Sim' : 'Não') : '–']);
    N.push('A tabela mensal conta o chamado no mês da primeira resolução, só para o time Suporte e sem os cancelados.');
  }
  return {C, N};
}
function hmlCartaoPagina(t, aba) {
  const urg = t.urgency || '', chips = hmlChip(t.status || (t.resolvedIn ? 'Resolvido' : '-'), 'pink') + hmlChip(t.category || 'Sem categoria') + (urg ? hmlChip('Urgência ' + urg, urg === 'Alta' ? 'bad' : urg === 'Média' ? 'warn' : '') : '');
  const {C, N} = hmlCamposPagina(t, aba), protoJs = jsStr(String(t.protocol));
  return `<div class="hml-exec"><div class="hml-exec-topo"><div><div class="hml-prot">Chamado ${esc(t.protocol)} · ${esc(window._hmlAba === 'reuniaoMensal' ? 'Reunião Mensal' : HML_ABAS[aba] || '')}</div><h3>${esc(t.subject || '')}</h3><div>${chips}</div></div>
    <div class="hml-exec-acoes"><a href="${MOVIDESK_BASE}${t.id}" target="_blank" rel="noopener">Abrir no Movidesk</a>
      <button type="button" onclick="document.getElementById('fluxoBuscaProtocolo').value=${protoJs}; showTab('fluxo'); buscarChamadoFluxoPorProtocolo();">Ver no fluxograma</button>
      <button type="button" onclick="window._glTicket=null; document.getElementById('glRes').innerHTML=''; document.getElementById('glInput').value='';">Fechar</button></div></div>
    <div class="hml-exec-grid">${C.map(c => hmlCampo(c[0], c[1])).join('')}</div>${N.map(n => `<div class="hml-pag-nota">${n}</div>`).join('')}</div>`;
}
function hmlMostraGlobal(t) { document.getElementById('glRes').innerHTML = hmlCartaoPagina(t, window._hmlAba); }
function hmlBuscaGlobal() {
  const v = document.getElementById('glInput').value, t = findTicketByProtocol(v), res = document.getElementById('glRes');
  if (!t) { window._glTicket = null; res.innerHTML = `<div class="hml-erro">Chamado "${esc(v)}" não encontrado (busca entre os abertos e os resolvidos nos meses carregados).</div>`; return; }
  window._glTicket = t; hmlMostraGlobal(t);
}
hmlAtualizaBarra();
setInterval(() => { const b = document.getElementById('hmlBuscaGlobal'); if (b) b.style.display = hmlBarraVisivel() ? '' : 'none'; }, 1000);

// ---------- Fluxograma de atendimento: arvore interativa
const HFX = {W: 780, H: 1040, nw: 190, nh: 84, X: {e: 10, c: 295, d: 580}, modo: 'qtd', sel: null, manual: false, ticket: null, ctx: null, esc: 1,
  modos: [['qtd', 'Quantidade'], ['media', 'Média parada'], ['maior', 'Mais antigo parado'], ['idade', 'Idade média'], ['sla', 'Com SLA vencido']],
  pos: {entrada: ['c', 0], triagem: ['c', 1], n1: ['c', 2], n2: ['c', 3], pendente_usuario: ['d', 3], task_dev: ['c', 4], validacao_impedimento: ['c', 5], validacao_cliente: ['e', 6], encerrado: ['c', 7]}};
const HFX_Y = r => 12 + r * 130;
function hfxDef(k) { return FLOW_MAIN_STAGES.concat([FLOW_SECONDARY_STAGE]).find(s => s.key === k) || {key: k, title: k, sub: ''}; }
function hfxBox(k) { const p = HFX.pos[k]; return {x: HFX.X[p[0]], y: HFX_Y(p[1]), w: HFX.nw, h: HFX.nh}; }
function hfxSeta(x, y, d) {
  return d === 'd' ? `M${x - 5} ${y - 9} L${x} ${y} L${x + 5} ${y - 9} Z` : d === 'u' ? `M${x - 5} ${y + 9} L${x} ${y} L${x + 5} ${y + 9} Z` : d === 'r' ? `M${x - 9} ${y - 5} L${x} ${y} L${x - 9} ${y + 5} Z` : `M${x + 9} ${y - 5} L${x} ${y} L${x + 9} ${y + 5} Z`;
}
function hfxCaminho(de, para) {
  const a = hfxBox(de), b = hfxBox(para), ra = HFX.pos[de][1], rb = HFX.pos[para][1], ca = HFX.pos[de][0], cb = HFX.pos[para][0];
  if (ra === rb) { const dir = b.x > a.x, x1 = dir ? a.x + a.w : a.x, x2 = dir ? b.x : b.x + b.w, y = a.y + a.h / 2; return {d: `M${x1} ${y} L${x2} ${y}`, s: hfxSeta(x2, y, dir ? 'r' : 'l'), volta: false}; }
  if (rb > ra) {
    const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
    if (x1 === x2) return {d: `M${x1} ${y1} L${x2} ${y2 - 1}`, s: hfxSeta(x2, y2, 'd'), volta: false};
    const ym = ca === 'c' ? y1 + 21 : (rb - ra > 1 ? y2 - 21 : (y1 + y2) / 2);
    return {d: `M${x1} ${y1} L${x1} ${ym} L${x2} ${ym} L${x2} ${y2 - 1}`, s: hfxSeta(x2, y2, 'd'), volta: false};
  }
  if (ca === cb) { const x = a.x - 26, ya = a.y + a.h / 2, yb = b.y + b.h / 2; return {d: `M${a.x} ${ya} L${x} ${ya} L${x} ${yb} L${b.x - 1} ${yb}`, s: hfxSeta(b.x, yb, 'r'), volta: true}; }
  if (ca === 'c' && cb === 'd') { const xb = b.x + b.w / 2, ya = a.y + a.h / 2; return {d: `M${a.x + a.w} ${ya} L${xb} ${ya} L${xb} ${b.y + b.h + 1}`, s: hfxSeta(xb, b.y + b.h, 'u'), volta: true}; }
  const x = a.x + a.w + 26, ya = a.y + a.h / 2, yb = b.y + b.h / 2; return {d: `M${a.x + a.w} ${ya} L${x} ${ya} L${x} ${yb} L${b.x + b.w + 1} ${yb}`, s: hfxSeta(b.x + b.w, yb, 'l'), volta: true};
}
function hfxMede() { const c = document.getElementById('flowDiagram'); let cw = c ? c.clientWidth : 0; if (cw < 300) cw = 1100; const m = hfMede2(cw); HFX.esc = m.s; HFX.Wc = m.Wc; hfAjustaX(m.Wc, HFX.X, HFX.nw, 780); }
function hfMede2(cw) { const Wd = (cw > 1100 ? cw - 360 - 18 : cw) - 28, s = Wd < 780 ? Wd / 780 : Math.min(1.3, Wd / 780); return {s: s, Wc: Wd < 780 ? 780 : Math.round(Wd / s)}; }
function hfxIndicadores(itens) { const b = hfIndicadores(itens); b.sla = itens.filter(t => t._slaVencido).length; return b; }
function hfxValor(ind) { if (HFX.modo === 'qtd') return String(ind.qtd); if (HFX.modo === 'sla') return String(ind.sla); const v = ind[HFX.modo]; return v === null ? '–' : Math.round(v) + ' d'; }
function hfxBuckets() {
  const b = {}; Object.keys(HFX.pos).forEach(k => { b[k] = []; });
  let abertos = []; try { abertos = fluxoOpenScope(); } catch (e) { abertos = TICKETS; }
  abertos.forEach(t => { let k = null; try { k = effectiveStageForTicket(t); } catch (e) {} if (k && b[k]) b[k].push(t); });
  return b;
}
function hfxRender() {
  const alvo = document.getElementById('flowDiagram'); if (!alvo || !HFX.ctx) return;
  hfxMede();
  const c = HFX.ctx, bk = hfxBuckets(), visit = c.visitedKeys || [], taken = c.takenNextMap || {};
  if (HFX.ticket && HFX.sel === null && !HFX.manual) HFX.sel = c.currentKey;
  let svg = '', nos = '';
  const alc = k => k === c.currentKey || visit.indexOf(k) !== -1;     // etapa que o chamado ja alcancou
  Object.keys(FLOW_NEXT_OPTIONS).forEach(de => (FLOW_NEXT_OPTIONS[de] || []).forEach(([para]) => {
    if (!HFX.pos[de] || !HFX.pos[para]) return;
    const e = hfxCaminho(de, para), cls = (e.volta ? ' volta' : '') + (HFX.sel === de ? ' on' : '') + (taken[de] === para ? ' taken' : '') + (HFX.ticket && taken[de] !== para && !(alc(de) && alc(para)) ? ' pendente' : '');
    svg += `<path class="hf-edge${cls}" d="${e.d}"/><path class="hf-seta${HFX.sel === de ? ' on' : ''}${taken[de] === para ? ' taken' : ''}" d="${e.s}"/>`;
  }));
  const modoNome = HFX.modos.find(m => m[0] === HFX.modo)[1].toLowerCase();
  Object.keys(HFX.pos).forEach(k => {
    const bx = hfxBox(k), d = hfxDef(k), itens = bk[k], ind = hfxIndicadores(itens), tempo = (c.stageTimes || {})[k];
    let cls = 'hf-node' + (!itens.length ? ' vazio' : ind.media > 15 ? ' danger' : ind.media > 7 ? ' warn' : '');
    if (HFX.sel === k) cls += ' sel';
    if (c.currentKey === k) cls += (c.blockedKey === k ? ' bloq' : ' fl-atual');
    else if (visit.indexOf(k) !== -1) cls += ' feito';
    if (HFX.ticket && !alc(k)) cls += ' pendente';
    const s = HFX.modo === 'qtd' ? (ind.media === null ? 'nenhum chamado' : 'média parado ' + Math.round(ind.media) + ' d') : modoNome + ' · ' + ind.qtd + (ind.qtd === 1 ? ' chamado' : ' chamados');
    const t2 = tempo !== undefined && tempo !== null ? ` · ${c.perTicket ? 'neste chamado' : 'média geral'}: ${fmtH(tempo)}` : '';
    nos += `<button type="button" class="${cls}" data-k="${k}" id="flowbox-${k}" style="left:${bx.x}px; top:${bx.y}px;" onclick="hfxSelecionar('${k}')"><div class="hf-t">${esc(d.title)}</div><div class="hf-v">${hfxValor(ind)}</div><div class="hf-s">${esc(s + t2)}</div></button>`;
  });
  alvo.innerHTML = `<div class="hf-wrap"><div class="hf-topo"><span class="hf-rot">Exibir em cada etapa:</span>
    <span class="seg-toggle" role="group" aria-label="Indicador exibido">${HFX.modos.map(m => `<button type="button" class="${m[0] === HFX.modo ? 'active' : ''}" onclick="hfxMudaModo('${m[0]}')">${m[1]}</button>`).join('')}</span></div>
    <div class="hf-grid"><div class="hf-diagrama" id="hfxDiag"><div class="hf-canvas" id="hfxCanvas" style="width:${HFX.Wc}px; height:${HFX.H}px;"><svg class="hf-svg" width="${HFX.Wc}" height="${HFX.H}" viewBox="0 0 ${HFX.Wc} ${HFX.H}" aria-hidden="true">${svg}</svg>${nos}</div></div>
    <aside class="hf-detalhe" id="hfxDet"></aside></div></div>`;
  const d = document.getElementById('hfxDiag'), cv = document.getElementById('hfxCanvas');
  cv.style.transform = 'scale(' + HFX.esc + ')'; d.style.height = (HFX.H * HFX.esc + 36) + 'px';
  hfxDetalhe(bk);
}
function hfxDetalhe(bk) {
  const el = document.getElementById('hfxDet'); if (!el) return;
  const c = HFX.ctx, t = HFX.ticket;
  if (!HFX.sel) {
    el.innerHTML = `<h3>Selecione uma etapa</h3><p class="hf-regra">Clique em uma etapa para ver o que ela significa, os próximos passos possíveis, os indicadores e os chamados que estão nela. Busque um chamado para ver por onde ele passou e o que vem agora.</p>`;
    return;
  }
  const k = HFX.sel, d = hfxDef(k), itens = bk[k] || [], ind = hfxIndicadores(itens), f = v => v === null ? '–' : Math.round(v) + ' d';
  let h = `<h3>${esc(d.title)}</h3><p class="hf-regra">${esc(d.sub || '')}</p>`;
  if (t && c && c.currentKey === k) h += `<div class="hf-prox"><b>Próximo passo deste chamado.</b> ${proximosPassosTexto(t.status)}</div>`;
  else if (t && c && (c.visitedKeys || []).indexOf(k) !== -1) h += `<div class="hf-prox">O chamado já passou por esta etapa.</div>`;
  const ops = FLOW_NEXT_OPTIONS[k] || [];
  h += `<div class="hf-sub">Próximos passos possíveis a partir daqui</div>` + (ops.length ? `<div class="hf-pills">${ops.map(([p, l]) => `<button type="button" class="hf-pill${c && c.takenNextMap && c.takenNextMap[k] === p ? ' feito' : ''}" onclick="hfxSelecionar('${p}', true)">${c && c.takenNextMap && c.takenNextMap[k] === p ? '✓ ' : ''}${esc(l)}</button>`).join('')}</div>` : '<p class="hf-regra">Fim do fluxo.</p>');
  h += `<div class="hf-ind"><div><b>${ind.qtd}</b><span>chamados abertos aqui</span></div><div><b>${f(ind.media)}</b><span>média parada</span></div><div><b>${f(ind.maior)}</b><span>mais antigo parado</span></div><div><b>${f(ind.idade)}</b><span>idade média</span></div><div><b>${ind.sla}</b><span>com SLA vencido</span></div><div><b>${f(ind.mediana)}</b><span>mediana parada</span></div></div>`;
  if (itens.length) {
    const top = itens.slice().sort((a, b) => gmDiasParado(b) - gmDiasParado(a)).slice(0, 8);
    h += `<table class="hf-lista"><tbody>${top.map(x => `<tr><td>${ticketLink(x.id, x.protocol)} ${esc((x.subject || '').slice(0, 60))}<div class="hf-c">${esc(x.clientOrg || '-')}${x._slaVencido ? ' · SLA vencido' : ''}</div></td><td>${Math.round(gmDiasParado(x))} d</td></tr>`).join('')}</tbody></table>
      <button type="button" class="hf-mais" onclick="abrirModalEtapaFluxo(${jsStr(k)}, ${jsStr(d.title)})">Ver os ${itens.length} chamados</button>`;
  } else h += '<p class="hf-vazio">Nenhum chamado aberto nesta etapa agora.</p>';
  el.innerHTML = h; el.classList.remove('entra'); void el.offsetWidth; el.classList.add('entra');
}
function hfxSelecionar(k, manter) { HFX.sel = (HFX.sel === k && !manter) ? null : k; HFX.manual = true; hfxRender(); }
function hfxMudaModo(m) { HFX.modo = m; hfxRender(); hfContaTudo('#flowDiagram'); }
renderFlowDiagram = function(currentKey, stageTimes, extras, perTicket, visitedKeys, takenNextMap, blockedKey) {
  HFX.ctx = {currentKey: currentKey, stageTimes: stageTimes || {}, extras: extras || {}, perTicket: perTicket, visitedKeys: visitedKeys || [], takenNextMap: takenNextMap || {}, blockedKey: blockedKey};
  hfxRender();
};
{
  const _c = carregarChamadoFluxo; carregarChamadoFluxo = function(t) { HFX.ticket = t; HFX.sel = null; HFX.manual = false; _c(t); };
  const _l = limparBuscaFluxo; limparBuscaFluxo = function() { HFX.ticket = null; HFX.sel = null; HFX.manual = false; _l(); };
  const painelPassos = document.getElementById('fluxoProximosPassos'); if (painelPassos && painelPassos.closest('.panel')) painelPassos.closest('.panel').style.display = 'none';
  window.addEventListener('resize', () => { clearTimeout(window._hfxT); window._hfxT = setTimeout(() => { const g = document.getElementById('flowDiagram'); if (g && g.offsetParent) hfxRender(); }, 150); });
  try { renderFluxoAgregado(); } catch (e) {}
}
"""


def aplicar_v10(html):
    barra = ('<div class="hml-busca-global" id="hmlBuscaGlobal"><div class="hml-busca"><input id="glInput" placeholder="Buscar chamado pelo número" '
             'onkeydown="if(event.key===\'Enter\')hmlBuscaGlobal()"><button type="button" onclick="hmlBuscaGlobal()">Buscar chamado</button>'
             '<span class="hml-aba-atual" id="glAba"></span></div><div id="glRes"></div></div>\n\n  ')
    return html.replace('<div class="tab-panel active" id="tabLive">', barra + '<div class="tab-panel active" id="tabLive">', 1)
