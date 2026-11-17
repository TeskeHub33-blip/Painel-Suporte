# -*- coding: utf-8 -*-
"""Quadros "Chamados Novos" e "Chamados priorizados" da aba Ao Vivo (no lugar dos cards de chat).

Dados: escala.json (gerado a partir das planilhas de escala e de sobreaviso do SharePoint). O painel e' estatico e nao
le o SharePoint: o arquivo e' atualizado por quem publica a escala. Dias uteis mostram o Principal da hora (so' ha dados
dos dias publicados); sabados, domingos e feriados mostram quem esta de sobreaviso.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

V16_CSS = """
/* ===== Escala agora (Ao Vivo): cartoes por atividade ===== */
#gridChatsLive .esc-tab { flex: 1 1 100%; width: 100%; box-sizing: border-box; min-height: 0; }
#gridChatsLive .esc-cab { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
#gridChatsLive .esc-cab-dir { display: flex; align-items: center; gap: 10px; }
#gridChatsLive .esc-hora { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: var(--text); font-variant-numeric: tabular-nums; }
#gridChatsLive .esc-pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 20px; font: 600 12px inherit; font-family: inherit; white-space: nowrap; }
#gridChatsLive .esc-pill i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; background: currentColor; }
#gridChatsLive .esc-pill.esc { background: var(--ok-dim); color: var(--ok); border: .625px solid var(--ok-bord); }
#gridChatsLive .esc-pill.sob { background: var(--pink-dim); color: var(--pink); border: .625px solid rgba(237,109,162,.4); }
#gridChatsLive .esc-pill.alerta { background: var(--warn-dim); color: var(--warn); border: .625px solid var(--warn-bord); }
#gridChatsLive .esc-grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap: 12px; margin-top: 16px; }
#gridChatsLive .esc-card { position: relative; display: flex; flex-direction: column; gap: 8px; padding: 14px 14px 12px 16px; border-radius: 6px; background: var(--surface2); overflow: hidden; transition: background .15s; }
#gridChatsLive .esc-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--pink); }
#gridChatsLive .esc-card.off::before { background: var(--text3); opacity: .5; }
#gridChatsLive .esc-card.alerta { background: var(--warn-dim); }
#gridChatsLive .esc-card.alerta::before { background: var(--warn-solid, var(--warn)); }
#gridChatsLive .esc-c-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
#gridChatsLive .esc-c-atv { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); }
#gridChatsLive .esc-c-det { font-size: 11px; color: var(--text3); margin-top: -6px; }
#gridChatsLive .esc-c-pessoa { display: flex; align-items: center; gap: 10px; min-width: 0; }
#gridChatsLive .esc-c-av { flex: none; width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: var(--pink-dim); color: var(--pink); font-size: 12px; font-weight: 700; }
#gridChatsLive .esc-c-nome { font-size: 16px; font-weight: 600; color: var(--text); line-height: 1.25; overflow: hidden; text-overflow: ellipsis; }
#gridChatsLive .esc-c-res { display: flex; flex-wrap: wrap; gap: 6px; min-height: 22px; font-size: 12px; }
#gridChatsLive .esc-c-chip { display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 20px; background: var(--panel); color: var(--text-dim); font-size: 12px; }
#gridChatsLive .esc-c-chip i { font-style: normal; font-size: 10px; font-weight: 700; color: var(--text3); }
#gridChatsLive .esc-c-vazio { font-size: 14px; color: var(--text3); min-height: 64px; display: flex; align-items: center; gap: 5px; }
#gridChatsLive .esc-card.alerta .esc-c-vazio { color: var(--warn); }
#gridChatsLive .esc-c-prox { margin-top: auto; padding-top: 8px; border-top: .5px solid var(--panel-border); font-size: 12px; color: var(--text-dim); display: flex; gap: 8px; align-items: baseline; }
#gridChatsLive .esc-c-prox span { font-size: 11px; font-weight: 600; color: var(--text3); font-variant-numeric: tabular-nums; }
#gridChatsLive .esc-vz { color: var(--text3); }
#gridChatsLive .esc-rodape { font-size: 11.5px; color: var(--text3); line-height: 1.5; margin-top: 14px; }
"""

V16_JS = r"""
// ===== Escala (Ao Vivo): cards Chamados Novos / priorizados + tabela com todas as atividades =====
// escala.json: dias[AAAA-MM-DD] = 24 posicoes do dia operacional (06h..23h, 00h..05h); cada posicao = 8 atividades "P|2a|3a".
function escalaDados() { try { return JSON.parse(document.getElementById('escalaDados').textContent); } catch (e) { return null; } }
function escalaPartes(ts) {
  const p = {}; new Intl.DateTimeFormat('en-CA', {timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23', weekday: 'short'})
    .formatToParts(new Date(ts)).forEach(x => { p[x.type] = x.value; });
  return {data: p.year + '-' + p.month + '-' + p.day, hora: Number(p.hour), fds: p.weekday === 'Sat' || p.weekday === 'Sun'};
}
function escalaDiaAnterior(data) { const d = new Date(data + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() - 1); return d.toISOString().slice(0, 10); }
// Celula da planilha para a atividade (indice 0..7) na data/hora de Brasilia. null = dia nao publicado.
function escalaCelula(dados, ai, pt) {
  const dop = pt.data, dia = (dados.dias || {})[dop];      // a planilha usa a data do calendario em todas as horas
  if (!dia) return null;
  const hora = dia[pt.hora];
  if (!hora) return null;      // hora que o SharePoint nao devolveu: sem escala publicada
  const txt = hora[ai] || '';
  if (txt === 'fora' || txt.indexOf('fora') === 0) return {fora: true, nomes: []};
  return {fora: false, nomes: txt.split('|').map(x => { x = x.trim(); return x === '—' || x === '-' ? '' : x; }), soPrincipal: (dados.so_principal || []).indexOf(dop) !== -1};
}
// Cards: no fim de semana/feriado com sobreaviso publicado, vale o sobreaviso; senao, o Principal da planilha.
function escalaQuem(dados, ai, pt) {
  const sob = (dados.sobreaviso || {})[pt.data];
  if (sob) return {tipo: 'sob', nomes: sob[pt.hora] || []};
  if (pt.fds) return {tipo: 'sob', nomes: null};
  const c = escalaCelula(dados, ai, pt);
  if (!c) return {tipo: 'sem', nomes: null};
  return {tipo: 'esc', nomes: c.nomes.filter(Boolean).slice(0, 1), reserva: c.nomes.filter(Boolean).slice(1)};
}
function escIniciais(nome) { const p = String(nome).trim().split(/\s+/); return ((p[0] || '').charAt(0) + (p.length > 1 ? p[p.length - 1].charAt(0) : '')).toUpperCase(); }
function renderEscalaAgora() {
  const dados = escalaDados(); if (!dados || !dados.dias) return '';
  const agora = Date.now(), pt = escalaPartes(agora), pn = escalaPartes(agora + 3600000), hh = h => String(h).padStart(2, '0') + 'h', AT = dados.atividades || [];
  let semResp = 0, soPrincipal = false;
  const cartoes = AT.map((nomeAtv, ai) => {
    let c = escalaCelula(dados, ai, pt), n = escalaCelula(dados, ai, pn), sob = false;
    // Chamados Novos (4) e priorizados (5): em dia com sobreaviso publicado, vale o sobreaviso
    if (ai === 4 || ai === 5) { const q = escalaQuem(dados, ai, pt); if (q.tipo === 'sob') { sob = true; c = q.nomes ? {fora: false, nomes: q.nomes} : null; const q2 = escalaQuem(dados, ai, pn); n = q2.nomes ? {fora: false, nomes: q2.nomes} : null; } }
    if (c && c.soPrincipal) soPrincipal = true;
    const titulo = nomeAtv.replace(/\s*\(.*\)$/, ''), detalhe = (nomeAtv.match(/\((.*)\)$/) || [])[1];
    const prox = !n ? '—' : n.fora ? 'fora do horário' : (n.nomes[0] ? esc(n.nomes[0]) : 'ninguém');
    const rodape = '<div class="esc-c-prox"><span>' + hh(pn.hora) + '</span>' + prox + '</div>';
    const cab = '<div class="esc-c-top"><span class="esc-c-atv">' + esc(titulo) + '</span>' + (sob ? '<span class="esc-pill sob"><i></i>Sobreaviso</span>' : '') + '</div>' + (detalhe ? '<div class="esc-c-det">' + esc(detalhe) + '</div>' : '');
    if (!c) return '<div class="esc-card off">' + cab + '<div class="esc-c-vazio">Escala não publicada</div>' + rodape + '</div>';
    if (c.fora) return '<div class="esc-card off">' + cab + '<div class="esc-c-vazio">Fora do horário</div>' + rodape + '</div>';
    const nomes = c.nomes.filter(Boolean);
    if (!nomes.length) { semResp++; return '<div class="esc-card alerta">' + cab + '<div class="esc-c-vazio"><b>Sem responsável</b> nesta hora</div>' + rodape + '</div>'; }
    const reserva = nomes.slice(1).map((x, i) => '<span class="esc-c-chip"><i>' + (i + 2) + 'º</i>' + esc(x) + '</span>').join('');
    return '<div class="esc-card">' + cab + '<div class="esc-c-pessoa"><span class="esc-c-av">' + esc(escIniciais(nomes[0])) + '</span><span class="esc-c-nome">' + esc(nomes[0]) + '</span></div>'
      + '<div class="esc-c-res">' + (reserva || '<span class="esc-vz">sem reserva</span>') + '</div>' + rodape + '</div>';
  }).join('');
  const resumo = semResp ? '<span class="esc-pill alerta"><i></i>' + semResp + ' sem responsável</span>' : '<span class="esc-pill esc"><i></i>Todas cobertas</span>';
  return '<div class="panel esc-tab"><div class="esc-cab"><div><h2>Escala agora</h2><div class="panel-sub">Quem está em cada atividade nesta hora, pela planilha de atividades.</div></div>'
    + '<div class="esc-cab-dir"><span class="esc-hora">' + hh(pt.hora) + '</span>' + resumo + '</div></div>'
    + '<div class="esc-grade">' + cartoes + '</div>'
    + '<div class="esc-rodape">Escala lida da planilha em ' + esc(dados.gerado_em || '-') + ' e conferida uma vez por dia.'
    + (soPrincipal ? ' Para hoje a planilha só informou o Principal de cada atividade.' : '')
    + ' Em sábados, domingos e feriados, Chamados Novos e priorizados mostram o sobreaviso.</div></div>';
}
function escalaAtualiza() { const g = document.getElementById('gridChatsLive'); if (g) g.innerHTML = renderEscalaAgora(); }
setInterval(escalaAtualiza, 60000);
"""


def aplicar_v16(html):
    try:
        with open(os.path.join(BASE, 'escala.json'), encoding='utf-8') as f:
            dados = json.load(f)
    except Exception:
        dados = {}
    js = json.dumps(dados, ensure_ascii=False).replace('</', '<\\/')
    bloco = f'<script type="application/json" id="escalaDados">{js}</script>\n  '
    return html.replace('<div class="tab-panel" id="tabFluxo">', bloco + '<div class="tab-panel" id="tabFluxo">', 1)
