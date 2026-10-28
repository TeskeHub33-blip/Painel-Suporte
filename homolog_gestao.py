# -*- coding: utf-8 -*-
"""Homologacao v2 — navegacao 'Gestao de Indicadores' e a visao 'Gestao Semanal - Bugs'.

Estrutura (so' na v2): a antiga aba 'Reuniao Mensal' vira 'Gestao de Indicadores' e passa a ter 3 sub-abas lado a lado:
  Reuniao Mensal | Gestao Semanal - Melhorias | Gestao Semanal - Bugs
A aba solta 'Gestao Semanal - Melhorias' deixa de existir no menu superior (o conteudo foi movido pra dentro).
"""

NAV_CSS = """
.gi-nav { display: flex; gap: 6px; margin: 0 0 18px 0; border-bottom: 1.5px solid var(--panel-border); flex-wrap: wrap; }
.gi-nav button { background: transparent; border: none; border-bottom: 3px solid transparent; margin-bottom: -1.5px; padding: 10px 18px;
  font-family: inherit; font-size: 14px; font-weight: 600; color: var(--text3); cursor: pointer; transition: color .15s, border-color .15s; }
.gi-nav button:hover { color: var(--text); }
.gi-nav button.active { color: var(--navy); border-bottom-color: var(--pink); }
.gb-urg-alta { background: var(--danger-dim); color: var(--danger); }
.gb-urg-media { background: var(--warn-dim); color: var(--warn); }
.gb-urg-outra { background: var(--surface2); color: var(--text3); }
"""

NAV_JS = r"""
// ===== HOMOLOGACAO v2: navegacao da aba 'Gestao de Indicadores' =====
function setGiSub(s) {
  ['reuniao', 'melhorias', 'bugs'].forEach(k => { const el = document.getElementById('giSub_' + k); if (el) el.style.display = k === s ? '' : 'none'; });
  document.querySelectorAll('#giNav button').forEach(b => b.classList.toggle('active', b.dataset.sub === s));
  if (s === 'bugs') renderGestaoBugs();
  if (s === 'melhorias') setGmSub(gmSub);
}
"""

BUGS_JS = r"""
// ===== HOMOLOGACAO v2: Gestao Semanal - Bugs =====
// Regras de bug do painel: categoria Bug; fila de desenvolvimento = 'Aguardando Desenvolvimento' (ou nome legado '- fila Bugs');
// SLA de repasse pro N2: Bug alto 1h, Bug medio 8h; ciclo de vida (repasse N1, abertura de task, tempo aberto no devops) do mes corrente.
const GB_COLS = [
  {k: 'n1', t: 'Em atendimento N1', who: "Status 'Em atendimento' + categoria Bug"},
  {k: 'n2', t: 'Em análise no N2', who: "Status 'Em atendimento - N2' + categoria Bug"},
  {k: 'dev', t: 'Na fila de desenvolvimento', who: "Status 'Aguardando Desenvolvimento' (task aberta)", key: true},
  {k: 'espera', t: 'Aguardando cliente / terceiros', who: "Status 'Aguardando Cliente' ou 'Aguardando Terceiros'"},
];
let gbSub = 'acomp';
function gbEtapa(t) {
  if (isDevQueueStatus(t.status)) return 'dev';
  if (t.status === 'Em atendimento - N2') return 'n2';
  if (t.status === 'Em atendimento') return 'n1';
  if (t.status === 'Aguardando Cliente' || t.status === 'Aguardando Terceiros') return 'espera';
  return null;
}
function gbUrg(t) {
  const u = t.urgency || '-';
  return `<span class="gm-selo ${u === 'Alta' ? 'gb-urg-alta' : u === 'Média' ? 'gb-urg-media' : 'gb-urg-outra'}">${esc(u)}</span>`;
}
function gbFmtDataHora(d) { const b = new Date(d.getTime() - 3 * 3600000).toISOString(); return b.slice(8, 10) + '/' + b.slice(5, 7) + ' ' + b.slice(11, 16); }
function setGbSub(s) {
  gbSub = s;
  document.querySelectorAll('#gbSubToggle button').forEach(b => b.classList.toggle('active', b.dataset.sub === s));
  document.getElementById('gbAcomp').style.display = s === 'acomp' ? '' : 'none';
  document.getElementById('gbIndic').style.display = s === 'indic' ? '' : 'none';
}
function renderGestaoBugs() {
  const todas = TICKETS.filter(t => t.category === 'Bug');
  todas.forEach(t => { t._gbE = gbEtapa(t); });
  const por = k => todas.filter(t => t._gbE === k);
  const alta = todas.filter(t => t.urgency === 'Alta'), media = todas.filter(t => t.urgency === 'Média');
  const comSla = todas.filter(t => t._sla).sort((a, b) => a._sla - b._sla);
  const vencidos = comSla.filter(t => t._sla < NOW);
  const em24h = comSla.filter(t => t._sla >= NOW && (t._sla - NOW) / 36e5 <= 24);

  document.getElementById('gbKpis').innerHTML =
    gmKpi(todas.length, 'Bugs abertos', '') +
    gmKpi(alta.length, 'Urgência Alta', alta.length ? 'danger' : '') +
    gmKpi(media.length, 'Urgência Média', '') +
    gmKpi(por('dev').length, 'Na fila de desenvolvimento', '') +
    gmKpi(em24h.length, 'SLA vence em até 24h', em24h.length ? 'warn' : '') +
    gmKpi(vencidos.length, 'SLA vencido', vencidos.length ? 'danger' : '');

  const linhasV = comSla.slice(0, 40).map(t => {
    const h = (t._sla - NOW) / 36e5;
    const pill = h < 0 ? `<span class="gm-selo gm-bad">vencido há ${fmtH(-h)}</span>` : `<span class="gm-selo ${h <= 24 ? 'gm-warn' : 'gm-ok'}">em ${fmtH(h)}</span>`;
    return `<tr><td style="white-space:nowrap; font-weight:600;">${gbFmtDataHora(t._sla)}</td><td style="text-align:center;">${pill}</td>
      <td class="col-id">${ticketLink(t.id, t.protocol)}</td><td class="col-subject">${esc((t.subject || '').slice(0, 70))}</td><td style="text-align:center;">${gbUrg(t)}</td>
      <td class="col-team">${esc(t.clientOrg || '-')}</td><td class="col-status">${esc(t.status)}</td><td style="min-width:240px; font-size:11.5px;">${gmComentario(t)}</td></tr>`;
  }).join('') || '<tr><td colspan="8" class="empty-msg">Nenhum bug aberto com SLA definido.</td></tr>';
  document.getElementById('gbVencBox').innerHTML = `<h2>Próximos vencimentos — SLA de solução</h2>
    <div class="panel-sub">Bugs abertos com prazo de SLA definido, do mais próximo (ou já vencido) para o mais distante.</div>
    <table><thead><tr><th>Vencimento</th><th>Prazo</th><th>Chamado</th><th>Bug</th><th>Urgência</th><th>Cliente</th><th>Status</th><th>Último comentário</th></tr></thead><tbody>${linhasV}</tbody></table>`;

  document.getElementById('gbKanbanBox').innerHTML = `<h2>Bugs parados em cada etapa</h2>
    <div class="panel-sub">Borda do cartão pelo tempo sem atualização: verde até 7 dias, amarelo de 8 a 15, vermelho acima de 15. Em cada coluna, os mais parados primeiro.</div>
    <div class="gm-board" style="grid-template-columns: repeat(4, minmax(250px, 1fr));">${GB_COLS.map(c => {
      const it = por(c.k).sort((a, b) => gmDiasParado(b) - gmDiasParado(a));
      const mostra = gmAbertos['b' + c.k] ? it : it.slice(0, GM_LIM);
      const med = it.length ? gmMedia(it.map(gmDiasParado)) : null;
      const cards = mostra.map(t => `<div class="gm-card gm-b-${gmCor(gmDiasParado(t))}">
          <div>${ticketLink(t.id, t.protocol)} ${gbUrg(t)}<span style="float:right; color:var(--text3); font-size:10.5px;">${esc(t.ownerTeam || '')}</span></div>
          <div class="gm-t">${esc((t.subject || '').slice(0, 80))}</div>
          <div style="color:var(--text3); font-size:10.5px;">${esc(t.clientOrg || '-')}</div>
          <div class="gm-m"><span>parado há <b>${gmDias(gmDiasParado(t))}</b></span><span>aberto há ${gmDias(gmDiasAberto(t))}</span></div>
          <div class="gm-c">${gmComentario(t, 90)}</div></div>`).join('') || '<div class="gm-vazio">Nenhum bug nesta etapa</div>';
      const mais = it.length > GM_LIM ? `<div class="gm-mais" onclick="gmAbertos['b${c.k}']=!gmAbertos['b${c.k}']; renderGestaoBugs();">${gmAbertos['b' + c.k] ? 'mostrar menos' : 'ver mais ' + (it.length - GM_LIM)}</div>` : '';
      return `<div class="gm-col ${c.key ? 'gm-key' : ''}"><h3>${c.t}<em>${it.length}</em></h3><div class="gm-who">${c.who}${med !== null ? ` · média parado ${gmDias(med)}` : ''}</div>${cards}${mais}</div>`;
    }).join('')}</div>`;

  renderGbIndicadores(todas, por);
  setGbSub(gbSub);
}
function renderGbIndicadores(todas, por) {
  const idade = todas.map(gmDiasAberto);
  const etapas = GB_COLS.map(c => ({nome: c.t, itens: por(c.k)}));
  const tabEtapas = etapas.map(l => `<tr><td>${l.nome}</td><td style="text-align:right;">${l.itens.length}</td>
    <td style="text-align:right;">${gmFmtN(gmMedia(l.itens.map(gmDiasNaEtapa)))}</td><td style="text-align:right;">${gmFmtN(gmMediana(l.itens.map(gmDiasNaEtapa)))}</td>
    <td style="text-align:right;">${l.itens.length ? gmDias(Math.max(...l.itens.map(gmDiasNaEtapa))) : '–'}</td></tr>`).join('');
  const urgs = ['Alta', 'Média'].concat(Array.from(new Set(todas.map(t => t.urgency).filter(u => u && u !== 'Alta' && u !== 'Média'))));
  const tabUrg = urgs.map(u => { const it = todas.filter(t => t.urgency === u); return `<tr><td>${esc(u)}</td><td style="text-align:right;">${it.length}</td><td style="text-align:right;">${gmFmtN(gmMedia(it.map(gmDiasAberto)))}</td><td style="text-align:right;">${gmFmtN(gmMediana(it.map(gmDiasAberto)))}</td></tr>`; }).join('');

  // SLA de repasse pro N2 (prazos fixos do painel) x tempo medio de repasse do mes corrente
  const rep = (u, prazoH, rotulo) => {
    const m = bugMetricsFor(u); const med = m.mediaRepasseN1;
    const cls = med === null ? '' : med <= prazoH ? 'gm-ok' : 'gm-bad';
    return `<tr><td>${rotulo}</td><td style="text-align:right;">${fmtH(prazoH)}</td><td style="text-align:right;">${med !== null ? fmtH(med) : '–'}</td>
      <td style="text-align:center;">${med === null ? '–' : `<span class="gm-selo ${cls}">${med <= prazoH ? 'dentro do prazo' : 'acima do prazo'}</span>`}</td><td style="text-align:right;">${m.total}</td></tr>`;
  };
  const ciclo = (u) => { const m = bugMetricsFor(u); return `<tr><td>${u}</td><td style="text-align:right;">${m.total}</td><td style="text-align:right;">${m.mediaRepasseN1 !== null ? fmtH(m.mediaRepasseN1) : '–'}</td><td style="text-align:right;">${m.mediaAberturaTask !== null ? fmtH(m.mediaAberturaTask) : '–'}</td><td style="text-align:right;">${m.mediaDevops !== null ? fmtH(m.mediaDevops) : '–'}</td></tr>`; };

  // por mes: bugs resolvidos, % no prazo (com SLA) e tempo medio
  const meses = Object.keys(MONTH_YM).sort((a, b) => Number(b) - Number(a)).map(k => {
    const its = (RESOLVED_MONTHS[k] || []).filter(r => r.category === 'Bug');
    const comSla = its.filter(r => r.slaSolutionDate && r.resolvedIn);
    const ok = comSla.filter(r => parseDt(r.resolvedIn) <= parseDt(r.slaSolutionDate)).length;
    const tempos = its.filter(r => r.createdDate && r.resolvedIn).map(r => (parseDt(r.resolvedIn) - parseDt(r.createdDate)) / 864e5);
    return `<tr><td>${MONTH_LABELS[k]}</td><td style="text-align:right;">${its.length}</td><td style="text-align:right;">${comSla.length ? Math.round(ok / comSla.length * 100) + '%' : '–'}</td><td style="text-align:right;">${gmFmtN(gmMedia(tempos))}</td></tr>`;
  }).join('');
  const incorretos = TICKETS.filter(t => t._classificacaoIncorreta).length;

  document.getElementById('gbIndic').innerHTML = `
    <div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
      ${gmKpi(todas.length, 'Bugs abertos', '')}${gmKpi(gmFmtN(gmMedia(idade)), 'Idade média do backlog', '')}${gmKpi(gmFmtN(gmMediana(idade)), 'Idade mediana', '')}
      ${gmKpi(incorretos, 'Abertos com classificação incorreta', incorretos ? 'warn' : '')}
    </div>
    <div class="panel" style="margin-top:18px;"><h2>SLA de repasse para o N2</h2>
      <div class="panel-sub">Prazos fixos: Bug alto 1 hora; Bug médio 8 horas (desde que fornecida solução de contorno). Tempo médio de repasse do mês corrente, descontado o tempo em Aguardando Cliente.</div>
      <table><thead><tr><th style="text-align:left;">Classificação</th><th>Prazo</th><th>Tempo médio</th><th>Situação</th><th>Bugs no mês</th></tr></thead><tbody>${rep('Alta', 1, 'Bug alto')}${rep('Média', 8, 'Bug médio')}</tbody></table></div>
    <div class="panel" style="margin-top:18px;"><h2>Ciclo de vida do bug — mês corrente</h2>
      <div class="panel-sub">Repasse N1 até o N2, abertura da task (N2 até a fila de desenvolvimento) e tempo aberto no devops (até o log de validação/impedimento do Azure, ou o tempo total na fila).</div>
      <table><thead><tr><th style="text-align:left;">Urgência</th><th>Bugs</th><th>Repasse N1</th><th>Abertura de task</th><th>Aberto no devops</th></tr></thead><tbody>${ciclo('Alta')}${ciclo('Média')}</tbody></table></div>
    <div class="panel" style="margin-top:18px;"><h2>Quantidade e tempo em cada etapa</h2>
      <table><thead><tr><th style="text-align:left;">Etapa</th><th>Qtd</th><th>Média na etapa</th><th>Mediana</th><th>Maior</th></tr></thead><tbody>${tabEtapas}</tbody></table></div>
    <div class="panel" style="margin-top:18px;"><h2>Backlog por urgência</h2>
      <table><thead><tr><th style="text-align:left;">Urgência</th><th>Qtd</th><th>Idade média</th><th>Idade mediana</th></tr></thead><tbody>${tabUrg}</tbody></table></div>
    <div class="panel" style="margin-top:18px;"><h2>Bugs resolvidos por mês</h2>
      <div class="panel-sub">% no prazo considera só os bugs com SLA definido (resolvido até a data do SLA), sem o expurgo de espera de órgão governamental. Tempo = da abertura até a resolução.</div>
      <table><thead><tr><th style="text-align:left;">Mês</th><th>Resolvidos</th><th>% no prazo</th><th>Tempo médio</th></tr></thead><tbody>${meses}</tbody></table></div>`;
}
"""

BUGS_HTML = """<div class="panel-sub" style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
      <span>Bugs abertos: acompanhamento por etapa, SLA e tempos do ciclo de vida</span>
      <span class="seg-toggle" id="gbSubToggle" role="group" aria-label="Visão">
        <button type="button" class="active" data-sub="acomp" onclick="setGbSub('acomp')">Acompanhamento</button>
        <button type="button" data-sub="indic" onclick="setGbSub('indic')">Indicadores</button>
      </span>
    </div>
    <div id="gbAcomp">
      <div class="kpi-row" id="gbKpis" style="grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));"></div>
      <div class="panel" id="gbVencBox" style="margin-top:18px;"></div>
      <div class="panel" id="gbKanbanBox" style="margin-top:18px;"></div>
    </div>
    <div id="gbIndic" style="display:none;"></div>"""


def reestruturar_navegacao(html):
    """Move 'Gestao Semanal - Melhorias' pra dentro da aba (renomeada) e cria a sub-aba de Bugs."""
    ini = html.index('<div class="tab-panel" id="tabGestaoMelhorias">')
    fim = html.index('<div class="tab-panel" id="tabFluxo">')
    bloco = html[ini:fim]
    html = html[:ini] + '<div class="tab-panel" id="tabGestaoMelhorias" style="display:none;"></div>\n\n  ' + html[fim:]
    interno = bloco[len('<div class="tab-panel" id="tabGestaoMelhorias">'):].rstrip()
    assert interno.endswith('</div>')
    interno = interno[:-len('</div>')]

    abre = '<div id="reuniaoMensalContent" style="display:none;">'
    a = html.index(abre) + len(abre)
    # o conteudo da Reuniao Mensal termina nos dois ultimos </div> antes do painel de Gestao (dummy) que acabamos de colocar
    limite = html.index('<div class="tab-panel" id="tabGestaoMelhorias" style="display:none;">')
    cauda = html[a:limite].rstrip()
    assert cauda.endswith('</div>\n  </div>'), cauda[-60:]
    corpo = cauda[:-len('</div>\n  </div>')]
    nav = ('\n      <div class="gi-nav" id="giNav" role="tablist">'
           '<button type="button" class="active" data-sub="reuniao" onclick="setGiSub(\'reuniao\')">Reunião Mensal</button>'
           '<button type="button" data-sub="melhorias" onclick="setGiSub(\'melhorias\')">Gestão Semanal - Melhorias</button>'
           '<button type="button" data-sub="bugs" onclick="setGiSub(\'bugs\')">Gestão Semanal - Bugs</button></div>\n')
    novo = (nav + '<div id="giSub_reuniao">' + corpo + '</div>\n'
            '<div id="giSub_melhorias" style="display:none;">' + interno + '</div>\n'
            '<div id="giSub_bugs" style="display:none;">' + BUGS_HTML + '</div>\n'
            '    </div>\n  </div>')
    html = html[:a] + novo + html[limite:]

    # menu superior: renomeia a aba e esconde o botao antigo (o showTab ainda referencia o id)
    html = html.replace('>Reuniao Mensal</button>', '>Gestão de Indicadores</button>', 1)
    html = html.replace('<button class="tab-btn" id="tabBtnGestaoMelhorias"', '<button class="tab-btn" id="tabBtnGestaoMelhorias" style="display:none;"', 1)
    html = html.replace("localStorage.getItem('activeTab') || 'live'", "(localStorage.getItem('activeTab') === 'gestaoMelhorias' ? 'reuniaoMensal' : (localStorage.getItem('activeTab') || 'live'))", 1)
    return html
