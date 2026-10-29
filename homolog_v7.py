# -*- coding: utf-8 -*-
"""Homologacao v7: Fluxo de melhorias como fluxograma em arvore, interativo.

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

- arvore com conectores ortogonais (tronco -> decisao -> caminho gratuito / cobrado -> convergencia)
- clicar numa etapa a seleciona (brilho rosa), destaca o caminho ate ela e abre o detalhamento ao lado
- seletor "Exibir em cada etapa": quantidade, media parada, mais antigo, idade media, parados ha mais de 15 dias
- o detalhamento traz regra da etapa, proximo passo, indicadores e os chamados mais parados
"""

V7_CSS = """
/* ===== HOMOLOGACAO v7: fluxograma em arvore interativo ===== */
.hf-wrap { display: flex; flex-direction: column; gap: 14px; }
.hf-topo { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.hf-topo .hf-rot { font-size: 13px; color: var(--text-dim); }
.hf-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 18px; align-items: start; }
@media (max-width: 1100px) { .hf-grid { grid-template-columns: minmax(0, 1fr); } }
.hf-diagrama { background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); padding: 18px 14px; overflow: hidden; position: relative; }
.hf-canvas { position: relative; transform-origin: 0 0; }
.hf-svg { position: absolute; inset: 0; pointer-events: none; overflow: visible; }
.hf-edge { fill: none; stroke: var(--navy-lt); stroke-width: 1.75; opacity: .55; transition: stroke .15s, opacity .15s, stroke-width .15s; }
.hf-edge.lado { stroke-dasharray: 5 5; }
.hf-edge.on { stroke: var(--pink); opacity: 1; stroke-width: 2.5; }
.hf-seta { fill: var(--navy-lt); opacity: .8; } .hf-seta.on { fill: var(--pink); opacity: 1; }
.hf-rotulo { position: absolute; font-size: 11.5px; font-weight: 600; color: var(--text3); background: var(--panel); padding: 1px 8px; border-radius: 6px; transform: translate(-50%, -50%); white-space: nowrap; }
.hf-node { position: absolute; width: 190px; height: 84px; box-sizing: border-box; padding: 10px 14px 10px 17px; border-radius: 6px; background: var(--panel); cursor: pointer;
  box-shadow: var(--shadow), inset 3px 0 0 var(--ok); transition: box-shadow .15s, background .15s; text-align: left; font-family: inherit; color: var(--text); border: none; }
.hf-node:hover { box-shadow: var(--shadow2), inset 3px 0 0 var(--ok); }
.hf-node.warn { box-shadow: var(--shadow), inset 3px 0 0 var(--warn-solid); }
.hf-node.danger { box-shadow: var(--shadow), inset 3px 0 0 var(--danger); }
.hf-node.vazio { box-shadow: var(--shadow), inset 3px 0 0 var(--panel-border); }
.hf-node:focus-visible { outline: 2px solid var(--pink); outline-offset: 2px; }
.hf-node .hf-t { font-size: 12.5px; font-weight: 600; line-height: 1.25; color: var(--text); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.hf-node .hf-v { font-size: 22px; font-weight: 700; letter-spacing: -.5px; line-height: 1.15; margin-top: 4px; font-variant-numeric: tabular-nums; }
.hf-node .hf-s { font-size: 11px; color: var(--text3); }
.hf-node.danger .hf-v { color: var(--danger); }
.hf-node.vazio .hf-v { color: var(--text3); }
.hf-node.hf-fixo { background: var(--surface2); cursor: pointer; box-shadow: var(--shadow); }
.hf-node.hf-raiz { background: var(--navy); color: #fff; box-shadow: var(--shadow); }
.hf-node.hf-raiz .hf-t { color: #fff; } .hf-node.hf-raiz .hf-s { color: #B8B8D0; }
.hf-node.hf-dec { background: var(--pink-dim); box-shadow: inset 0 0 0 1px var(--pink); }
.hf-node.sel { box-shadow: 0 0 0 2px var(--pink), 0 0 20px rgba(237,109,162,.55); }
.hf-node.fl-atual::before { content: 'Etapa atual'; position: absolute; top: -9px; left: 12px; padding: 1px 8px; border-radius: 6px; background: var(--pink); color: #fff; font-size: 11px; font-weight: 600; }
html[data-tema="dark"] .hf-node.hf-raiz { background: #3A3A66; }
.hf-detalhe { background: var(--panel); border-radius: 6px; box-shadow: var(--shadow); padding: 20px 22px; position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: auto; }
.hf-detalhe h3 { margin: 0 0 4px 0; font-size: 17px; font-weight: 600; letter-spacing: -.2px; }
.hf-detalhe .hf-regra { font-size: 12.5px; color: var(--text-dim); line-height: 1.5; margin: 0 0 12px 0; }
.hf-detalhe .hf-prox { font-size: 12.5px; color: var(--text); line-height: 1.5; background: var(--surface2); border-radius: 6px; padding: 10px 12px; margin: 0 0 14px 0; }
.hf-ind { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px 14px; margin: 0 0 16px 0; }
.hf-ind div b { display: block; font-size: 20px; font-weight: 700; letter-spacing: -.4px; font-variant-numeric: tabular-nums; }
.hf-ind div span { font-size: 12px; color: var(--text3); }
.hf-lista { width: 100%; border-collapse: collapse; font-size: 12px; }
.hf-lista td { padding: 8px 0; border-bottom: 1px solid rgba(135,135,153,.15); vertical-align: top; }
.hf-lista td:last-child { text-align: right; white-space: nowrap; padding-left: 8px; font-weight: 600; font-variant-numeric: tabular-nums; }
.hf-lista .hf-c { color: var(--text3); font-size: 11.5px; margin-top: 2px; }
.hf-mais { display: inline-block; margin-top: 12px; font: 600 13px inherit; font-family: inherit; color: var(--navy); background: transparent; border: 1.25px solid #878799; border-radius: 6px; padding: 6px 14px; cursor: pointer; }
.hf-mais:hover { background: rgba(36,36,62,.05); border-color: var(--navy); }
.hf-vazio { color: var(--text3); font-size: 13px; line-height: 1.5; }
.hf-rank { margin: 12px 0 0 0; padding: 0; list-style: none; }
.hf-rank li { display: flex; justify-content: space-between; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(135,135,153,.15); cursor: pointer; font-size: 13px; }
.hf-rank li:hover { color: var(--pink); }
.hf-rank li b { font-variant-numeric: tabular-nums; }
"""

V7_JS = r"""
// ===== HOMOLOGACAO v7: fluxograma em arvore =====
const HF_W = 780, HF_H = 1540, HF_NW = 190, HF_NH = 84;
const HF_X = {e: 10, c: 295, d: 580};            // esquerda (cobrado), centro (tronco), direita (gratuito / lateral)
const HF_Y = r => 12 + r * 130;
let HF_LARG = HF_W, HF_ESC = 1;   // largura logica do desenho e escala (se adaptam a largura da tela)
function hfMede(idCont, larguraBase) {
  const cont = document.getElementById(idCont); let cw = cont ? cont.clientWidth : 0; if (cw < 300) cw = 1100;
  const Wd = (cw > 1100 ? cw - 360 - 18 : cw) - 28;                  // largura util do diagrama (o detalhamento fica ao lado em telas largas)
  const s = Wd < larguraBase ? Wd / larguraBase : Math.min(1.3, Wd / larguraBase);
  return {s: s, Wc: Wd < larguraBase ? larguraBase : Math.round(Wd / s)};
}
function hfAjustaX(Wc, X, nw, base) { const d = Math.round((Wc - base) * 0.15); X.e = 10 + d; X.d = Wc - 10 - nw - d; X.c = Math.round((Wc - nw) / 2); }
const HF_POS = {
  cliente: [HF_X.c, HF_Y(0)], n1: [HF_X.c, HF_Y(1)], n2: [HF_X.c, HF_Y(2)], info: [HF_X.d, HF_Y(2)], refina: [HF_X.c, HF_Y(3)], decide: [HF_X.c, HF_Y(4)],
  tec: [HF_X.e, HF_Y(5)], aprcom: [HF_X.e, HF_Y(6)], orc: [HF_X.e, HF_Y(7)], assin: [HF_X.e, HF_Y(8)], n2com: [HF_X.e, HF_Y(9)],
  aprov: [HF_X.d, HF_Y(5)], n2apr: [HF_X.d, HF_Y(6)], prev: [HF_X.c, HF_Y(10)], agend: [HF_X.c, HF_Y(11)],
};
const HF_PAIS = {n1: ['cliente'], n2: ['n1'], refina: ['n2'], decide: ['refina'], tec: ['decide'], aprcom: ['tec'], orc: ['aprcom'], assin: ['orc'], n2com: ['assin'],
  aprov: ['decide'], n2apr: ['aprov'], prev: ['n2com', 'n2apr'], agend: ['prev']};
const HF_ROTULOS = [['tec', 'decide', 'cobrado', 0.5], ['aprov', 'decide', 'roadmap', 0.5]];
const HF_INFO = {
  cliente: {t: 'Cliente solicita melhoria', regra: 'Chamado de categoria Melhoria, preenchido no padrão.', prox: 'N1 ou Implantação levantam as informações e repassam para a fila Em atendimento - N2.'},
  n1: {regra: "Status Em atendimento.", prox: 'Levantadas as informações, repassar para a fila Em atendimento - N2. Se precisar de mais informações do cliente, coloca em Pendente usuário (Aguardando Cliente, sem tag).'},
  n2: {regra: "Status Em atendimento - N2, sem tag.", prox: 'O N2 confere se a melhoria já existe e falta só configuração, e se não é um bug. Se for aderente, move para Refinamento Suporte Melhoria. Se precisar de mais informações, coloca em Pendente usuário (Aguardando Cliente, sem tag).'},
  info: {regra: "Pendente usuário: status Aguardando Cliente, sem tag.", prox: 'N1 ou N2 precisa de mais informações e colocou o chamado em Pendente usuário. Quando o cliente responde, o chamado volta para quem pediu (N1 ou N2).'},
  refina: {regra: "Status Refinamento Suporte Melhoria, sem nenhuma tag.", prox: 'Aguarda a reunião de quarta, 14:00, com o time de Produto.'},
  decide: {t: 'Produto decide', regra: 'Decisão tomada na reunião de alinhamento.', prox: 'Falta informação: volta para Em atendimento - N2, sem tag. Roadmap: tag Aprovado PO. Cobrada do cliente: tag Estimativa Técnica.'},
  aprov: {regra: "Refinamento + tag Aprovado PO.", prox: 'Será feito pelo time de produto dentro das sprints. O chamado vai para Em atendimento - N2 para abrir a task.'},
  n2apr: {regra: "Em atendimento - N2 + tag Aprovado PO.", prox: 'N2 abre a task. Depois o chamado vai para Aguardando Desenvolvimento.'},
  tec: {regra: "Refinamento + tag Estimativa Técnica.", prox: 'Aguarda o time de desenvolvimento informar a quantidade de horas. Com as horas, o chamado vai para pendente usuário, com a tag, no nome do Diogo.'},
  aprcom: {regra: "Aguardando Cliente + só a tag Estimativa Técnica.", prox: 'Horas definidas, aguardando a aprovação comercial. Quando o cliente retorna, o CS cria a proposta.'},
  orc: {regra: "Em atendimento - CS + tags Estimativa Técnica e Estimativa Comercial.", prox: 'O CS monta a proposta comercial e a formaliza com o cliente.'},
  assin: {regra: "Aguardando Cliente + tag Estimativa Comercial.", prox: 'Proposta formal enviada. Depois da aprovação, o chamado vai para a fila do N2 abrir a task.'},
  n2com: {regra: "Em atendimento - N2 + tag Estimativa Comercial.", prox: 'N2 abre a task. Depois o chamado vai para Aguardando Desenvolvimento.'},
  prev: {regra: "Aguardando Desenvolvimento + tag Aprovado PO ou Estimativa Comercial, sem Previsão de solução.", prox: 'Aguarda a data de entrega. Com a data, ela é preenchida em Previsão de solução e o chamado entra na lista de próximas entregas.'},
  agend: {regra: "Aguardando Desenvolvimento + tag + Previsão de solução preenchida.", prox: 'Entrega agendada. Aparece na lista Próximas entregas, ordenada por data.'},
};
const HF_FIXOS = ['cliente', 'decide'];
const HF_MODOS = [['qtd', 'Quantidade'], ['media', 'Média parada'], ['maior', 'Mais antigo parado'], ['idade', 'Idade média'], ['velhos', 'Parados há mais de 15 dias']];
let hfModo = 'qtd', hfSel = null;

function hfIndicadores(itens) {
  if (!itens.length) return {qtd: 0, media: null, mediana: null, maior: null, idade: null, velhos: 0};
  const parado = itens.map(gmDiasParado);
  return {qtd: itens.length, media: gmMedia(parado), mediana: gmMediana(parado), maior: Math.max(...parado), idade: gmMedia(itens.map(gmDiasAberto)), velhos: parado.filter(d => d > 15).length};
}
function hfValor(ind) {
  if (hfModo === 'qtd') return String(ind.qtd);
  if (hfModo === 'velhos') return String(ind.velhos);
  const v = ind[hfModo];
  return v === null ? '–' : Math.round(v) + ' d';
}
function hfCadeia(k, acc) { acc = acc || new Set(); (HF_PAIS[k] || []).forEach(p => { acc.add(p + '>' + k); hfCadeia(p, acc); }); return acc; }

function hfCaixa(k) { const p = HF_POS[k]; return {x: p[0], y: p[1], w: HF_NW, h: HF_NH}; }
function hfCaminho(de, para) {
  const a = hfCaixa(de), b = hfCaixa(para);
  const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y, ym = (y1 + y2) / 2;
  return x1 === x2 ? `M${x1} ${y1} L${x2} ${y2 - 1}` : `M${x1} ${y1} L${x1} ${ym} L${x2} ${ym} L${x2} ${y2 - 1}`;
}
function hfSeta(x, y) { return `M${x - 5} ${y - 9} L${x} ${y} L${x + 5} ${y - 9} Z`; }

renderGmFluxo = function() {
  { const m = hfMede('gmFluxo', HF_W); HF_LARG = m.Wc; HF_ESC = m.s; hfAjustaX(m.Wc, HF_X, HF_NW, HF_W); }
  const todas = gmMelhorias(); todas.forEach(t => { t._gmE = gmEtapa(t); });
  const L = k => todas.filter(t => t._gmE === k);
  const cadeia = hfSel ? hfCadeia(hfSel) : new Set();
  let svg = '', nos = '', rotulos = '';
  Object.keys(HF_PAIS).forEach(k => HF_PAIS[k].forEach(p => {
    const on = cadeia.has(p + '>' + k), b = hfCaixa(k);
    svg += `<path class="hf-edge ${on ? 'on' : ''}" data-e="${p}>${k}" d="${hfCaminho(p, k)}"/><path class="hf-seta ${on ? 'on' : ''}" data-e="${p}>${k}" d="${hfSeta(b.x + b.w / 2, b.y)}"/>`;
  }));
  { const a = hfCaixa('n2'), b = hfCaixa('info'), y = a.y + a.h / 2;   // lateral: N2 <-> informacoes do cliente
    svg += `<path class="hf-edge lado" d="M${a.x + a.w} ${y} L${b.x} ${y}"/><path class="hf-seta" d="M${b.x - 9} ${y - 5} L${b.x} ${y} L${b.x - 9} ${y + 5} Z"/><path class="hf-seta" d="M${a.x + a.w + 9} ${y - 5} L${a.x + a.w} ${y} L${a.x + a.w + 9} ${y + 5} Z"/>`;
    rotulos += `<div class="hf-rotulo" style="left:${(a.x + a.w + b.x) / 2}px; top:${y - 14}px;">pede informação</div>`; }
  { const a1 = hfCaixa('n1'), b1 = hfCaixa('info'), ya = a1.y + a1.h / 2, xb = b1.x + b1.w / 2;   // o N1 tambem pode colocar em Pendente usuario
    svg += `<path class="hf-edge lado" data-e="n1>info" d="M${a1.x + a1.w} ${ya} L${xb} ${ya} L${xb} ${b1.y - 1}"/><path class="hf-seta" data-e="n1>info" d="${hfSeta(xb, b1.y)}"/>`;
    rotulos += `<div class="hf-rotulo" style="left:${(a1.x + a1.w + xb) / 2}px; top:${ya - 14}px;">pede informação</div>`; }
  HF_ROTULOS.forEach(([k, p, txt]) => { const a = hfCaixa(k), b = hfCaixa(p); rotulos += `<div class="hf-rotulo" style="left:${a.x + a.w / 2 + (k === 'tec' ? 40 : -40)}px; top:${(a.y + b.y + b.h) / 2}px;">${txt}</div>`; });
  Object.keys(HF_POS).forEach(k => {
    const p = HF_POS[k], info = HF_INFO[k] || {};
    const fixo = HF_FIXOS.indexOf(k) !== -1;
    const titulo = info.t || HML6_NOMES[k] || k;
    let cls = 'hf-node', v = '', s = '';
    if (fixo) { cls += k === 'cliente' ? ' hf-raiz' : ' hf-dec'; s = k === 'cliente' ? 'N1 ou Implantação' : 'reunião de quarta, 14:00'; }
    else {
      const itens = L(k), ind = hfIndicadores(itens);
      v = hfValor(ind);
      s = hfModo === 'qtd' ? (ind.media === null ? 'nenhum chamado' : 'média parado ' + Math.round(ind.media) + ' d') : HF_MODOS.find(m => m[0] === hfModo)[1].toLowerCase() + ' · ' + ind.qtd + (ind.qtd === 1 ? ' chamado' : ' chamados');
      cls += !itens.length ? ' vazio' : ind.media > 15 ? ' danger' : ind.media > 7 ? ' warn' : '';
    }
    if (hfSel === k) cls += ' sel';
    nos += `<button type="button" class="${cls}" data-k="${k}" style="left:${p[0]}px; top:${p[1]}px;" onclick="hfSelecionar('${k}')"><div class="hf-t">${esc(titulo)}</div>${v !== '' ? `<div class="hf-v">${v}</div>` : ''}<div class="hf-s">${esc(s)}</div></button>`;
  });
  document.getElementById('gmFluxo').innerHTML = `<div class="hf-wrap">
    <div class="hf-topo"><span class="hf-rot">Exibir em cada etapa:</span>
      <span class="seg-toggle" id="hfModoToggle" role="group" aria-label="Indicador exibido">${HF_MODOS.map(m => `<button type="button" class="${m[0] === hfModo ? 'active' : ''}" onclick="hfMudaModo('${m[0]}')">${m[1]}</button>`).join('')}</span></div>
    <div class="hf-grid"><div class="hf-diagrama" id="hfDiag"><div class="hf-canvas" id="hfCanvas" style="width:${HF_LARG}px; height:${HF_H}px;">
      <svg class="hf-svg" width="${HF_LARG}" height="${HF_H}" viewBox="0 0 ${HF_LARG} ${HF_H}" aria-hidden="true">${svg}</svg>${rotulos}${nos}</div></div>
    <aside class="hf-detalhe" id="hfDet"></aside></div></div>`;
  hfEscala(); hfDetalhe(); hmlDestacaEtapa();
};
function hfEscala() {
  const d = document.getElementById('hfDiag'), c = document.getElementById('hfCanvas'); if (!d || !c) return;
  const s = HF_ESC;
  c.style.transform = 'scale(' + s + ')'; d.style.height = (HF_H * s + 36) + 'px';
}
window.addEventListener('resize', () => { clearTimeout(window._hfT); window._hfT = setTimeout(() => { const g = document.getElementById('gmFluxo'); if (g && g.offsetParent) renderGmFluxo(); }, 150); });
function hfSelecionar(k) { hfSel = hfSel === k ? null : k; renderGmFluxo(); }
function hfMudaModo(m) { hfModo = m; renderGmFluxo(); }
hmlDestacaEtapa = function() {
  document.querySelectorAll('#gmFluxo .hf-node.fl-atual').forEach(n => n.classList.remove('fl-atual'));
  if (!hmlMelhoriaSel) return;
  const k = gmEtapa(hmlMelhoriaSel), no = k && document.querySelector('#gmFluxo .hf-node[data-k="' + k + '"]');
  if (no) no.classList.add('fl-atual');
};

function hfDetalhe() {
  const el = document.getElementById('hfDet'); if (!el) return;
  const todas = gmMelhorias(); todas.forEach(t => { t._gmE = gmEtapa(t); });
  if (!hfSel) {
    const etapas = Object.keys(HML6_NOMES).filter(k => HF_POS[k] && HF_FIXOS.indexOf(k) === -1 && k !== 'decide').map(k => ({k, it: todas.filter(t => t._gmE === k)})).filter(e => e.it.length)
      .sort((a, b) => hfIndicadores(b.it).media - hfIndicadores(a.it).media).slice(0, 5);
    el.innerHTML = `<h3>Selecione uma etapa</h3><p class="hf-regra">Clique em uma etapa do fluxograma para ver a regra, os indicadores e os chamados dela. O caminho até a etapa fica em rosa.</p>
      ${etapas.length ? '<div class="hf-regra" style="margin:0;">Etapas mais paradas agora</div><ul class="hf-rank">' + etapas.map(e => `<li onclick="hfSelecionar('${e.k}')"><span>${esc(HML6_NOMES[e.k])}</span><b>${Math.round(hfIndicadores(e.it).media)} d</b></li>`).join('') + '</ul>' : '<p class="hf-vazio">Nenhum chamado nas etapas acompanhadas.</p>'}`;
    return;
  }
  const info = HF_INFO[hfSel] || {}, titulo = info.t || HML6_NOMES[hfSel] || hfSel;
  let corpo = `<h3>${esc(titulo)}</h3><p class="hf-regra">${esc(info.regra || '')}</p><div class="hf-prox"><b>Próximo passo.</b> ${esc(info.prox || '')}</div>`;
  if (HF_FIXOS.indexOf(hfSel) === -1) {
    const itens = todas.filter(t => t._gmE === hfSel), ind = hfIndicadores(itens);
    const f = v => v === null ? '–' : Math.round(v) + ' d';
    corpo += `<div class="hf-ind"><div><b>${ind.qtd}</b><span>chamados</span></div><div><b>${f(ind.media)}</b><span>média parada</span></div><div><b>${f(ind.maior)}</b><span>mais antigo parado</span></div><div><b>${f(ind.idade)}</b><span>idade média</span></div><div><b>${ind.velhos}</b><span>parados há mais de 15 dias</span></div><div><b>${f(ind.mediana)}</b><span>mediana parada</span></div></div>`;
    if (itens.length) {
      const top = itens.slice().sort((a, b) => gmDiasParado(b) - gmDiasParado(a)).slice(0, 8);
      corpo += `<table class="hf-lista"><tbody>${top.map(t => `<tr><td>${ticketLink(t.id, t.protocol)} ${esc((t.subject || '').slice(0, 60))}${gmSelos(t)}<div class="hf-c">${esc(t.clientOrg || '-')}${t.lastComment ? ' · ' + esc((t.lastComment.description || '').replace(/\s+/g, ' ').slice(0, 70)) : ''}</div></td><td>${Math.round(gmDiasParado(t))} d</td></tr>`).join('')}</tbody></table>`;
      corpo += `<button type="button" class="hf-mais" onclick="gmAbreLista(${jsStr(titulo)}, [${itens.map(t => t.id).join(',')}])">Ver os ${itens.length} chamados</button>`;
    } else corpo += '<p class="hf-vazio">Nenhum chamado nesta etapa agora.</p>';
  }
  el.innerHTML = corpo;
}
window.addEventListener('load', () => setTimeout(hfEscala, 50));
"""
