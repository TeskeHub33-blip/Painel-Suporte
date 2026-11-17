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
/* ===== Escala agora (Ao Vivo) ===== */
#gridChatsLive .esc-panel { display: flex; flex-direction: column; gap: 6px; }
#gridChatsLive .esc-linha { display: flex; align-items: center; gap: 10px; font-size: 12.5px; color: var(--text3); }
#gridChatsLive .esc-pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 20px; font: 600 12px inherit; font-family: inherit; }
#gridChatsLive .esc-pill i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; background: currentColor; }
#gridChatsLive .esc-pill.esc { background: var(--ok-dim); color: var(--ok); border: .625px solid var(--ok-bord); }
#gridChatsLive .esc-pill.sob { background: var(--pink-dim); color: var(--pink); border: .625px solid rgba(237,109,162,.4); }
#gridChatsLive .esc-pill.sem { background: var(--surface2); color: var(--text3); border: .625px solid var(--panel-border); }
#gridChatsLive .esc-nome { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: var(--text); line-height: 1.2; margin: 4px 0 2px 0; }
#gridChatsLive .esc-nome.vazio { font-size: 15px; font-weight: 400; letter-spacing: 0; color: var(--text3); }
#gridChatsLive .esc-prox { display: flex; flex-wrap: wrap; gap: 6px 14px; margin-top: 6px; padding-top: 10px; border-top: .5px solid var(--panel-border); font-size: 12px; color: var(--text3); }
#gridChatsLive .esc-prox b { color: var(--text-dim); font-weight: 600; }
#gridChatsLive .esc-tab { grid-column: 1 / -1; flex: 1 1 100%; width: 100%; box-sizing: border-box; min-height: 0; order: 3; }
#gridChatsLive .esc-panel { flex: 1 1 320px; }
#gridChatsLive .esc-rodape { flex: 1 1 100%; order: 4; }
#gridChatsLive .esc-tab table { width: 100%; border-collapse: collapse; margin-top: 8px; }
#gridChatsLive .esc-tab td, #gridChatsLive .esc-tab th { padding: 8px 10px; font-size: 13px; text-align: left; border-bottom: .5px solid var(--panel-border); }
#gridChatsLive .esc-tab th { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); }
#gridChatsLive .esc-vz { color: var(--text3); }
#gridChatsLive .esc-tab tr.esc-alerta td { background: var(--warn-dim); }
#gridChatsLive .esc-panel { min-height: 0; }
#gridChatsLive .esc-rodape { grid-column: 1 / -1; font-size: 11.5px; color: var(--text3); line-height: 1.5; margin-top: 2px; }
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
  const dop = pt.hora >= 6 ? pt.data : escalaDiaAnterior(pt.data), dia = (dados.dias || {})[dop];
  if (!dia) return null;
  const txt = (dia[(pt.hora - 6 + 24) % 24] || [])[ai] || '';
  if (txt === 'fora' || txt.indexOf('fora') === 0) return {fora: true, nomes: []};
  return {fora: false, nomes: txt.split('|').map(x => { x = x.trim(); return x === '—' || x === '-' ? '' : x; }), aConfirmar: escalaDepois(dados, dop, pt.hora)};
}
function escalaDepois(dados, dop, hora) {
  const c = dados.conferido_ate; if (!c) return false;
  const d = c.slice(0, 10), h = Number(c.slice(11, 13));
  return dop > d || (dop === d && ((hora - 6 + 24) % 24) > ((h - 6 + 24) % 24));
}
// Cards: no fim de semana/feriado com sobreaviso publicado, vale o sobreaviso; senao, o Principal da planilha.
function escalaQuem(dados, ai, pt) {
  const sob = (dados.sobreaviso || {})[pt.data];
  if (sob) return {tipo: 'sob', nomes: sob[pt.hora] || []};
  if (pt.fds) return {tipo: 'sob', nomes: null};
  const c = escalaCelula(dados, ai, pt);
  if (!c) return {tipo: 'sem', nomes: null};
  return {tipo: 'esc', nomes: c.nomes.filter(Boolean).slice(0, 1), reserva: c.nomes.filter(Boolean).slice(1), aConfirmar: c.aConfirmar};
}
function renderEscalaAgora() {
  const dados = escalaDados(); if (!dados || !dados.dias) return '';
  const agora = Date.now(), pt = escalaPartes(agora), hh = h => String(h).padStart(2, '0') + 'h', AT = dados.atividades || [];
  const quadro = (titulo, ai) => {
    const q = escalaQuem(dados, ai, pt);
    const pill = q.tipo === 'sob' ? '<span class="esc-pill sob"><i></i>Sobreaviso</span>' : q.tipo === 'esc' ? '<span class="esc-pill esc"><i></i>Em turno</span>' : '<span class="esc-pill sem"><i></i>Sem escala</span>';
    const nome = q.nomes && q.nomes.length ? '<div class="esc-nome">' + esc(q.nomes.join(' · ')) + '</div>'
      : '<div class="esc-nome vazio">' + (q.nomes === null ? (q.tipo === 'sob' ? 'Sobreaviso deste dia não publicado' : 'Escala deste dia não publicada') : 'Ninguém escalado nesta hora') + '</div>';
    const res = q.reserva && q.reserva.length ? '<div class="esc-linha">Na sequência: ' + esc(q.reserva.join(' · ')) + '</div>' : '';
    let prox = '';
    for (let k = 1; k <= 5; k++) {
      const p2 = escalaPartes(agora + k * 3600000), q2 = escalaQuem(dados, ai, p2);
      prox += '<span>' + hh(p2.hora) + ' <b>' + (q2.nomes && q2.nomes.length ? esc(q2.nomes.join(' · ')) : '—') + '</b></span>';
    }
    return '<div class="panel esc-panel"><h2>' + titulo + '</h2><div class="esc-linha">' + pill + '<span>agora · ' + hh(pt.hora) + '</span></div>' + nome + res + '<div class="esc-prox">' + prox + '</div></div>';
  };
  // tabela com todas as atividades da planilha, na hora atual
  const pn = escalaPartes(agora + 3600000);
  let algumAConfirmar = false;
  const linhas = AT.map((nomeAtv, ai) => {
    const c = escalaCelula(dados, ai, pt), n = escalaCelula(dados, ai, pn);
    if (c && c.aConfirmar) algumAConfirmar = true;
    const cel = (x, i) => !x ? '<td class="esc-vz">não publicada</td>' : x.fora ? (i === 0 ? '<td class="esc-vz">fora do horário</td>' : '<td class="esc-vz">—</td>') : '<td>' + (x.nomes[i] ? esc(x.nomes[i]) : '<span class="esc-vz">—</span>') + '</td>';
    const sem = c && !c.fora && !c.nomes[0];
    return '<tr class="' + (sem ? 'esc-alerta' : '') + '"><td><b>' + esc(nomeAtv) + '</b></td>' + cel(c, 0) + cel(c, 1) + cel(c, 2) + cel(n, 0) + '</tr>';
  }).join('');
  const sobHoje = (dados.sobreaviso || {})[pt.data], sobLinha = sobHoje ? '<div class="esc-rodape" style="margin-top:8px;"><span class="esc-pill sob"><i></i>Sobreaviso</span> nesta hora: <b>' + (esc((sobHoje[pt.hora] || []).join(' · ')) || '—') + '</b></div>' : '';
  const tabela = '<div class="panel esc-tab"><h2>Escala agora · todas as atividades</h2><div class="panel-sub">Quem está em cada atividade às ' + hh(pt.hora) + ', pela planilha de atividades. Linha em destaque = atividade sem responsável nesta hora.</div>'
    + '<table><thead><tr><th>Atividade</th><th>Principal</th><th>Secundária</th><th>Terceira</th><th>Principal às ' + hh(pn.hora) + '</th></tr></thead><tbody>' + linhas + '</tbody></table>' + sobLinha + '</div>';
  return quadro('Chamados Novos', 4) + quadro('Chamados priorizados', 5) + tabela
    + '<div class="esc-rodape">Escala lida da planilha em ' + esc(dados.gerado_em || '-') + ' e conferida uma vez por dia.'
    + (algumAConfirmar || (dados.conferido_ate && pt.data > dados.conferido_ate.slice(0, 10)) ? ' <b>Atenção:</b> os dias depois de ' + esc(dados.conferido_ate) + ' vieram de uma cópia anterior da planilha e podem ter mudado.' : '')
    + ' Sábados, domingos e feriados com sobreaviso publicado mostram o sobreaviso nos dois quadros de chamados.</div>';
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
