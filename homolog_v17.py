# -*- coding: utf-8 -*-
"""Fluxograma com visao executiva: ao buscar um chamado, aparece um resumo com graficos (tempo por etapa, SLA, idade
frente a media da categoria) e um paragrafo executivo, acima do diagrama de fluxo. A busca existe so' no Fluxograma
(e nos fluxos de Melhorias e Bugs, que ja tem a propria busca)."""

V17_CSS = """
/* ===== Visao executiva do Fluxograma ===== */
#fluxoExec:empty { display: none; }
#fluxoExec .ex-wrap { margin-top: 18px; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; }
#fluxoExec .ex-full { grid-column: 1 / -1; }
#fluxoExec .ex-topo { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
#fluxoExec .ex-prot { font-size: 12px; color: var(--text3); letter-spacing: .4px; }
#fluxoExec h3 { margin: 2px 0 8px 0; font-size: 18px; font-weight: 600; color: var(--text); }
#fluxoExec .ex-chips { display: flex; gap: 6px; flex-wrap: wrap; }
#fluxoExec .ex-chip { display: inline-block; padding: 3px 10px; border-radius: 20px; font: 600 12px inherit; font-family: inherit; background: var(--surface2); color: var(--text-dim); border: .625px solid var(--panel-border); }
#fluxoExec .ex-chip.pink { background: var(--pink-dim); color: var(--pink); border-color: rgba(237,109,162,.4); }
#fluxoExec .ex-chip.bad { background: var(--danger-dim); color: var(--danger); border-color: var(--danger-bord); }
#fluxoExec .ex-chip.warn { background: var(--warn-dim); color: var(--warn); border-color: var(--warn-bord); }
#fluxoExec .ex-chip.ok { background: var(--ok-dim); color: var(--ok); border-color: var(--ok-bord); }
#fluxoExec .ex-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-top: 14px; }
#fluxoExec .ex-kpi .v { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: var(--text); }
#fluxoExec .ex-kpi .v.bad { color: var(--danger); } #fluxoExec .ex-kpi .v.warn { color: var(--warn); } #fluxoExec .ex-kpi .v.ok { color: var(--ok); }
#fluxoExec .ex-kpi .l { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); margin-top: 2px; }
#fluxoExec .ex-barra { display: flex; height: 22px; border-radius: 6px; overflow: hidden; background: var(--surface2); margin-top: 10px; }
#fluxoExec .ex-barra > div { height: 100%; min-width: 3px; }
#fluxoExec .ex-leg { list-style: none; margin: 10px 0 0 0; padding: 0; font-size: 12.5px; }
#fluxoExec .ex-leg li { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: var(--text-dim); }
#fluxoExec .ex-leg li i { width: 10px; height: 10px; border-radius: 2px; flex: none; }
#fluxoExec .ex-leg li b { margin-left: auto; color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
#fluxoExec .ex-leg li.atual { color: var(--text); font-weight: 600; }
#fluxoExec .ex-medidor { height: 12px; border-radius: 999px; background: var(--surface2); overflow: hidden; margin-top: 12px; }
#fluxoExec .ex-medidor > div { height: 100%; border-radius: 999px; transition: width .6s ease; }
#fluxoExec .ex-comp { margin-top: 10px; display: grid; gap: 10px; }
#fluxoExec .ex-comp .linha { display: grid; grid-template-columns: 120px 1fr 64px; align-items: center; gap: 10px; font-size: 12.5px; color: var(--text-dim); }
#fluxoExec .ex-comp .trilho { height: 12px; border-radius: 6px; background: var(--surface2); overflow: hidden; }
#fluxoExec .ex-comp .trilho > div { height: 100%; border-radius: 6px; }
#fluxoExec .ex-comp .linha b { text-align: right; color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
#fluxoExec .ex-resumo { font-size: 14px; line-height: 1.6; color: var(--text); }
#fluxoExec .ex-nota { font-size: 12px; color: var(--text3); margin-top: 8px; line-height: 1.5; }
"""

V17_JS = r"""
// ===== Visao executiva do Fluxograma (aparece ao buscar um chamado) =====
function exTitulo(k) { const f = FLOW_MAIN_STAGES.concat([FLOW_SECONDARY_STAGE]).find(s => s.key === k); return f ? f.title : k; }
function exCor(k) { return (typeof STAGE_COLORS === 'object' && STAGE_COLORS[k]) || '#878799'; }
function exFluxoRender(t) {
  const box = document.getElementById('fluxoExec'); if (!box) return;
  if (!t) { box.innerHTML = ''; return; }
  const agora = (typeof NOW !== 'undefined' && NOW) ? new Date(NOW) : new Date();
  const {curStage, hist, path} = computeTicketFlowPath(t);
  const tempos = hist.length ? stageDurationsForTicket(hist) : {};
  const criado = parseDt(t.createdDate), fim = t.resolvedIn ? parseDt(t.resolvedIn) : agora;
  const idadeH = criado ? (fim - criado) / 3600000 : null;
  const paradoH = t._hoursSinceUpdate !== undefined && t._hoursSinceUpdate !== null ? t._hoursSinceUpdate : null;
  const sla = t.slaSolutionDate ? parseDt(t.slaSolutionDate) : null;
  const slaH = sla ? (sla - agora) / 3600000 : null;
  const slaPct = sla && criado ? Math.max(0, Math.round((agora - criado) / (sla - criado) * 100)) : null;
  const slaCls = slaPct === null ? '' : slaPct >= 100 ? 'bad' : slaPct >= 75 ? 'warn' : 'ok';
  const urg = t.urgency || '', encerrado = curStage === 'encerrado' || !!t.resolvedIn;
  const chips = '<span class="ex-chip pink">' + esc(t.status || (t.resolvedIn ? 'Resolvido' : '-')) + '</span><span class="ex-chip">' + esc(t.category || 'Sem categoria') + '</span>'
    + (urg ? '<span class="ex-chip ' + (urg === 'Alta' ? 'bad' : urg === 'Média' ? 'warn' : '') + '">Urgência ' + esc(urg) + '</span>' : '') + '<span class="ex-chip">' + esc(exTitulo(curStage)) + '</span>';

  // 1) tempo por etapa
  const itens = Object.keys(tempos).filter(k => tempos[k] > 0).sort((a, b) => path.indexOf(a) - path.indexOf(b));
  const total = itens.reduce((s, k) => s + tempos[k], 0) || 1;
  const barra = itens.length ? '<div class="ex-barra">' + itens.map(k => '<div title="' + esc(exTitulo(k)) + ': ' + fmtH(tempos[k]) + '" style="width:' + (tempos[k] * 100 / total).toFixed(1) + '%;background:' + exCor(k) + ';"></div>').join('') + '</div>'
    + '<ul class="ex-leg">' + itens.map(k => '<li class="' + (k === curStage ? 'atual' : '') + '"><i style="background:' + exCor(k) + ';"></i>' + esc(exTitulo(k)) + (k === curStage && !encerrado ? ' · etapa atual' : '') + '<b>' + fmtH(tempos[k]) + '</b></li>').join('') + '</ul>'
    : '<div class="ex-nota">Este chamado ainda não tem histórico de etapas para medir.</div>';

  // 2) SLA
  const medidor = slaPct === null ? '<div class="ex-nota">Sem SLA definido para este chamado.</div>'
    : '<div class="ex-medidor"><div style="width:' + Math.min(100, slaPct) + '%;background:var(--' + (slaCls === 'bad' ? 'danger' : slaCls === 'warn' ? 'warn-solid' : 'ok') + ');"></div></div>'
      + '<div class="ex-nota" style="font-size:13px;color:var(--text);">' + slaPct + '% do prazo consumido · ' + (slaH < 0 ? '<b>vencido há ' + fmtH(-slaH) + '</b>' : 'vence em <b>' + fmtH(slaH) + '</b>') + '</div>';

  // 3) idade frente a media da categoria (chamados abertos)
  const mesmaCat = (typeof TICKETS !== 'undefined' ? TICKETS : []).filter(x => x !== t && x.category === t.category && x._hoursOpen !== undefined && x._hoursOpen !== null);
  const mediaCat = mesmaCat.length ? mesmaCat.reduce((s, x) => s + x._hoursOpen, 0) / mesmaCat.length : null;
  const mediaParado = mesmaCat.length ? mesmaCat.reduce((s, x) => s + (x._hoursSinceUpdate || 0), 0) / mesmaCat.length : null;
  const maxC = Math.max(idadeH || 0, mediaCat || 0, paradoH || 0, mediaParado || 0, 1);
  const lin = (nome, v, cor) => v === null ? '' : '<div class="linha"><span>' + nome + '</span><div class="trilho"><div style="width:' + Math.max(2, v * 100 / maxC).toFixed(1) + '%;background:' + cor + ';"></div></div><b>' + fmtH(v) + '</b></div>';
  const comp = '<div class="ex-comp">' + lin('Idade do chamado', idadeH, 'var(--pink)') + lin('Média da categoria', mediaCat, 'var(--navy-lt)') + lin('Parado há', paradoH, 'var(--pink)') + lin('Parado (média)', mediaParado, 'var(--navy-lt)') + '</div>'
    + '<div class="ex-nota">Média calculada entre os ' + mesmaCat.length + ' outros chamados abertos da mesma categoria.</div>';

  // 4) resumo executivo
  const prox = (typeof CFG_PROXIMO === 'object' && CFG_PROXIMO[t.status]) || 'Seguir o fluxo de atendimento conforme a etapa.';
  const frases = ['O chamado ' + esc(t.protocol) + ' (' + esc(t.category || 'sem categoria') + (urg ? ', urgência ' + esc(urg.toLowerCase()) : '') + ') ' + (encerrado ? 'está encerrado' : 'está em <b>' + esc(exTitulo(curStage)) + '</b>') + (idadeH !== null ? ', com ' + fmtH(idadeH) + (encerrado ? ' da abertura à resolução' : ' de idade') : '') + '.'];
  if (!encerrado && paradoH !== null) frases.push('Sem atualização há ' + fmtH(paradoH) + (mediaParado !== null ? (paradoH > mediaParado * 1.5 ? ', acima do normal da categoria' : ', dentro do normal da categoria') : '') + '.');
  if (slaPct !== null) frases.push(slaH < 0 ? 'O SLA está <b>vencido há ' + fmtH(-slaH) + '</b>.' : 'O SLA vence em ' + fmtH(slaH) + ' (' + slaPct + '% do prazo consumido).');
  frases.push('Passou por ' + path.length + ' etapa' + (path.length === 1 ? '' : 's') + (itens.length ? ', e a que mais consumiu tempo foi ' + esc(exTitulo(itens.slice().sort((a, b) => tempos[b] - tempos[a])[0])) + '.' : '.'));
  if (!encerrado) frases.push('Próximo passo: ' + esc(prox));
  if (t.ownerName) frases.push('Responsável: ' + esc(t.ownerName) + '.');

  box.innerHTML = '<div class="ex-wrap">'
    + '<div class="panel ex-full"><div class="ex-topo"><div><div class="ex-prot">VISÃO EXECUTIVA · CHAMADO ' + esc(t.protocol) + '</div><h3>' + esc(t.subject || '') + '</h3><div class="ex-chips">' + chips + '</div></div>'
    + '<div class="ex-chips"><a class="ex-chip" target="_blank" rel="noopener" href="' + MOVIDESK_BASE + t.id + '">Abrir no Movidesk</a></div></div>'
    + '<div class="ex-kpis">'
    + '<div class="ex-kpi"><div class="v">' + (idadeH !== null ? fmtH(idadeH) : '-') + '</div><div class="l">' + (encerrado ? 'Tempo até resolver' : 'Idade') + '</div></div>'
    + '<div class="ex-kpi"><div class="v ' + (paradoH !== null && paradoH >= 48 && !encerrado ? 'warn' : '') + '">' + (encerrado ? '-' : paradoH !== null ? fmtH(paradoH) : '-') + '</div><div class="l">Sem atualização</div></div>'
    + '<div class="ex-kpi"><div class="v ' + slaCls + '">' + (slaPct !== null ? slaPct + '%' : '-') + '</div><div class="l">Prazo (SLA) consumido</div></div>'
    + '<div class="ex-kpi"><div class="v">' + esc(exTitulo(curStage)) + '</div><div class="l">Etapa atual</div></div></div></div>'
    + '<div class="panel"><h2>Tempo em cada etapa</h2>' + barra + '</div>'
    + '<div class="panel"><h2>SLA</h2>' + medidor + '</div>'
    + '<div class="panel"><h2>Idade frente à categoria</h2>' + comp + '</div>'
    + '<div class="panel"><h2>Resumo executivo</h2><div class="ex-resumo">' + frases.join(' ') + '</div></div></div>';
}
{
  const _c = carregarChamadoFluxo; carregarChamadoFluxo = function(t) { _c(t); try { exFluxoRender(t); } catch (e) { console.error(e); } };
  const _l = limparBuscaFluxo; limparBuscaFluxo = function() { _l(); exFluxoRender(null); };
}
"""


def aplicar_v17(html):
    a = '<div class="grid" id="fluxoCardsContainer"'
    if a in html:
        html = html.replace(a, '<div id="fluxoExec"></div>\n    ' + a, 1)
    return html
