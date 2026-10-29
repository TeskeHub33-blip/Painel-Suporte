# -*- coding: utf-8 -*-
"""Homologacao v6: fluxo de melhorias remontado com as regras de negocio de 29/10/2026.

SO' a versao de homologacao usa este CSS/JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Tags: Estimativa Tecnica, Estimativa Comercial, Aprovado PO (ou "Aprovado produto").
Etapas (status + tags):
  Em atendimento N1               Em atendimento
  Aguardando validacao do N2      Em atendimento - N2, sem tag
  Aguardando informacoes          Aguardando Cliente, sem tag
  Aguardando reuniao              Refinamento Suporte Melhoria, sem nenhuma tag
  Aprovado pelo produto           Refinamento + Aprovado PO (task a abrir)
  N2 abrindo a task (roadmap)     Em atendimento - N2 + Aprovado PO
  Aguardando estimativa tecnica   Refinamento + Estimativa Tecnica
  Aguardando aprovacao comercial  Aguardando Cliente + so' Estimativa Tecnica
  Aguardando orcamento            Em atendimento - CS + Estimativa Tecnica e Comercial
  Aguardando assinatura           Aguardando Cliente + Estimativa Comercial
  N2 abrindo a task (cobrado)     Em atendimento - N2 + Estimativa Comercial
  Aguardando previsao de entrega  Aguardando Desenvolvimento + (Aprovado PO ou Estimativa Comercial), sem Previsao de solucao
  Entrega agendada                o mesmo, com Previsao de solucao preenchida -> lista "Proximas entregas"
  Aguardando Desenvolvimento sem tag = backlog antigo (fora do fluxo)
"""

V6_CSS = """
/* ===== HOMOLOGACAO v6: fluxo de melhorias com as regras de 29/10 ===== */
#gmKanbanBox .gm-board { grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)) !important; overflow-x: visible; }
#giSub_melhorias #gmKpis .kpi { display: block !important; }
#gmFluxo .fl-node { max-width: 215px; flex: 1 0 185px; }
#gmFluxo .fl-nota { font-size: 12px; color: var(--text3); margin: 0 0 12px 0; max-width: 80ch; line-height: 1.5; }
"""

V6_JS = r"""
// ===== HOMOLOGACAO v6: etapas de melhorias (status + tags) =====
const HML6_COLS = [
  {k: 'n1', t: 'Em atendimento N1', who: "Status 'Em atendimento' · N1 e Implantação levantam as informações e repassam ao N2; se precisar de mais informações, vai para Pendente usuário"},
  {k: 'n2', t: 'Aguardando validação do N2', who: "Status 'Em atendimento - N2' sem tag · o N2 confere se já existe, se falta configuração ou se é bug; se precisar de mais informações, vai para Pendente usuário"},
  {k: 'info', t: 'Aguardando informações do cliente', who: "Pendente usuário: status 'Aguardando Cliente' sem tag · N1 ou N2 precisa de mais informações"},
  {k: 'refina', t: 'Aguardando reunião de alinhamento', who: "Status 'Refinamento Suporte Melhoria' sem nenhuma tag · quarta 14:00 com Produto", key: true},
  {k: 'aprov', t: 'Aprovado pelo produto · task a abrir', who: "Refinamento + tag Aprovado PO · volta ao N2 para abrir a task"},
  {k: 'n2apr', t: 'N2 abrindo a task (roadmap)', who: "Em atendimento - N2 + tag Aprovado PO"},
  {k: 'tec', t: 'Aguardando estimativa técnica', who: "Refinamento + tag Estimativa Técnica · o dev informa as horas"},
  {k: 'aprcom', t: 'Aguardando aprovação comercial', who: "Aguardando Cliente + só a tag Estimativa Técnica · horas definidas, com o Diogo"},
  {k: 'orc', t: 'Aguardando orçamento', who: "Em atendimento - CS + tags Estimativa Técnica e Comercial · o CS monta a proposta formal"},
  {k: 'assin', t: 'Aguardando assinatura do cliente', who: "Aguardando Cliente + tag Estimativa Comercial · proposta formal enviada"},
  {k: 'n2com', t: 'N2 abrindo a task (cobrado)', who: "Em atendimento - N2 + tag Estimativa Comercial"},
  {k: 'prev', t: 'Aguardando previsão de entrega', who: "Aguardando Desenvolvimento + tag Aprovado PO ou Estimativa Comercial, sem Previsão de solução"},
];
GM_COLS.splice(0, GM_COLS.length, ...HML6_COLS);
const HML6_NOMES = Object.fromEntries(HML6_COLS.map(c => [c.k, c.t]));
HML6_NOMES.agend = 'Entrega agendada'; HML6_NOMES.decide = 'Produto decide';

gmEtapa = function(t) {
  const tec = gmTagTem(t, 'estimativa t'), com = gmTagTem(t, 'estimativa c'), apr = gmTagTem(t, 'aprovado');
  const st = t.status;
  if (st === 'Em atendimento') return 'n1';
  if (st === 'Em atendimento - N2') return apr ? 'n2apr' : (com ? 'n2com' : 'n2');
  if (st === GM_ST_REFINAMENTO) return apr ? 'aprov' : (tec ? 'tec' : 'refina');
  if (st === 'Em atendimento - CS') return tec && com ? 'orc' : null;
  if (st === 'Aguardando Cliente') return com ? 'assin' : (tec ? 'aprcom' : (apr ? null : 'info'));
  if (st === GM_ST_DEV) return apr || com ? (t._sla ? 'agend' : 'prev') : null;
  return null;
};
hmlChaveEtapaMel = function(t) { return gmEtapa(t); };
gmSelos = function(t) {
  let h = '';
  if (gmTagTem(t, 'aprovado')) h += ' <span class="gm-selo gm-ok">Aprovado PO</span>';
  if (gmTagTem(t, 'estimativa t')) h += ' <span class="gm-selo gm-info">Estimativa Técnica</span>';
  if (gmTagTem(t, 'estimativa c')) h += ' <span class="gm-selo gm-info">Estimativa Comercial</span>';
  return h;
};

// passos no resumo executivo: caminho gratuito, cobrado ou o trecho comum enquanto Produto ainda nao decidiu
hmlPassosMelhoria = function(t) {
  const k = gmEtapa(t);
  const tec = gmTagTem(t, 'estimativa t'), com = gmTagTem(t, 'estimativa c'), apr = gmTagTem(t, 'aprovado');
  let caminho;
  if (apr || ['aprov', 'n2apr'].indexOf(k) !== -1) caminho = ['n1', 'n2', 'refina', 'aprov', 'n2apr', 'prev', 'agend'];
  else if (tec || com || ['tec', 'aprcom', 'orc', 'assin', 'n2com'].indexOf(k) !== -1) caminho = ['n1', 'n2', 'refina', 'tec', 'aprcom', 'orc', 'assin', 'n2com', 'prev', 'agend'];
  else caminho = ['n1', 'n2', 'refina', 'decide'];
  const idx = k ? caminho.indexOf(k) : -1;
  if (idx === -1) {
    const onde = k ? HML6_NOMES[k] : (t.status === GM_ST_DEV ? 'Aguardando Desenvolvimento sem tag (backlog)' : `status ${t.status || '-'}`);
    return `<div class="hml-exec-bloco"><div class="k">Etapa no fluxo de melhorias</div><div class="v">${esc(onde)}${k === 'info' ? ' · volta ao N2 quando o cliente responder' : ' · fora do caminho principal'}</div></div>`;
  }
  const itens = caminho.map((c, i) => `<div class="hml-passo ${i < idx ? 'feito' : i === idx ? 'atual' : ''}">${i === idx ? '<small>Etapa atual</small>' : ''}${esc(HML6_NOMES[c])}</div>`).join('');
  return `<div class="hml-exec-bloco"><div class="k">Etapa no fluxo de melhorias</div><div class="hml-passos">${itens}</div></div>`;
};
hmlDestacaEtapa = function() {
  document.querySelectorAll('#gmFluxo .fl-node.fl-atual').forEach(n => n.classList.remove('fl-atual'));
  if (!hmlMelhoriaSel) return;
  const k = gmEtapa(hmlMelhoriaSel);
  const no = k && document.querySelector('#gmFluxo .fl-node[data-k="' + k + '"]');
  if (no) no.classList.add('fl-atual');
};

// ---------- Fluxo animado com as etapas novas
renderGmFluxo = function() {
  const todas = gmMelhorias(); todas.forEach(t => { t._gmE = gmEtapa(t); });
  const L = k => todas.filter(t => t._gmE === k);
  const no = (k, itens, sub) => {
    const titulo = HML6_NOMES[k];
    const parado = itens.length ? gmMedia(itens.map(gmDiasParado)) : 0;
    const cls = itens.length && parado > 15 ? ' fl-danger' : itens.length && parado > 7 ? ' fl-warn' : '';
    const pulso = itens.some(t => gmDiasParado(t) > 30) ? ' fl-pulse' : '';
    return `<div class="fl-node${cls}${pulso}" data-k="${k}" tabindex="0" role="button" onclick="gmAbreLista(${jsStr(titulo)}, [${itens.map(t => t.id).join(',')}])" onkeydown="if(event.key==='Enter')this.click()">
      <div class="fl-t">${titulo}</div><div class="fl-n" data-alvo="${itens.length}">0</div>
      <div class="fl-s">${sub}${itens.length ? ' · média parado ' + gmDias(parado) : ''}</div><div class="fl-bar"></div></div>`;
  };
  const fixo = (titulo, texto, extra) => `<div class="fl-node ${extra || ''}" style="cursor:default;"><div class="fl-t">${titulo}</div><div class="fl-s" style="margin-top:6px;">${texto}</div></div>`;
  const seta = rot => `<div class="fl-arrow">${rot ? '<span>' + rot + '</span>' : ''}</div>`;
  const agend = L('agend').filter(t => t._sla).sort((a, b) => a._sla - b._sla);
  const proxima = agend.find(t => t._sla >= NOW) || agend[0];
  document.getElementById('gmFluxo').innerHTML = `<div class="fl-wrap">
    <p class="fl-nota">Cada etapa é identificada pelo status do chamado e pelas tags Aprovado PO, Estimativa Técnica e Estimativa Comercial. Clique em uma etapa para ver os chamados. A barra e a cor mostram há quanto tempo, em média, estão sem atualização.</p>
    <div class="fl-lane"><h3>Entrada e análise</h3><div class="fl-row">
      ${fixo('Cliente solicita melhoria', 'N1 ou Implantação levantam as informações e repassam ao N2', 'fl-ponto')}${seta()}
      ${no('n1', L('n1'), "Status Em atendimento")}${seta('repassa ao N2')}
      ${no('n2', L('n2'), "Em atendimento - N2 sem tag")}${seta('se aderente')}
      ${no('refina', L('refina'), "Refinamento sem tag · quarta 14:00")}${seta()}
      ${fixo('Produto decide', 'Falta informação: volta ao N2 sem tag. Roadmap: tag Aprovado PO. Cobrada: tag Estimativa Técnica.', 'fl-dec')}
    </div></div>
    <div class="fl-lane"><h3>Quando falta informação</h3><div class="fl-row">
      ${no('info', L('info'), "Aguardando Cliente sem tag · volta ao N2 quando o cliente responde")}
    </div></div>
    <div class="fl-lane"><h3>Caminho gratuito — roadmap · depois da task aberta, segue para Aguardando previsão de entrega</h3><div class="fl-row">
      ${no('aprov', L('aprov'), "Refinamento + Aprovado PO")}${seta('volta ao N2')}
      ${no('n2apr', L('n2apr'), "Em atendimento - N2 + Aprovado PO")}
    </div></div>
    <div class="fl-lane"><h3>Caminho cobrado — estimativa e orçamento · depois da task aberta, segue para Aguardando previsão de entrega</h3><div class="fl-row">
      ${no('tec', L('tec'), "Refinamento + Estimativa Técnica")}${seta('horas definidas')}
      ${no('aprcom', L('aprcom'), "Aguardando Cliente + só Estimativa Técnica")}${seta('cliente retorna')}
      ${no('orc', L('orc'), "Em atendimento - CS + as duas tags")}${seta('proposta enviada')}
      ${no('assin', L('assin'), "Aguardando Cliente + Estimativa Comercial")}${seta('assinada')}
      ${no('n2com', L('n2com'), "Em atendimento - N2 + Estimativa Comercial")}
    </div></div>
    <div class="fl-lane"><h3>Final dos dois caminhos</h3><div class="fl-row">
      ${no('prev', L('prev'), "Aguardando previsão de entrega")}${seta('data informada')}
      ${no('agend', agend, proxima ? 'Próxima: ' + gmFmtData(proxima._sla) : 'Previsão de solução preenchida')}
    </div></div>
  </div>`;
  document.querySelectorAll('#gmFluxo .fl-n').forEach(el => gmContaAnima(el, Number(el.dataset.alvo)));
  hmlDestacaEtapa();
};

// ---------- KPIs e lista de proximas entregas
const _v6Rgm = renderGestaoMelhorias;
renderGestaoMelhorias = function() {
  _v6Rgm();
  const todas = gmMelhorias(); todas.forEach(t => { t._gmE = gmEtapa(t); });
  const comTag = t => gmTagTem(t, 'aprovado') || gmTagTem(t, 'estimativa');
  const agend = todas.filter(t => t._sla && comTag(t)).sort((a, b) => a._sla - b._sla);
  const prev = todas.filter(t => t._gmE === 'prev').length;
  const backlog = todas.filter(t => t.status === GM_ST_DEV && !comTag(t)).length;
  const prox7 = agend.filter(t => t._sla >= NOW && (t._sla - NOW) / 864e5 <= 7).length;
  const venc = agend.filter(t => t._sla < NOW).length;
  document.getElementById('gmKpis').innerHTML =
    gmKpi(prev, 'Aguardando previsão de entrega', prev ? 'warn' : '', "gmScroll('gmKanbanBox')") +
    gmKpi(agend.length, 'Entregas agendadas', '', "gmScroll('gmVencBox')") +
    gmKpi(prox7, 'Entregam em até 7 dias', prox7 ? 'warn' : '', "gmScroll('gmVencBox')") +
    gmKpi(venc, 'Previsão vencida', venc ? 'danger' : '', "gmScroll('gmVencBox')") +
    gmKpi(backlog, 'Backlog em desenvolvimento (sem tag)', '', '');
  const linhas = agend.map(t => {
    const dd = (t._sla - NOW) / 864e5;
    const pill = dd < 0 ? `<span class="gm-selo gm-bad">vencida há ${gmDias(-dd)}</span>` : `<span class="gm-selo ${dd <= 7 ? 'gm-warn' : 'gm-ok'}">em ${gmDias(dd)}</span>`;
    return `<tr><td style="white-space:nowrap; font-weight:600;">${gmFmtData(t._sla)}</td><td style="text-align:center;">${pill}</td>
      <td class="col-id">${ticketLink(t.id, t.protocol)}</td><td class="col-subject">${esc((t.subject || '').slice(0, 70))}${gmSelos(t)}</td>
      <td class="col-team">${esc(t.clientOrg || '-')}</td><td class="col-status">${esc(HML6_NOMES[t._gmE] || t.status)}</td><td style="min-width:260px; font-size:11.5px;">${gmComentario(t)}</td></tr>`;
  }).join('') || '<tr><td colspan="7" class="empty-msg">Nenhuma melhoria com tag e Previsão de solução preenchida ainda.</td></tr>';
  document.getElementById('gmVencBox').innerHTML = `<h2>Próximas entregas</h2>
    <div class="panel-sub">Melhorias com tag Aprovado PO, Estimativa Técnica ou Estimativa Comercial e o campo Previsão de solução preenchido, da data mais próxima para a mais distante. As vencidas aparecem primeiro. Chamados em Aguardando Desenvolvimento sem tag são o backlog antigo e ficam fora desta lista.</div>
    <table><thead><tr><th>Previsão</th><th>Prazo</th><th>Chamado</th><th>Melhoria</th><th>Cliente</th><th>Etapa</th><th>Último comentário</th></tr></thead><tbody>${linhas}</tbody></table>`;
};
renderGestaoMelhorias();
"""
