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
#gridChatsLive .esc-rodape { grid-column: 1 / -1; font-size: 11.5px; color: var(--text3); line-height: 1.5; margin-top: 2px; }
"""

V16_JS = r"""
// ===== Escala agora (Ao Vivo): Chamados Novos e Chamados priorizados =====
function escalaDados() { try { return JSON.parse(document.getElementById('escalaDados').textContent); } catch (e) { return null; } }
function escalaPartes(ts) {
  const p = {}; new Intl.DateTimeFormat('en-CA', {timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23', weekday: 'short'})
    .formatToParts(new Date(ts)).forEach(x => { p[x.type] = x.value; });
  return {data: p.year + '-' + p.month + '-' + p.day, hora: Number(p.hour), fds: p.weekday === 'Sat' || p.weekday === 'Sun'};
}
function escalaDiaAnterior(data) { const d = new Date(data + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() - 1); return d.toISOString().slice(0, 10); }
function escalaQuem(dados, ativ, pt) {
  const sob = (dados.sobreaviso || {})[pt.data];
  if (sob) return {tipo: 'sob', nomes: sob[pt.hora] || []};
  if (pt.fds) return {tipo: 'sob', nomes: null};
  const u = (dados.util || {})[pt.hora >= 6 ? pt.data : escalaDiaAnterior(pt.data)];
  if (!u) return {tipo: 'sem', nomes: null};
  const n = u[ativ][(pt.hora - 6 + 24) % 24];
  return {tipo: 'esc', nomes: n && n !== '—' ? [n] : []};
}
function renderEscalaAgora() {
  const dados = escalaDados(); if (!dados) return '';
  const agora = Date.now(), pt = escalaPartes(agora), hh = h => String(h).padStart(2, '0') + 'h';
  const quadro = (titulo, ativ) => {
    const q = escalaQuem(dados, ativ, pt);
    const pill = q.tipo === 'sob' ? '<span class="esc-pill sob"><i></i>Sobreaviso</span>' : q.tipo === 'esc' ? '<span class="esc-pill esc"><i></i>Em turno</span>' : '<span class="esc-pill sem"><i></i>Sem escala</span>';
    const nome = q.nomes && q.nomes.length ? '<div class="esc-nome">' + esc(q.nomes.join(' · ')) + '</div>'
      : '<div class="esc-nome vazio">' + (q.nomes === null ? (q.tipo === 'sob' ? 'Sobreaviso deste dia não publicado' : 'Escala deste dia não publicada') : 'Ninguém escalado nesta hora') + '</div>';
    let prox = '';
    for (let k = 1; k <= 5; k++) {
      const p2 = escalaPartes(agora + k * 3600000), q2 = escalaQuem(dados, ativ, p2);
      const t2 = q2.nomes && q2.nomes.length ? esc(q2.nomes.join(' · ')) : '—';
      prox += '<span>' + hh(p2.hora) + ' <b>' + t2 + '</b></span>';
    }
    return '<div class="panel esc-panel"><h2>' + titulo + '</h2><div class="esc-linha">' + pill + '<span>agora · ' + hh(pt.hora) + '</span></div>' + nome + '<div class="esc-prox">' + prox + '</div></div>';
  };
  return quadro('Chamados Novos', 'novos') + quadro('Chamados priorizados', 'priorizados')
    + '<div class="esc-rodape">Escala atualizada em ' + esc(dados.gerado_em || '-') + '. Fonte: planilhas de escala e de sobreaviso do time de Suporte. Sábados, domingos e feriados mostram o sobreaviso. Dias úteis só aparecem quando a escala do dia foi publicada.</div>';
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
