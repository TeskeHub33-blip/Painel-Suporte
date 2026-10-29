# -*- coding: utf-8 -*-
"""Homologacao v5: revisao visual guiada pela skill frontend-design.

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Decisoes (plano da skill):
  - mantem a identidade EmiteAi (navy/rosa/Inter) — e' marca, nao escolha de template
  - um elemento memoravel: a faixa "onde estao paradas", com a etapa mais parada em rosa e uma frase com os dados
  - tira os sinais de pagina gerada: KPIs em cartoes identicos repetindo o Kanban, rotulos em CAIXA ALTA,
    elevacao de cartao ao passar o mouse, entrada animada em todo bloco
  - movimento so' onde chama atencao: contagem dos numeros e pulso nas etapas com chamado parado ha mais de 30 dias
"""

V5_CSS = """
/* ===== HOMOLOGACAO v5: frontend-design ===== */
/* sem rotulos em caixa alta */
.kpi .label, .fl-lane h3, .hml-exec-grid .k, .hml-exec-bloco .k, .hml-passo small, #tabFluxo #flowRowMain::before, #tabFluxo #flowRowSecundaria::before,
.fl-node.fl-atual::before, #tabFluxo .flow-box.flow-current::before { text-transform: none; letter-spacing: 0; }
.fl-lane h3, #tabFluxo #flowRowMain::before, #tabFluxo #flowRowSecundaria::before { font-size: 13px; font-weight: 600; color: var(--text-dim); }
.hml-exec-grid .k, .hml-exec-bloco .k { font-size: 12px; font-weight: 400; color: var(--text3); }
.kpi .label { font-size: 12.5px; font-weight: 400; }
.fl-node.fl-atual::before, #tabFluxo .flow-box.flow-current::before { font-size: 11px; font-weight: 600; }

/* sem elevacao ao passar o mouse nem entrada animada em todo bloco */
.kpi:hover, .panel:hover { box-shadow: var(--shadow); }
.fl-node, #tabFluxo .flow-box { animation: none; }
.fl-node:hover, .fl-node:focus-visible, #tabFluxo .flow-box.flow-clickable:hover { transform: none; box-shadow: var(--shadow2); }
.fl-arrow, #tabFluxo .flow-row .flow-box:not(:last-child)::after { animation: none; }

/* KPIs: uma faixa unica em vez de cartoes iguais */
#giSub_melhorias .kpi-row, #giSub_bugs .kpi-row { display: grid !important; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: 0 !important;
  background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); overflow: hidden; }
#giSub_melhorias .kpi-row .kpi, #giSub_bugs .kpi-row .kpi { background: transparent; box-shadow: none; border-radius: 0; box-shadow: inset 1px 0 0 var(--panel-border); padding: 16px 20px; }
#giSub_melhorias .kpi-row .kpi:first-child, #giSub_bugs .kpi-row .kpi:first-child { box-shadow: none; }
#giSub_melhorias .kpi-row .kpi::before, #giSub_bugs .kpi-row .kpi::before { display: none !important; }
#giSub_melhorias .kpi .value, #giSub_bugs .kpi .value { font-size: 28px; font-weight: 600; letter-spacing: -.8px; font-variant-numeric: tabular-nums; }
#gmKpis .kpi:nth-child(-n+5) { display: none; }       /* ja estao na faixa "onde estao paradas" */
#gbKpis .kpi:nth-child(4) { display: none; }
#giSub_melhorias td, #giSub_bugs td, #giSub_melhorias th, #giSub_bugs th { font-variant-numeric: tabular-nums; }

/* faixa "onde estao paradas": o elemento memoravel */
.hml-pipe-bloco { margin: 0 0 18px 0; }
.hml-pipe-bloco h2 { margin: 0 0 4px 0; font-size: 18px; font-weight: 600; letter-spacing: -.3px; color: var(--text); }
.hml-pipe-bloco p { margin: 0 0 12px 0; font-size: 13.5px; color: var(--text-dim); max-width: 70ch; line-height: 1.5; }
.hml-pipe-bloco p b { font-weight: 600; color: var(--text); }
.hml-pipe { display: flex; flex-wrap: wrap; background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); overflow: hidden; }
.hml-pipe-seg { flex: var(--w) 1 150px; position: relative; padding: 16px 20px 14px; box-shadow: inset 1px 0 0 var(--panel-border); }
.hml-pipe-seg:first-child { box-shadow: none; }
.hml-pipe-seg b { display: block; font-size: 34px; font-weight: 600; letter-spacing: -1px; line-height: 1.05; font-variant-numeric: tabular-nums; color: var(--text); }
.hml-pipe-seg span { display: block; margin-top: 6px; font-size: 13px; color: var(--text-dim); }
.hml-pipe-seg small { display: block; margin-top: 2px; font-size: 12px; color: var(--text3); }
.hml-pipe-seg.critica::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: var(--pink); }
.hml-pipe-seg.critica small { color: var(--pink); font-weight: 600; }
.hml-pipe-seg.vazia b { color: var(--text3); }

/* Emissoes x Chamados: cartoes compactos, sem estourar a largura (a tabela de cada mes cabe no proprio cartao) */
#tabelaEmissoes .emis-grid { grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }
#tabelaEmissoes .emis-card { min-width: 0; overflow-x: auto; padding: 14px 16px; }
#tabelaEmissoes .emis-card-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
#tabelaEmissoes .emis-card table { width: 100%; table-layout: auto; font-size: 12px; }
#tabelaEmissoes .emis-card table th { padding: 5px 8px; font-size: 12px; font-weight: 600; background: transparent !important; text-transform: none; letter-spacing: 0; color: var(--text3); border-bottom: 1px solid var(--panel-border); white-space: nowrap; }
#tabelaEmissoes .emis-card table td { padding: 6px 8px; font-size: 12px; border-bottom: 1px solid rgba(135,135,153,.12); font-variant-numeric: tabular-nums; }
#tabelaEmissoes .emis-card table td:first-child { white-space: normal; min-width: 96px; }
#tabelaEmissoes .emis-card tr:last-child td { border-bottom: none; }

/* Fluxograma: mesmo desenho do Fluxo de melhorias (nos com numero, setas, etapa atual em rosa) */
#flowDiagram .fl-wrap { gap: 20px; }
#flowDiagram .fl-lane { box-shadow: none; background: transparent; padding: 0; }
#flowDiagram .fl-lane h3 { margin: 0 0 12px 0; }
#flowDiagram .fl-node { max-width: 230px; flex: 1 0 190px; cursor: default; }
#flowDiagram .fl-node[role="button"] { cursor: pointer; }
#flowDiagram .fl-node.fl-feito { box-shadow: var(--shadow), inset 3px 0 0 var(--ok); }
#flowDiagram .fl-node.fl-bloq { background: var(--danger-dim); box-shadow: var(--shadow), inset 0 0 0 2px var(--danger); }
#flowDiagram .fl-node .fl-n { margin: 6px 0 2px; }
#flowDiagram .fl-node .fl-s { margin-bottom: 4px; }
#flowDiagram .fl-node .flow-sub { font-size: 11.5px; color: var(--text3); line-height: 1.35; }
#flowDiagram .fl-node .flow-next-options { margin-top: 10px; }
"""

V5_JS = r"""
// ===== HOMOLOGACAO v5: faixa "onde estao paradas" (Melhorias e Bugs) =====
function hmlFaixaParadas(boxId, titulo, itens, cols, chaveFn) {
  const alvo = document.getElementById(boxId); if (!alvo) return;
  const etapas = cols.map(c => ({t: c.t, it: itens.filter(x => chaveFn(x) === c.k)}));
  const total = etapas.reduce((s, e) => s + e.it.length, 0);
  const comItens = etapas.filter(e => e.it.length);
  const media = e => gmMedia(e.it.map(gmDiasParado));
  const critica = comItens.slice().sort((a, b) => media(b) - media(a))[0];
  const frase = !total ? 'Nenhum chamado nas etapas acompanhadas agora.'
    : `${total} ${total === 1 ? 'chamado está' : 'chamados estão'} nas etapas acompanhadas. A etapa mais parada é <b>“${esc(critica.t)}”</b>, com média de <b>${Math.round(media(critica))} dias</b> sem atualização.`;
  const segs = etapas.map(e => {
    const m = e.it.length ? media(e) : null;
    return `<div class="hml-pipe-seg ${e === critica ? 'critica' : ''} ${e.it.length ? '' : 'vazia'}" style="--w:${Math.max(e.it.length, 1)}">
      <b>${e.it.length}</b><span>${esc(e.t)}</span><small>${m === null ? 'nenhum chamado' : (e === critica ? 'mais parada · ' : '') + 'média ' + Math.round(m) + ' dias parado'}</small></div>`;
  }).join('');
  alvo.innerHTML = `<div class="hml-pipe-bloco"><h2>${titulo}</h2><p>${frase}</p><div class="hml-pipe">${segs}</div></div>`;
}
document.getElementById('gmKpis').insertAdjacentHTML('beforebegin', '<div id="gmPipe"></div>');
document.getElementById('gbKpis').insertAdjacentHTML('beforebegin', '<div id="gbPipe"></div>');
// ===== Fluxograma com o mesmo markup do Fluxo de melhorias =====
renderFlowDiagram = function(currentKey, stageTimes, extras, perTicket, visitedKeys, takenNextMap, blockedKey) {
  extras = extras || {}; visitedKeys = visitedKeys || []; takenNextMap = takenNextMap || {}; stageTimes = stageTimes || {};
  const no = (s) => {
    const clicavel = FLOW_CLICKAVEL.indexOf(s.key) !== -1;
    const tempo = stageTimes[s.key];
    const qtd = clicavel ? ticketsNaEtapa(s.key).length : null;
    const atual = s.key === currentKey, bloq = atual && s.key === blockedKey, feito = !atual && visitedKeys.indexOf(s.key) !== -1;
    const attrs = clicavel ? `tabindex="0" role="button" onclick="abrirModalEtapaFluxo(${jsStr(s.key)}, ${jsStr(s.title)})" onkeydown="if(event.key==='Enter')abrirModalEtapaFluxo(${jsStr(s.key)}, ${jsStr(s.title)})"` : '';
    const tempoTxt = tempo !== undefined && tempo !== null ? `<div class="fl-s">${perTicket ? 'Tempo neste chamado' : 'Tempo médio'}: <b>${fmtH(tempo)}</b></div>` : '';
    return `<div class="fl-node ${bloq ? 'fl-bloq' : atual ? 'fl-atual' : ''} ${feito ? 'fl-feito' : ''}" id="flowbox-${s.key}" data-pid="${s.key}" ${attrs}>
      <div class="fl-t">${esc(s.title)}</div>
      ${qtd !== null ? `<div class="fl-n" data-alvo="${qtd}">0</div><div class="fl-s">chamados agora</div>` : ''}
      <div class="flow-sub">${esc(s.sub)}</div>${tempoTxt}${extras[s.key] || ''}${flowNextPillsHtml(s.key, takenNextMap[s.key])}</div>`;
  };
  const seta = '<div class="fl-arrow"></div>';
  document.getElementById('flowDiagram').innerHTML = `<div class="fl-wrap">
    <div class="fl-lane"><h3>Fluxo de atendimento</h3><div class="fl-row">${FLOW_MAIN_STAGES.map(no).join(seta)}</div></div>
    <div class="fl-lane"><h3>Desvio do fluxo</h3><div class="fl-row">${no(FLOW_SECONDARY_STAGE)}</div></div></div>`;
  document.querySelectorAll('#flowDiagram .fl-n').forEach(el => gmContaAnima(el, Number(el.dataset.alvo)));
};
renderFluxoAgregado();

const _v5Rgm = renderGestaoMelhorias;
renderGestaoMelhorias = function() {
  _v5Rgm();
  const todas = gmMelhorias(); todas.forEach(t => { t._gmE = gmEtapa(t); });
  hmlFaixaParadas('gmPipe', 'Onde as melhorias estão paradas', todas, GM_COLS, t => t._gmE);
};
const _v5Rgb = renderGestaoBugs;
renderGestaoBugs = function() {
  _v5Rgb();
  const todas = TICKETS.filter(t => t.category === 'Bug'); todas.forEach(t => { t._gbE = gbEtapa(t); });
  hmlFaixaParadas('gbPipe', 'Onde os bugs estão parados', todas, GB_COLS, t => t._gbE);
};
"""
