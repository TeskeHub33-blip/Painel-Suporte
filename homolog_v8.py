# -*- coding: utf-8 -*-
"""Homologacao v8: Fluxo de bugs como fluxograma em arvore interativo (mesmo desenho do Fluxo de melhorias).

SO' a versao de homologacao usa este JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Etapas (status do Movidesk + log do Azure DevOps, regras de bug do painel):
  Em atendimento N1            Em atendimento
  Repasse ao N2                SLA de repasse: bug alto 1h, bug medio 8h (urgente 15 min)
  Em analise no N2             Em atendimento - N2
  Aguardando cliente           Aguardando Cliente        (lateral: pede informacao / cliente responde)
  Aguardando terceiros         Aguardando Terceiros      (lateral)
  Na fila de desenvolvimento   Aguardando Desenvolvimento (task aberta)
  Em validacao no devops       ultimo log do Azure indica Validacao
  Em impedimento no devops     ultimo log do Azure indica Impedimento
  N2 reage ao log              valida com o cliente ou devolve ao dev
"""

V8_JS = r"""
// ===== HOMOLOGACAO v8: fluxograma de bugs =====
const HFB = {
  W: 780, H: 1040, nw: 190, nh: 84, modo: 'qtd', sel: null,
  X: {e: 10, c: 295, d: 580}, Y: r => 12 + r * 130,
  modos: [['qtd', 'Quantidade'], ['media', 'Média parada'], ['maior', 'Mais antigo parado'], ['idade', 'Idade média'], ['sla', 'Com SLA vencido']],
  pais: {n1: ['cliente'], repasse: ['n1'], n2: ['repasse'], dev: ['n2'], valid: ['dev'], imped: ['dev'], reacao: ['valid', 'imped'], fim: ['reacao']},
  fixos: ['cliente', 'repasse', 'reacao', 'fim'],
  nomes: {cliente: 'Cliente reporta o problema', n1: 'Em atendimento N1', repasse: 'Repasse ao N2', n2: 'Em análise no N2', cli: 'Aguardando cliente', terc: 'Aguardando terceiros',
    dev: 'Na fila de desenvolvimento', valid: 'Em validação no devops', imped: 'Em impedimento no devops', reacao: 'N2 reage ao log do devops', fim: 'Chamado resolvido'},
  sub: {cliente: 'N1 atende', repasse: 'alto 1h · médio 8h', reacao: 'valida ou devolve ao dev', fim: 'fim do fluxo'},
  info: {
    cliente: {regra: 'Chamado de categoria Bug aberto pelo cliente ou pelo time.', prox: 'O N1 atende, confirma o problema e coleta as informações.'},
    n1: {regra: 'Status Em atendimento, categoria Bug.', prox: 'Confirmado o bug, o N1 repassa para a fila Em atendimento - N2 dentro do prazo de repasse.'},
    repasse: {regra: 'SLA de repasse para o N2: urgente 15 minutos, bug alto 1 hora, bug médio 8 horas (desde que fornecida solução de contorno).', prox: 'O tempo é contado da abertura até o chamado entrar em Em atendimento - N2, sem o tempo em Aguardando Cliente.'},
    n2: {regra: 'Status Em atendimento - N2, categoria Bug.', prox: 'O N2 analisa o problema e abre a task. Depois o chamado vai para Aguardando Desenvolvimento.'},
    cli: {regra: 'Status Aguardando Cliente, categoria Bug.', prox: 'O time pediu informação ou retorno ao cliente. Quando ele responde, o chamado volta ao atendimento.'},
    terc: {regra: 'Status Aguardando Terceiros, categoria Bug.', prox: 'Depende de um parceiro ou órgão. Entra no Aging quando fica 48 horas sem atualização.'},
    dev: {regra: 'Status Aguardando Desenvolvimento (ou o nome antigo "fila Bugs"), sem log de validação ou impedimento.', prox: 'A task está com o desenvolvimento. O log do Azure DevOps indica quando vai para validação ou impedimento.'},
    valid: {regra: 'O último log do Azure DevOps no chamado indica Validação.', prox: 'A correção está sendo validada. O N2 confirma com o cliente ou devolve ao desenvolvimento.'},
    imped: {regra: 'O último log do Azure DevOps no chamado indica Impedimento.', prox: 'A task está parada por um impedimento. O N2 trata o motivo informado no log.'},
    reacao: {regra: 'Depois do último log de Validação ou Impedimento.', prox: 'Validado: o N2 coloca em Aguardando Cliente. Não resolveu: devolve para a fila de desenvolvimento.'},
    fim: {regra: 'Chamado resolvido.', prox: 'Entra nos indicadores de resolvidos do mês.'},
  },
};
HFB.pos = {cliente: ['c', 0], n1: ['c', 1], repasse: ['c', 2], n2: ['c', 3], cli: ['d', 3], terc: ['e', 3], dev: ['c', 4], valid: ['e', 5], imped: ['d', 5], reacao: ['c', 6], fim: ['c', 7]};
HFB.laterais = [['n2', 'cli', 'informação'], ['n2', 'terc', 'parceiro']];
let hfbMarcado = null;

function hfbEtapa(t) {
  const st = t.status; let k = null;
  if (st === 'Em atendimento') k = 'n1';
  else if (st === 'Em atendimento - N2') k = 'n2';
  else if (isDevQueueStatus(st)) k = 'dev';
  else if (st === 'Aguardando Cliente') k = 'cli';
  else if (st === 'Aguardando Terceiros') k = 'terc';
  else return null;
  if (k === 'n1' || k === 'n2' || k === 'dev') {
    let sub = null; try { sub = devopsSubStatusForTicket(t); } catch (e) {}
    if (sub) { const s = (sub.status || '').toLowerCase(); if (s.indexOf('impediment') !== -1) return 'imped'; if (s.indexOf('valida') !== -1) return 'valid'; }
  }
  return k;
}
function hfbAjusta() { const m = hfMede('gbFluxo', 780); HFB.W = m.Wc; HFB.esc = m.s; hfAjustaX(m.Wc, HFB.X, HFB.nw, 780); }
function hfbCaixa(k) { const p = HFB.pos[k]; return {x: HFB.X[p[0]], y: HFB.Y(p[1]), w: HFB.nw, h: HFB.nh}; }
function hfbCadeia(k, acc) { acc = acc || new Set(); (HFB.pais[k] || []).forEach(p => { acc.add(p + '>' + k); hfbCadeia(p, acc); }); return acc; }
function hfbCaminho(de, para) {
  const a = hfbCaixa(de), b = hfbCaixa(para);
  const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y, ym = (y1 + y2) / 2;
  return x1 === x2 ? `M${x1} ${y1} L${x2} ${y2 - 1}` : `M${x1} ${y1} L${x1} ${ym} L${x2} ${ym} L${x2} ${y2 - 1}`;
}
function hfbValor(ind) {
  if (HFB.modo === 'qtd') return String(ind.qtd);
  if (HFB.modo === 'sla') return String(ind.sla);
  const v = ind[HFB.modo]; return v === null ? '–' : Math.round(v) + ' d';
}
function hfbInd(itens) {
  const base = hfIndicadores(itens);
  base.sla = itens.filter(t => t._slaVencido).length;
  return base;
}

function hfbRender() {
  const alvo = document.getElementById('gbFluxo'); if (!alvo) return;
  hfbAjusta();
  const todas = TICKETS.filter(t => t.category === 'Bug'); todas.forEach(t => { t._gbF = hfbEtapa(t); });
  const L = k => todas.filter(t => t._gbF === k);
  const cadeia = HFB.sel ? hfbCadeia(HFB.sel) : new Set();
  let svg = '', nos = '', rot = '';
  Object.keys(HFB.pais).forEach(k => HFB.pais[k].forEach(p => {
    const on = cadeia.has(p + '>' + k), b = hfbCaixa(k);
    svg += `<path class="hf-edge ${on ? 'on' : ''}" data-e="${p}>${k}" d="${hfbCaminho(p, k)}"/><path class="hf-seta ${on ? 'on' : ''}" data-e="${p}>${k}" d="${hfSeta(b.x + b.w / 2, b.y)}"/>`;
  }));
  HFB.laterais.forEach(([de, para, txt]) => {
    const a = hfbCaixa(de), b = hfbCaixa(para), y = a.y + a.h / 2, dir = b.x > a.x;
    const x1 = dir ? a.x + a.w : a.x, x2 = dir ? b.x : b.x + b.w, s = dir ? 1 : -1;
    svg += `<path class="hf-edge lado" d="M${x1} ${y} L${x2} ${y}"/><path class="hf-seta" d="M${x2 - 9 * s} ${y - 5} L${x2} ${y} L${x2 - 9 * s} ${y + 5} Z"/><path class="hf-seta" d="M${x1 + 9 * s} ${y - 5} L${x1} ${y} L${x1 + 9 * s} ${y + 5} Z"/>`;
    rot += `<div class="hf-rotulo" style="left:${(x1 + x2) / 2}px; top:${y - 14}px;">${txt}</div>`;
  });
  const modoNome = HFB.modos.find(m => m[0] === HFB.modo)[1].toLowerCase();
  Object.keys(HFB.pos).forEach(k => {
    const c = hfbCaixa(k), fixo = HFB.fixos.indexOf(k) !== -1;
    let cls = 'hf-node', v = '', s = HFB.sub[k] || '';
    if (fixo) cls += k === 'cliente' ? ' hf-raiz' : (k === 'repasse' ? ' hf-dec' : ' hf-fixo');
    else {
      const itens = L(k), ind = hfbInd(itens); v = hfbValor(ind);
      s = HFB.modo === 'qtd' ? (ind.media === null ? 'nenhum bug' : 'média parado ' + Math.round(ind.media) + ' d') : modoNome + ' · ' + ind.qtd + (ind.qtd === 1 ? ' bug' : ' bugs');
      cls += !itens.length ? ' vazio' : ind.media > 15 ? ' danger' : ind.media > 7 ? ' warn' : '';
    }
    if (HFB.sel === k) cls += ' sel';
    nos += `<button type="button" class="${cls}" data-k="${k}" style="left:${c.x}px; top:${c.y}px;" onclick="hfbSelecionar('${k}')"><div class="hf-t">${esc(HFB.nomes[k])}</div>${v !== '' ? `<div class="hf-v">${v}</div>` : ''}<div class="hf-s">${esc(s)}</div></button>`;
  });
  alvo.innerHTML = `<div class="hf-wrap">
    <div class="hf-topo"><span class="hf-rot">Exibir em cada etapa:</span>
      <span class="seg-toggle" role="group" aria-label="Indicador exibido">${HFB.modos.map(m => `<button type="button" class="${m[0] === HFB.modo ? 'active' : ''}" onclick="hfbMudaModo('${m[0]}')">${m[1]}</button>`).join('')}</span></div>
    <div class="hf-grid"><div class="hf-diagrama" id="hfbDiag"><div class="hf-canvas" id="hfbCanvas" style="width:${HFB.W}px; height:${HFB.H}px;">
      <svg class="hf-svg" width="${HFB.W}" height="${HFB.H}" viewBox="0 0 ${HFB.W} ${HFB.H}" aria-hidden="true">${svg}</svg>${rot}${nos}</div></div>
    <aside class="hf-detalhe" id="hfbDet"></aside></div></div>`;
  hfbEscala(); hfbDetalhe(todas); hfbDestaca();
}
function hfbEscala() {
  const d = document.getElementById('hfbDiag'), c = document.getElementById('hfbCanvas'); if (!d || !c) return;
  const s = HFB.esc || 1;
  c.style.transform = 'scale(' + s + ')'; d.style.height = (HFB.H * s + 36) + 'px';
}
window.addEventListener('resize', () => { clearTimeout(window._hfbT); window._hfbT = setTimeout(() => { const g = document.getElementById('gbFluxo'); if (g && g.offsetParent) hfbRender(); }, 150); });
function hfbSelecionar(k) { HFB.sel = HFB.sel === k ? null : k; hfbRender(); }
function hfbMudaModo(m) { HFB.modo = m; hfbRender(); }
function hfbDestaca() {
  document.querySelectorAll('#gbFluxo .hf-node.fl-atual').forEach(n => n.classList.remove('fl-atual'));
  if (!hfbMarcado) return;
  const k = hfbEtapa(hfbMarcado), no = k && document.querySelector('#gbFluxo .hf-node[data-k="' + k + '"]');
  if (no) no.classList.add('fl-atual');
}
function hfbDetalhe(todas) {
  const el = document.getElementById('hfbDet'); if (!el) return;
  if (!HFB.sel) {
    const etapas = Object.keys(HFB.pos).filter(k => HFB.fixos.indexOf(k) === -1).map(k => ({k, it: todas.filter(t => t._gbF === k)})).filter(e => e.it.length)
      .sort((a, b) => hfIndicadores(b.it).media - hfIndicadores(a.it).media).slice(0, 5);
    el.innerHTML = `<h3>Selecione uma etapa</h3><p class="hf-regra">Clique em uma etapa do fluxograma para ver a regra, os indicadores e os bugs dela. O caminho até a etapa fica em rosa.</p>
      ${etapas.length ? '<div class="hf-regra" style="margin:0;">Etapas mais paradas agora</div><ul class="hf-rank">' + etapas.map(e => `<li onclick="hfbSelecionar('${e.k}')"><span>${esc(HFB.nomes[e.k])}</span><b>${Math.round(hfIndicadores(e.it).media)} d</b></li>`).join('') + '</ul>' : '<p class="hf-vazio">Nenhum bug nas etapas acompanhadas.</p>'}`;
    return;
  }
  const k = HFB.sel, info = HFB.info[k] || {};
  let corpo = `<h3>${esc(HFB.nomes[k])}</h3><p class="hf-regra">${esc(info.regra || '')}</p><div class="hf-prox"><b>Próximo passo.</b> ${esc(info.prox || '')}</div>`;
  if (HFB.fixos.indexOf(k) === -1) {
    const itens = todas.filter(t => t._gbF === k), ind = hfbInd(itens), f = v => v === null ? '–' : Math.round(v) + ' d';
    const alta = itens.filter(t => t.urgency === 'Alta').length, media = itens.filter(t => t.urgency === 'Média').length;
    corpo += `<div class="hf-ind"><div><b>${ind.qtd}</b><span>bugs</span></div><div><b>${f(ind.media)}</b><span>média parada</span></div><div><b>${f(ind.maior)}</b><span>mais antigo parado</span></div><div><b>${f(ind.idade)}</b><span>idade média</span></div><div><b>${alta}</b><span>urgência alta</span></div><div><b>${media}</b><span>urgência média</span></div><div><b>${ind.sla}</b><span>com SLA vencido</span></div><div><b>${f(ind.mediana)}</b><span>mediana parada</span></div></div>`;
    if (itens.length) {
      const top = itens.slice().sort((a, b) => gmDiasParado(b) - gmDiasParado(a)).slice(0, 8);
      corpo += `<table class="hf-lista"><tbody>${top.map(t => `<tr><td>${ticketLink(t.id, t.protocol)} ${esc((t.subject || '').slice(0, 60))} ${gbUrg(t)}<div class="hf-c">${esc(t.clientOrg || '-')}${t._slaVencido ? ' · SLA vencido' : ''}${t.lastComment ? ' · ' + esc((t.lastComment.description || '').replace(/\s+/g, ' ').slice(0, 60)) : ''}</div></td><td>${Math.round(gmDiasParado(t))} d</td></tr>`).join('')}</tbody></table>`;
      corpo += `<button type="button" class="hf-mais" onclick="gmAbreLista(${jsStr(HFB.nomes[k])}, [${itens.map(t => t.id).join(',')}])">Ver os ${itens.length} bugs</button>`;
    } else corpo += '<p class="hf-vazio">Nenhum bug nesta etapa agora.</p>';
  }
  el.innerHTML = corpo;
}

// sub-aba Fluxo dentro de Bugs
const _v8Sgb = setGbSub;
setGbSub = function(s) {
  const f = document.getElementById('gbFluxo');
  if (s !== 'fluxo') { if (f) f.style.display = 'none'; _v8Sgb(s); return; }
  gbSub = 'fluxo';
  document.querySelectorAll('#gbSubToggle button').forEach(b => b.classList.toggle('active', b.dataset.sub === 'fluxo'));
  ['gbAcomp', 'gbIndic', 'gbRecor'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
  f.style.display = '';
  hfbRender();
};
// busca de bug: mostra a etapa e marca no fluxograma
const _v8Busca = hmlBuscaChamado;
hmlBuscaChamado = function(p) {
  _v8Busca(p);
  if (p !== 'gbBusca') return;
  const t = findTicketByProtocol(document.getElementById('gbBuscaInput').value);
  if (!t || t.category !== 'Bug' || t._created === undefined || t.resolvedIn) return;
  hfbMarcado = t;
  const k = hfbEtapa(t), nome = k ? HFB.nomes[k] : 'status ' + (t.status || '-');
  const card = document.querySelector('#gbBuscaRes .hml-exec');
  if (card) card.insertAdjacentHTML('beforeend', `<div class="hml-exec-bloco"><div class="k">Etapa no fluxo de bugs</div><div class="v">${esc(nome)} <button type="button" class="hf-mais" style="margin:0 0 0 8px; padding:3px 10px;" onclick="setGiSub('bugs'); setGbSub('fluxo');">Ver no fluxo</button></div></div>`);
  if (document.getElementById('gbFluxo').style.display !== 'none') hfbRender();
};
window.addEventListener('load', () => setTimeout(hfbEscala, 50));
"""


def aplicar_v8(html):
    html = html.replace('<button type="button" data-sub="recor" onclick="setGbSub(\'recor\')">Recorrências</button>',
                        '<button type="button" data-sub="recor" onclick="setGbSub(\'recor\')">Recorrências</button>\n'
                        '        <button type="button" data-sub="fluxo" onclick="setGbSub(\'fluxo\')">Fluxo</button>', 1)
    html = html.replace('<div id="gbRecor" style="display:none;"></div>',
                        '<div id="gbRecor" style="display:none;"></div>\n    <div id="gbFluxo" style="display:none;"></div>', 1)
    return html
