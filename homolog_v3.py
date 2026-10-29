# -*- coding: utf-8 -*-
"""Homologacao v3: busca de chamado com resumo executivo, recorrencias nos Bugs e Fluxograma com a nova identidade.

Usado so' pelo homolog_extras.aplicar_homologacao (versao /homolog/); o painel atual nao usa nada daqui.
"""
import re

V3_CSS = """
/* ===== HOMOLOGACAO v3 ===== */
/* Busca de chamado + resumo executivo */
.hml-busca { display: flex; gap: 8px; align-items: center; margin: 0 0 14px 0; flex-wrap: wrap; }
.hml-busca input { flex: 1 1 280px; max-width: 420px; padding: 9px 14px; font: 400 14px inherit; font-family: inherit; color: var(--text);
  background: var(--panel); border: 1.25px solid var(--panel-border); border-radius: 6px; outline: none; }
.hml-busca input:focus { border-color: var(--pink); }
.hml-busca button { padding: 9px 18px; border-radius: 6px; border: none; background: var(--pink); color: #fff; font: 600 13px inherit; font-family: inherit; cursor: pointer; }
.hml-busca button:hover { filter: brightness(.95); }
.hml-erro { color: var(--danger); font-size: 12.5px; margin: 0 0 12px 0; }
.hml-exec { background: var(--panel); border-radius: 8px; box-shadow: var(--shadow); padding: 20px 24px; margin: 0 0 18px 0; border-left: 4px solid var(--pink); }
.hml-exec-topo { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; flex-wrap: wrap; }
.hml-exec h3 { margin: 2px 0 8px 0; font-size: 17px; font-weight: 600; letter-spacing: -.2px; color: var(--text); max-width: 760px; }
.hml-exec .hml-prot { font-size: 12px; font-weight: 600; color: var(--text3); letter-spacing: .4px; }
.hml-exec-acoes { display: flex; gap: 8px; }
.hml-exec-acoes a, .hml-exec-acoes button { padding: 6px 12px; border-radius: 6px; border: 1.25px solid var(--panel-border); background: transparent; color: var(--text-dim);
  font: 600 12px inherit; font-family: inherit; cursor: pointer; text-decoration: none; }
.hml-exec-acoes a:hover, .hml-exec-acoes button:hover { color: var(--text); border-color: var(--text3); }
.hml-exec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px 24px; margin-top: 16px; }
.hml-exec-grid .k { font-size: 10.5px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--text3); }
.hml-exec-grid .v { font-size: 14px; color: var(--text); margin-top: 2px; line-height: 1.35; }
.hml-exec-grid .v small { color: var(--text3); font-size: 11.5px; }
.hml-exec-bloco { margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--panel-border); }
.hml-exec-bloco .k { font-size: 10.5px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--text3); margin-bottom: 4px; }
.hml-exec-bloco .v { font-size: 13px; color: var(--text-dim); line-height: 1.5; white-space: pre-line; }
.hml-chip { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 11.5px; font-weight: 600; margin: 0 6px 0 0; background: var(--surface2); color: var(--text-dim); }
.hml-chip.pink { background: var(--pink-dim); color: var(--pink); }
.hml-chip.ok { background: var(--ok-dim); color: var(--ok); }
.hml-chip.warn { background: var(--warn-dim); color: var(--warn); }
.hml-chip.bad { background: var(--danger-dim); color: var(--danger); }
/* Recorrencias */
.hml-rec-grupo summary { cursor: pointer; color: var(--pink); font-size: 11.5px; font-weight: 600; }
.hml-rec-grupo div { font-size: 11.5px; margin-top: 4px; line-height: 1.7; }
/* Fluxograma com a mesma identidade */
#tabFluxo .panel { padding: 20px 24px; }
#tabFluxo .flow-box { border-radius: 8px; box-shadow: none; }
#tabFluxo .flow-search-row { background: var(--panel); border-radius: 8px; box-shadow: var(--shadow); padding: 12px 16px; }
#tabFluxo .flow-search-row input, #tabFluxo .flow-search-row select { background: var(--panel); border: 1.25px solid var(--panel-border); border-radius: 6px; color: var(--text); font-family: inherit; }
#tabFluxo .flow-search-row .export-btn { background: var(--pink); color: #fff; border: none; border-radius: 6px; font-weight: 600; }
#tabFluxo .flow-next-steps { border-radius: 8px; }
#tabFluxo .flow-timeline-item { border-left-color: var(--panel-border); }
#tabFluxo .flow-sla-table th { background: transparent; }
"""

V3_JS = r"""
// ===== HOMOLOGACAO v3 =====
// Busca por protocolo em TODOS os meses carregados (a versao atual so' olhava os 3 mais recentes).
findTicketByProtocol = function(protocol) {
  protocol = String(protocol || '').trim();
  if (!protocol) return null;
  let t = TICKETS.find(x => String(x.protocol) === protocol);
  if (t) return t;
  for (const k of Object.keys(RESOLVED_MONTHS)) { t = (RESOLVED_MONTHS[k] || []).find(x => String(x.protocol) === protocol); if (t) return t; }
  return RESOLVED_TODAY.find(x => String(x.protocol) === protocol) || null;
};

// ---------- etapa da melhoria no fluxo (usada no resumo executivo e no destaque do Fluxo)
const HML_PASSOS = [['n1', 'Em atendimento N1'], ['n2', 'Validação do N2'], ['refina', 'Reunião de alinhamento'], ['tec', 'Estimativa técnica'], ['orc', 'Orçamento'], ['cliente', 'Resposta do cliente'], ['dev', 'Desenvolvimento']];
function hmlChaveEtapaMel(t) {
  const e = gmEtapa(t);
  if (e === 'refina') return gmTagTem(t, 'aprovado po') ? 'po' : 'refina';
  if (e) return e;
  if (t.status === GM_ST_DEV) return 'dev';
  if (t.status === 'Aguardando Cliente') return 'cliente';
  return null;
}
function hmlPassosMelhoria(t) {
  const chave = hmlChaveEtapaMel(t), passoAtual = chave === 'po' ? 'refina' : chave;
  const idx = HML_PASSOS.findIndex(p => p[0] === passoAtual);
  if (idx === -1) return `<div class="hml-exec-bloco"><div class="k">Etapa no fluxo de melhorias</div><div class="v">Fora das etapas do fluxo (status ${esc(t.status || '-')}).</div></div>`;
  const itens = HML_PASSOS.map((p, i) => `<div class="hml-passo ${i < idx ? 'feito' : i === idx ? 'atual' : ''}">${i === idx ? '<small>Etapa atual</small>' : ''}${esc(p[1])}${i === idx && chave === 'po' ? '<small style="display:block;">Aprovado PO · aguardando data</small>' : ''}</div>`).join('');
  return `<div class="hml-exec-bloco"><div class="k">Etapa no fluxo de melhorias</div><div class="hml-passos">${itens}</div></div>`;
}
let hmlMelhoriaSel = null;
function hmlDestacaEtapa() {
  document.querySelectorAll('#gmFluxo .fl-node.fl-atual').forEach(n => n.classList.remove('fl-atual'));
  if (!hmlMelhoriaSel) return;
  let k = hmlChaveEtapaMel(hmlMelhoriaSel);
  if (k === 'dev') k = (hmlMelhoriaSel.tags || []).some(x => (x || '').toLowerCase().indexOf('estimativa') !== -1) ? 'dev2' : 'dev1';
  const no = k && document.querySelector('#gmFluxo .fl-node[data-k="' + k + '"]');
  if (no) no.classList.add('fl-atual');
}

// ---------- resumo executivo do chamado
function hmlChip(txt, cls) { return `<span class="hml-chip ${cls || ''}">${esc(txt)}</span>`; }
function hmlCampo(k, v) { return `<div><div class="k">${k}</div><div class="v">${v}</div></div>`; }
function hmlDt(iso) { const d = parseDt(iso); if (!d) return '–'; const b = new Date(d.getTime() - 3 * 3600000).toISOString(); return b.slice(8, 10) + '/' + b.slice(5, 7) + '/' + b.slice(0, 4) + ' ' + b.slice(11, 16); }
function hmlCartaoExecutivo(t, fonte) {
  const aberto = t._created !== undefined;          // chamado de TICKETS (aberto agora) tem campos calculados
  const resolvido = !aberto || !!t.resolvedIn;
  const criado = parseDt(t.createdDate);
  const idadeH = criado ? ((t.resolvedIn ? parseDt(t.resolvedIn) : NOW) - criado) / 36e5 : null;
  const urg = t.urgency || '';
  const chips = hmlChip(t.status || (resolvido ? 'Resolvido' : '-'), 'pink') + hmlChip(t.category || 'Sem categoria') + (urg ? hmlChip('Urgência ' + urg, urg === 'Alta' ? 'bad' : urg === 'Média' ? 'warn' : '') : '') +
    (t.ownerTeam ? hmlChip(t.ownerTeam) : '') + Array.from(new Set(t.tags || [])).map(x => hmlChip(x)).join('');
  // SLA
  let sla = '<span style="color:var(--text3);">sem SLA definido</span>';
  if (t.slaSolutionDate) {
    const alvo = parseDt(t.slaSolutionDate);
    if (t.resolvedIn) { const ok = parseDt(t.resolvedIn) <= alvo; sla = `${hmlDt(t.slaSolutionDate)} <small>${ok ? 'cumprido' : 'estourado'}</small>`; }
    else { const h = (alvo - NOW) / 36e5; sla = `${hmlDt(t.slaSolutionDate)} <small>${h < 0 ? 'vencido há ' + fmtH(-h) : 'vence em ' + fmtH(h)}</small>`; }
  }
  const naEtapa = aberto && !t.resolvedIn ? `há ${gmDias(gmDiasNaEtapa(t))}` : '–';
  const ultimaAtu = aberto && t._hoursSinceUpdate !== null ? `há ${fmtH(t._hoursSinceUpdate)}` : '–';
  const desc = (t.description || '').replace(/\s+/g, ' ').trim();
  const comentario = t.lastComment ? gmComentario(t, 420) : '';
  const protoJs = jsStr(String(t.protocol));
  const ehMelhoriaAberta = aberto && !t.resolvedIn && t.category === 'Melhoria';
  return `<div class="hml-exec">
    <div class="hml-exec-topo"><div><div class="hml-prot">Chamado ${esc(t.protocol)}</div><h3>${esc(t.subject || '')}</h3><div>${chips}</div></div>
      <div class="hml-exec-acoes"><a href="${MOVIDESK_BASE}${t.id}" target="_blank" rel="noopener">Abrir no Movidesk</a>
        ${ehMelhoriaAberta ? `<button type="button" onclick="hmlMelhoriaSel = findTicketByProtocol(${protoJs}); setGiSub('melhorias'); setGmSub('fluxo');">Ver no fluxo</button>` : ''}
        ${fonte === 'fluxo' ? '' : `<button type="button" onclick="document.getElementById('fluxoBuscaProtocolo').value=${protoJs}; showTab('fluxo'); buscarChamadoFluxoPorProtocolo();">Ver no fluxograma</button>`}
        ${fonte && fonte !== 'fluxo' ? `<button type="button" onclick="document.getElementById('${fonte}Res').innerHTML=''; document.getElementById('${fonte}Input').value='';">Fechar</button>` : ''}</div></div>
    <div class="hml-exec-grid">
      ${hmlCampo('Cliente', esc(t.clientOrg || '–'))}
      ${hmlCampo('Responsável', esc(t.ownerName || '–'))}
      ${hmlCampo('Canal de entrada', esc(originLabel(t.origin)))}
      ${hmlCampo('Aberto em', `${hmlDt(t.createdDate)} <small>${idadeH !== null ? (t.resolvedIn ? 'levou ' : 'há ') + fmtH(idadeH) : ''}</small>`)}
      ${t.resolvedIn ? hmlCampo('Resolvido em', hmlDt(t.resolvedIn)) : hmlCampo('Tempo no status atual', naEtapa)}
      ${hmlCampo('Última atualização', ultimaAtu)}
      ${hmlCampo('SLA de solução', sla)}
      ${t.resolvedInFirstCall !== undefined && t.resolvedIn ? hmlCampo('Resolvido na 1ª resposta', t.resolvedInFirstCall ? 'Sim' : 'Não') : ''}
    </div>
    ${ehMelhoriaAberta ? hmlPassosMelhoria(t) : ''}
    ${comentario ? `<div class="hml-exec-bloco"><div class="k">Último comentário</div><div class="v">${comentario}</div></div>` : ''}
    ${desc ? `<div class="hml-exec-bloco"><div class="k">Descrição</div><div class="v">${esc(desc.slice(0, 420))}${desc.length > 420 ? '…' : ''}</div></div>` : ''}
  </div>`;
}
// ---------- busca por chamado nas abas Melhorias e Bugs
function hmlBuscaHtml(p, rotulo) {
  return `<div class="hml-busca"><input id="${p}Input" placeholder="${rotulo}" onkeydown="if(event.key==='Enter')hmlBuscaChamado('${p}')"><button type="button" onclick="hmlBuscaChamado('${p}')">Buscar chamado</button></div><div id="${p}Res"></div>`;
}
function hmlBuscaChamado(p) {
  const v = document.getElementById(p + 'Input').value, res = document.getElementById(p + 'Res');
  const t = findTicketByProtocol(v);
  if (t && t.category === 'Melhoria' && t._created !== undefined) { hmlMelhoriaSel = t; if (document.getElementById('gmFluxo').style.display !== 'none') renderGmFluxo(); }
  res.innerHTML = t ? hmlCartaoExecutivo(t, p) : `<div class="hml-erro">Chamado "${esc(v)}" não encontrado (busca entre os abertos e os resolvidos nos meses carregados).</div>`;
}
document.getElementById('giSub_melhorias').insertAdjacentHTML('afterbegin', hmlBuscaHtml('gmBusca', 'Buscar melhoria pelo número do chamado'));
document.getElementById('giSub_bugs').insertAdjacentHTML('afterbegin', hmlBuscaHtml('gbBusca', 'Buscar bug pelo número do chamado'));

// ---------- Fluxograma: resumo executivo ao buscar um chamado
const _hmlCarregaFluxo = carregarChamadoFluxo;
carregarChamadoFluxo = function(t) { _hmlCarregaFluxo(t); const el = document.getElementById('fluxoExecutivo'); if (el) el.innerHTML = hmlCartaoExecutivo(t, 'fluxo'); };
const _hmlLimpaFluxo = limparBuscaFluxo;
limparBuscaFluxo = function() { _hmlLimpaFluxo(); const el = document.getElementById('fluxoExecutivo'); if (el) el.innerHTML = ''; };

// ---------- Bugs: situacoes recorrentes (total e por cliente)
function hmlOcorrenciasBug() {
  const itens = [];
  TICKETS.filter(t => t.category === 'Bug').forEach(t => itens.push({id: t.id, protocolo: t.protocol, assunto: t.subject, cliente: t.clientOrg || 'Sem cliente', aberto: true}));
  ['0', '1', '2'].forEach(k => (RESOLVED_MONTHS[k] || []).filter(r => r.category === 'Bug').forEach(r => itens.push({id: r.id, protocolo: r.protocol, assunto: r.subject, cliente: r.clientOrg || 'Sem cliente', aberto: false})));
  return itens;
}
function hmlListaProtocolos(its) { return its.map(i => `<a href="${MOVIDESK_BASE}${i.id}" target="_blank" rel="noopener" class="ticket-link">${esc(i.protocolo)}</a>${i.aberto ? '' : ' <span style="color:var(--text3);">(resolvido)</span>'}`).join(' · '); }
function renderGbRecor() {
  const itens = hmlOcorrenciasBug();
  const porSit = {};
  itens.forEach(i => { const k = normalizeSubjectHist(i.assunto); if (!k) return; (porSit[k] = porSit[k] || {assunto: i.assunto, its: []}).its.push(i); });
  const grupos = Object.values(porSit).filter(g => g.its.length >= 2).sort((a, b) => b.its.length - a.its.length);
  const clientesAfetados = new Set(); grupos.forEach(g => g.its.forEach(i => clientesAfetados.add(i.cliente)));
  const totalOcorr = grupos.reduce((s, g) => s + g.its.length, 0);

  const tabTotal = grupos.slice(0, 30).map(g => {
    const cl = {}; g.its.forEach(i => { cl[i.cliente] = (cl[i.cliente] || 0) + 1; });
    const top = Object.entries(cl).sort((a, b) => b[1] - a[1]);
    return `<tr><td style="max-width:360px;">${esc(g.assunto)}<details class="hml-rec-grupo"><summary>ver chamados</summary><div>${hmlListaProtocolos(g.its)}</div></details></td>
      <td style="text-align:right; font-weight:600;">${g.its.length}</td><td style="text-align:right;">${g.its.filter(i => i.aberto).length}</td>
      <td style="text-align:right;">${top.length}</td><td style="font-size:11.5px;">${top.slice(0, 3).map(([n, c]) => esc(n) + ' (' + c + ')').join(', ')}</td></tr>`;
  }).join('') || '<tr><td colspan="5" class="empty-msg">Nenhuma situação recorrente identificada.</td></tr>';

  // por cliente: mesma situacao repetida (2+) para o MESMO cliente
  const porCliente = {};
  itens.forEach(i => { const k = normalizeSubjectHist(i.assunto); if (!k) return; const c = (porCliente[i.cliente] = porCliente[i.cliente] || {}); (c[k] = c[k] || {assunto: i.assunto, its: []}).its.push(i); });
  const linhasCli = Object.entries(porCliente).map(([cli, sits]) => {
    const rec = Object.values(sits).filter(g => g.its.length >= 2).sort((a, b) => b.its.length - a.its.length);
    return {cli, rec, ocorr: rec.reduce((s, g) => s + g.its.length, 0)};
  }).filter(x => x.rec.length && x.cli !== 'Sem cliente').sort((a, b) => b.ocorr - a.ocorr);
  const tabCli = linhasCli.slice(0, 25).map(x => `<tr><td style="font-weight:600;">${esc(x.cli)}</td><td style="text-align:right;">${x.rec.length}</td><td style="text-align:right; font-weight:600;">${x.ocorr}</td>
      <td style="font-size:11.5px;">${x.rec.slice(0, 3).map(g => `<details class="hml-rec-grupo"><summary>${esc(g.assunto.slice(0, 70))} (${g.its.length})</summary><div>${hmlListaProtocolos(g.its)}</div></details>`).join('')}</td></tr>`).join('')
    || '<tr><td colspan="4" class="empty-msg">Nenhum cliente com situação repetida.</td></tr>';

  document.getElementById('gbRecor').innerHTML = `
    <div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
      ${gmKpi(grupos.length, 'Situações recorrentes', grupos.length ? 'warn' : '')}${gmKpi(totalOcorr, 'Ocorrências nessas situações', '')}
      ${gmKpi(clientesAfetados.size, 'Clientes afetados', '')}${gmKpi(linhasCli.length ? esc(linhasCli[0].cli.slice(0, 18)) : '–', 'Cliente com mais repetições', '')}
    </div>
    <div class="panel" style="margin-top:18px;"><h2>Situações recorrentes — total</h2>
      <div class="panel-sub">Bugs com o mesmo assunto (texto normalizado) em 2 ou mais chamados, entre os abertos agora e os resolvidos nos últimos 3 meses. Mostra quantas vezes aconteceu, quantas ainda estão abertas e quais clientes foram afetados.</div>
      <table><thead><tr><th style="text-align:left;">Situação</th><th>Ocorrências</th><th>Abertas</th><th>Clientes</th><th style="text-align:left;">Principais clientes</th></tr></thead><tbody>${tabTotal}</tbody></table></div>
    <div class="panel" style="margin-top:18px;"><h2>Situações recorrentes — por cliente</h2>
      <div class="panel-sub">Clientes que tiveram a mesma situação mais de uma vez, do que mais repete para o que menos repete.</div>
      <table><thead><tr><th style="text-align:left;">Cliente</th><th>Situações repetidas</th><th>Ocorrências</th><th style="text-align:left;">Principais situações</th></tr></thead><tbody>${tabCli}</tbody></table></div>`;
}
const _hmlSetGb = setGbSub;
setGbSub = function(s) {
  const r = document.getElementById('gbRecor');
  if (s !== 'recor') { r.style.display = 'none'; _hmlSetGb(s); return; }
  gbSub = 'recor';
  document.querySelectorAll('#gbSubToggle button').forEach(b => b.classList.toggle('active', b.dataset.sub === 'recor'));
  document.getElementById('gbAcomp').style.display = 'none';
  document.getElementById('gbIndic').style.display = 'none';
  r.style.display = '';
  renderGbRecor();
};
"""


def aplicar_v3(html):
    # Fluxograma: tira os dois paineis de barras (entrada por canal / em desenvolvimento por categoria) — o JS existente
    # continua preenchendo os elementos, so' ficam ocultos.
    html = re.sub(r'<div class="panel">(\s*<h2>[^<]*Entrada — por canal</h2>)', r'<div class="panel" style="display:none;">\1', html, count=1)
    html = re.sub(r'<div class="panel">(\s*<h2>[^<]*Em desenvolvimento — por categoria</h2>)', r'<div class="panel" style="display:none;">\1', html, count=1)
    # area do resumo executivo do chamado no Fluxograma
    alvo = '<div id="fluxoErro" style="display:none; color:var(--danger); font-size:12.5px; margin-bottom:10px;"></div>'
    html = html.replace(alvo, alvo + '\n    <div id="fluxoExecutivo"></div>', 1)
    # sub-aba Recorrencias nos Bugs
    html = html.replace('<button type="button" data-sub="indic" onclick="setGbSub(\'indic\')">Indicadores</button>',
                        '<button type="button" data-sub="indic" onclick="setGbSub(\'indic\')">Indicadores</button>\n'
                        '        <button type="button" data-sub="recor" onclick="setGbSub(\'recor\')">Recorrências</button>', 1)
    html = html.replace('<div id="gbIndic" style="display:none;"></div>',
                        '<div id="gbIndic" style="display:none;"></div>\n    <div id="gbRecor" style="display:none;"></div>', 1)
    return html
