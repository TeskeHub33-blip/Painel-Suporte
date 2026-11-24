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
#gridChatsLive .esc-hora { font-size: clamp(22px, 1.7vw, 32px); font-weight: 700; letter-spacing: -0.5px; color: var(--text); font-variant-numeric: tabular-nums; }
#gridChatsLive .esc-pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 20px; font: 600 12px inherit; font-family: inherit; white-space: nowrap; }
#gridChatsLive .esc-pill i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; background: currentColor; }
#gridChatsLive .esc-pill.esc { background: var(--ok-dim); color: var(--ok); border: .625px solid var(--ok-bord); }
#gridChatsLive .esc-pill.sob { background: var(--pink-dim); color: var(--pink); border: .625px solid rgba(237,109,162,.4); }
#gridChatsLive .esc-pill.alerta { background: var(--warn-dim); color: var(--warn); border: .625px solid var(--warn-bord); }
#gridChatsLive .esc-grupo { margin-top: 18px; }
#gridChatsLive .esc-g-tit { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--text3); display: flex; align-items: center; gap: 12px; }
#gridChatsLive .esc-g-tit::after { content: ''; flex: 1; height: .5px; background: var(--panel-border); }
#gridChatsLive .esc-grade { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 10px; }
@media (max-width: 1100px) { #gridChatsLive .esc-grade { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { #gridChatsLive .esc-grade { grid-template-columns: minmax(0, 1fr); } }
#gridChatsLive .esc-card { position: relative; display: flex; flex-direction: column; gap: 10px; padding: 16px 16px 14px 20px; border-radius: 6px; background: var(--surface2); overflow: hidden; transition: background .15s; }
#gridChatsLive .esc-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--pink); }
#gridChatsLive .esc-card.off::before { background: var(--text3); opacity: .5; }
#gridChatsLive .esc-card.alerta { background: var(--warn-dim); }
#gridChatsLive .esc-card.alerta::before { background: var(--warn-solid, var(--warn)); }
#gridChatsLive .esc-c-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
#gridChatsLive .esc-c-atv { font-size: clamp(11px, .75vw, 14px); font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); }
#gridChatsLive .esc-c-det { font-size: 11px; color: var(--text3); margin-top: -6px; }
#gridChatsLive .esc-c-pessoa { display: flex; align-items: center; gap: 10px; min-width: 0; }
#gridChatsLive .esc-c-av { flex: none; width: clamp(34px, 2.5vw, 48px); height: clamp(34px, 2.5vw, 48px); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: var(--pink-dim); color: var(--pink); font-size: clamp(12px, .85vw, 16px); font-weight: 700; }
#gridChatsLive .esc-c-nome { font-size: clamp(16px, 1.3vw, 25px); font-weight: 600; white-space: nowrap; color: var(--text); line-height: 1.25; overflow: hidden; text-overflow: ellipsis; }
#gridChatsLive .esc-c-res { display: flex; flex-wrap: wrap; gap: 6px; min-height: 22px; font-size: 12px; }
#gridChatsLive .esc-c-chip { display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 20px; background: var(--panel); color: var(--text-dim); font-size: clamp(12px, .8vw, 15px); }
#gridChatsLive .esc-c-chip i { font-style: normal; font-size: 10px; font-weight: 700; color: var(--text3); }
#gridChatsLive .esc-c-vazio { font-size: 14px; color: var(--text3); min-height: 64px; display: flex; align-items: center; gap: 5px; }
#gridChatsLive .esc-card.alerta .esc-c-vazio { color: var(--warn); }
#gridChatsLive .esc-c-prox { margin-top: auto; padding-top: 8px; border-top: .5px solid var(--panel-border); font-size: clamp(12px, .8vw, 15px); color: var(--text-dim); display: flex; gap: 8px; align-items: baseline; }
#gridChatsLive .esc-c-prox span { font-size: 11px; font-weight: 600; color: var(--text3); font-variant-numeric: tabular-nums; }
#gridChatsLive .esc-vz { color: var(--text3); }
#gridChatsLive .esc-card { cursor: pointer; }
html.tv #gridChatsLive .esc-manual { display: none; }
#gridChatsLive .esc-card:hover { outline: 1.5px solid var(--accent, #6c8cff); }
.esc-modal { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,.55); display: flex; align-items: center; justify-content: center; padding: 16px; }
.esc-modal-box { background: var(--panel, #1b2030); color: var(--text, #e8ecf5); border: .5px solid var(--panel-border, #333); border-radius: 12px; padding: 18px 20px; width: min(440px, 100%); display: flex; flex-direction: column; gap: 10px; }
.esc-modal-box h3 { margin: 0; font-size: 17px; }
.esc-modal-box label { display: flex; flex-direction: column; gap: 3px; font-size: 12px; color: var(--text-dim, #aab); }
.esc-modal-box input, .esc-modal-box select { font: inherit; font-size: 14px; padding: 7px 9px; border-radius: 7px; border: 1px solid var(--panel-border, #444); background: var(--bg, #11151f); color: var(--text, #e8ecf5); }
.esc-modal-box .esc-m-linha { display: flex; gap: 10px; }
.esc-modal-box .esc-m-linha label { flex: 1; }
.esc-modal-box .esc-m-bot { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.esc-modal-box button { font: inherit; font-size: 13px; font-weight: 600; padding: 7px 12px; border-radius: 7px; border: 1px solid var(--panel-border, #444); background: transparent; color: var(--text, #e8ecf5); cursor: pointer; }
.esc-modal-box button.prim { background: var(--accent, #4f6bff); border-color: transparent; color: #fff; }
.esc-modal-box .esc-m-msg { font-size: 12px; color: var(--warn, #e8b04a); min-height: 16px; }
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
// Preenchimento manual na tela (vale sobre a planilha): mapa data -> hora -> atividade -> "P|2a|3a". Fica no GitHub (api/escala) e neste navegador.
function escManualMapa() {
  const rem = window.__ESC || {};
  let loc = null; try { loc = JSON.parse(localStorage.getItem('escManualLocal') || 'null'); } catch (e) {}
  return (loc && (!rem.salvo_em || loc.salvo_em > rem.salvo_em)) ? (loc.manual || {}) : (rem.manual || {});
}
function escManualCell(ai, pt) {
  const m = ((escManualMapa()[pt.data] || {})[pt.hora] || {})[ai];
  if (m === undefined || m === null) return null;
  return {fora: false, manual: true, nomes: String(m).split('|').map(x => x.trim()), soPrincipal: false};
}
function escalaCelula(dados, ai, pt) {
  const man = escManualCell(ai, pt); if (man) return man;
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
  const man = escManualCell(ai, pt);
  if (man) { const nm = man.nomes.filter(Boolean); return {tipo: 'esc', nomes: nm.slice(0, 1), reserva: nm.slice(1)}; }
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
    const abre = cls => '<div class="esc-card' + cls + '" onclick="escEdita(' + ai + ')" title="Clique para preencher manualmente">';
    const cab = '<div class="esc-c-top"><span class="esc-c-atv">' + esc(titulo) + '</span>' + (c && c.manual ? '<span class="esc-pill sob esc-manual"><i></i>Manual</span>' : (sob ? '<span class="esc-pill sob"><i></i>Sobreaviso</span>' : '')) + '</div>' + (detalhe ? '<div class="esc-c-det">' + esc(detalhe) + '</div>' : '');
    if (!c) return abre(' off') + cab + '<div class="esc-c-vazio">Escala não publicada</div>' + rodape + '</div>';
    if (c.fora) return abre(' off') + cab + '<div class="esc-c-vazio">Fora do horário</div>' + rodape + '</div>';
    const nomes = c.nomes.filter(Boolean);
    if (!nomes.length) { semResp++; return abre(' alerta') + cab + '<div class="esc-c-vazio"><b>Sem responsável</b> nesta hora</div>' + rodape + '</div>'; }
    const reserva = nomes.slice(1).map((x, i) => '<span class="esc-c-chip"><i>' + (i + 2) + 'º</i>' + esc(x) + '</span>').join('');
    return abre('') + cab + '<div class="esc-c-pessoa"><span class="esc-c-av">' + esc(escIniciais(nomes[0])) + '</span><span class="esc-c-nome">' + esc(nomes[0]) + '</span></div>'
      + '<div class="esc-c-res">' + (reserva || '<span class="esc-vz">sem reserva</span>') + '</div>' + rodape + '</div>';
  });
  const grupo = (titulo, de, ate) => '<div class="esc-grupo"><div class="esc-g-tit">' + titulo + '</div><div class="esc-grade">' + cartoes.slice(de, ate).join('') + '</div></div>';
  const resumo = semResp ? '<span class="esc-pill alerta"><i></i>' + semResp + ' sem responsável</span>' : '<span class="esc-pill esc"><i></i>Todas cobertas</span>';
  return '<div class="panel esc-tab"><div class="esc-cab"><div><h2>Escala agora</h2><div class="panel-sub">Quem está em cada atividade nesta hora, pela planilha de atividades.</div></div>'
    + '<div class="esc-cab-dir"><span class="esc-hora">' + hh(pt.hora) + '</span>' + resumo + '</div></div>'
    + grupo('Canais de atendimento', 0, 4) + grupo('Chamados e N2', 4, 8)
    + '<div class="esc-rodape">Escala lida da planilha em ' + esc(dados.gerado_em || '-') + ' e conferida uma vez por dia.'
    + (soPrincipal ? ' Para hoje a planilha só informou o Principal de cada atividade.' : '')
    + ' Em sábados, domingos e feriados, Chamados Novos e priorizados mostram o sobreaviso. Clique em um cartão para preencher manualmente.</div></div>';
}
function escNomesConhecidos() {
  const set = new Set(), d = escalaDados();
  Object.keys((d && d.dias) || {}).forEach(k => ((d.dias[k]) || []).forEach(h => (h || []).forEach(c => String(c).split('|').forEach(x => { x = x.trim(); if (x && x !== '—' && x !== '-' && x.indexOf('fora') !== 0) set.add(x); }))));
  return Array.from(set).sort((a, b) => a.localeCompare(b));
}
function escV(id) { const e = document.getElementById(id); return e ? e.value : ''; }
function escFecha() { const m = document.getElementById('escModal'); if (m) m.remove(); }
function escEdita(ai) {
  const dados = escalaDados(); if (!dados) return;
  const pt = escalaPartes(Date.now()), AT = dados.atividades || [], atual = escalaCelula(dados, ai, pt);
  const nomes = atual && !atual.fora ? atual.nomes : [];
  escFecha();
  const ov = document.createElement('div'); ov.id = 'escModal'; ov.className = 'esc-modal';
  ov.onclick = e => { if (e.target === ov) escFecha(); };
  const hs = (id, sel) => '<select id="' + id + '">' + Array.from({length: 24}, (_, h) => '<option value="' + h + '"' + (h === sel ? ' selected' : '') + '>' + String(h).padStart(2, '0') + 'h</option>').join('') + '</select>';
  const campo = (i, rot) => '<label>' + rot + '<input type="text" id="escN' + i + '" list="escNomes" value="' + esc(nomes[i] || '') + '" placeholder="Nome (deixe vazio para ninguém)"></label>';
  ov.innerHTML = '<div class="esc-modal-box"><h3>' + esc((AT[ai] || '').replace(/ *[(].*$/, '')) + ' — preencher manualmente</h3>'
    + '<div style="font-size:12px;color:var(--text3);">Vale sobre a planilha, para todos que abrirem o painel. Hoje, ' + esc(pt.data.split('-').reverse().join('/')) + '.</div>'
    + campo(0, 'Principal') + campo(1, '2º') + campo(2, '3º')
    + '<datalist id="escNomes">' + escNomesConhecidos().map(n => '<option value="' + esc(n) + '">').join('') + '</datalist>'
    + '<div class="esc-m-linha"><label>Das' + hs('escDe', pt.hora) + '</label><label>Até as (inclusive)' + hs('escAte', pt.hora) + '</label></div>'
    + '<div class="esc-m-msg" id="escMsg"></div>'
    + '<div class="esc-m-bot"><button type="button" class="prim" onclick="escSalva(' + ai + ', false)">Salvar</button>'
    + '<button type="button" onclick="escSalva(' + ai + ', true)" title="Apaga o preenchimento manual dessas horas">Voltar para a planilha</button>'
    + '<button type="button" onclick="escFecha()">Cancelar</button></div></div>';
  document.body.appendChild(ov);
}
async function escSalva(ai, limpar) {
  const pt = escalaPartes(Date.now()), de = Number(escV('escDe')), ate = Number(escV('escAte')), msg = document.getElementById('escMsg');
  if (ate < de) { if (msg) msg.textContent = 'A hora final precisa ser igual ou depois da inicial.'; return; }
  const nomes = [0, 1, 2].map(i => escV('escN' + i).replace(/[|]/g, ' ').trim());
  if (!limpar && !nomes[0] && (nomes[1] || nomes[2])) { if (msg) msg.textContent = 'Preencha o Principal antes do 2º e do 3º.'; return; }
  const base = JSON.parse(JSON.stringify(escManualMapa()));
  base[pt.data] = base[pt.data] || {};
  for (let h = de; h <= ate; h++) {
    base[pt.data][h] = base[pt.data][h] || {};
    if (limpar) delete base[pt.data][h][ai]; else base[pt.data][h][ai] = nomes.join('|');
  }
  try { localStorage.setItem('escManualLocal', JSON.stringify({salvo_em: new Date().toISOString(), manual: base})); } catch (e) {}
  escalaAtualiza();
  if (msg) msg.textContent = 'Salvando para todos...';
  try {
    const resp = await fetch('/api/escala', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data: pt.data, de: de, ate: ate, atividade: ai, nomes: limpar ? null : nomes})});
    const d = await resp.json().catch(() => ({}));
    if (!resp.ok) { if (msg) msg.textContent = (d.erro || ('Erro ' + resp.status)) + ' Salvo só neste navegador.'; return; }
    if (d.salvo_em) { window.__ESC = {salvo_em: d.salvo_em, manual: base}; try { localStorage.removeItem('escManualLocal'); } catch (e) {} escalaAtualiza(); }
  } catch (e) { if (msg) msg.textContent = 'Sem conexão: salvo só neste navegador.'; return; }
  escFecha();
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
