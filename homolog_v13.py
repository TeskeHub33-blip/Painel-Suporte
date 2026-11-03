# -*- coding: utf-8 -*-
"""Homologacao v13: aba Historico com a quantidade de chamados abertos e fechados por dia.

SO' a versao de homologacao usa este JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Definicoes (as mesmas do restante da aba: time Suporte, sem cancelados, respeita o filtro de cliente):
  - aberto no dia  = chamado CRIADO naquele dia (data de Brasilia), entre os resolvidos dos meses carregados e os abertos agora
  - fechado no dia = chamado RESOLVIDO naquele dia (resolvedIn), entre os resolvidos dos meses carregados
  - saldo do dia   = abertos - fechados (positivo: a fila cresceu)
"""

V13_CSS = """
/* ===== HOMOLOGACAO v13: Historico, abertos e fechados por dia ===== */
#histDiario .hd-grafico { margin-top: 14px; }
#histDiario .hd-grafico svg { width: 100%; height: auto; display: block; }
#histDiario .hd-det { margin-top: 12px; }
#histDiario .hd-det summary { cursor: pointer; font-size: 13px; font-weight: 600; color: var(--text-dim); padding: 6px 0; }
#histDiario .hd-det summary:hover { color: var(--pink); }
#histDiario .hd-topo { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
#histDiario .hd-tabela { max-height: 360px; overflow: auto; margin-top: 14px; border-radius: 6px; }
#histDiario table { width: 100%; border-collapse: collapse; }
#histDiario td.num, #histDiario th.num { text-align: right; font-variant-numeric: tabular-nums; }
#histDiario tr.hd-fim td { color: var(--text3); }
#histDiario tr.hd-total td { font-weight: 600; border-top: 1.5px solid var(--panel-border); position: sticky; bottom: 0; background: var(--panel); }
#histDiario .hd-pos { color: var(--danger); font-weight: 600; } #histDiario .hd-neg { color: var(--ok); font-weight: 600; }
"""

V13_JS = r"""
// ===== HOMOLOGACAO v13: Historico, abertos e fechados por dia =====
function hdDia(iso) { const d = parseDt(iso); return d ? brasiliaDateStr(d) : null; }
function hdDados() {
  const cli = (document.getElementById('selClienteHistorico') || {}).value || '';
  const ok = r => r && r.ownerTeam === 'Suporte' && r.status !== 'Cancelado' && (!cli || r.clientOrg === cli);
  const criados = {}, fechados = {}, vistosCri = new Set();
  const contaCriado = r => { const k = String(r.protocol || r.id); if (vistosCri.has(k)) return; vistosCri.add(k); const d = hdDia(r.createdDate); if (d) criados[d] = (criados[d] || 0) + 1; };
  Object.keys(RESOLVED_MONTHS).forEach(m => (RESOLVED_MONTHS[m] || []).forEach(r => { if (!ok(r)) return; contaCriado(r); const d = hdDia(r.resolvedIn); if (d) fechados[d] = (fechados[d] || 0) + 1; }));
  TICKETS.forEach(t => { if (ok(t)) contaCriado(t); });
  return {criados, fechados, cli};
}
function hdDias(periodo) {
  const hoje = brasiliaDateStr(NOW), [ay, am, ad] = hoje.split('-').map(Number), out = [];
  const fmt = dt => dt.toISOString().slice(0, 10);
  if (periodo === 'ult30') { for (let i = 29; i >= 0; i--) out.push(fmt(new Date(Date.UTC(ay, am - 1, ad - i)))); return out; }
  const [y, m] = periodo.split('-').map(Number), ultimo = new Date(Date.UTC(y, m, 0)).getUTCDate();
  for (let d = 1; d <= ultimo; d++) { const s = fmt(new Date(Date.UTC(y, m - 1, d))); if (s <= hoje) out.push(s); }
  return out;
}
let hdTipo = 'linhas';
function hdLinhas(info) {
  const W = 920, H = 320, pl = 40, pr = 14, pt = 16, pb = 44, ih = H - pt - pb, iw = W - pl - pr, n = info.length;
  const max = Math.max(4, ...info.map(x => Math.max(x.a, x.f))), passos = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000], passo = passos.find(p => p * 4 >= max) || 1000, teto = passo * 4;   // eixo com marcas redondas
  const X = i => pl + (n === 1 ? iw / 2 : i * iw / (n - 1)), Y = v => pt + ih * (1 - v / teto);
  let g = '';
  info.forEach((x, i) => { if (x.dow === 0 || x.dow === 6) g += `<rect x="${(X(i) - iw / (n - 1) / 2).toFixed(1)}" y="${pt}" width="${(iw / (n - 1)).toFixed(1)}" height="${ih}" style="fill:var(--surface2)" opacity=".7"/>`; });
  for (let k = 0; k <= 4; k++) { const v = teto * k / 4, y = Y(v); g += `<line x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}" stroke="rgba(135,135,153,.22)"/><text class="eixo" x="${pl - 6}" y="${y + 3}" text-anchor="end">${Math.round(v)}</text>`; }
  const pts = k => info.map((x, i) => `${X(i).toFixed(1)},${Y(x[k]).toFixed(1)}`).join(' ');
  g += `<polygon points="${X(0).toFixed(1)},${Y(0)} ${pts('a')} ${X(n - 1).toFixed(1)},${Y(0)}" style="fill:var(--pink)" opacity=".13"/>`;
  g += `<polyline points="${pts('a')}" fill="none" style="stroke:var(--pink)" stroke-width="2.4" stroke-linejoin="round"/><polyline points="${pts('f')}" fill="none" style="stroke:var(--navy)" stroke-width="2.4" stroke-linejoin="round"/>`;
  info.forEach((x, i) => {
    g += `<circle cx="${X(i).toFixed(1)}" cy="${Y(x.a).toFixed(1)}" r="3.4" style="fill:var(--pink)"><title>${x.dd}/${x.m} · abertos: ${x.a}</title></circle><circle cx="${X(i).toFixed(1)}" cy="${Y(x.f).toFixed(1)}" r="3.4" style="fill:var(--navy)"><title>${x.dd}/${x.m} · fechados: ${x.f}</title></circle>`;
    if (n <= 16 || i % 2 === 0 || i === n - 1) g += `<text class="eixo" x="${X(i).toFixed(1)}" y="${H - 24}" text-anchor="middle">${x.dd}</text><text class="eixo" x="${X(i).toFixed(1)}" y="${H - 10}" text-anchor="middle" style="font-weight:600">${x.ini}</text>`;
  });
  return `<div class="hml-leg"><span><i style="background:var(--pink)"></i>Abertos</span><span><i style="background:var(--navy)"></i>Fechados</span><span style="color:var(--text3);">Fins de semana em cinza</span></div><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Chamados abertos e fechados por dia">${g}</svg>`;
}
function hdRender() {
  const box = document.getElementById('hdCorpo'); if (!box) return;
  const sel = document.getElementById('hdPeriodo'), periodo = sel ? sel.value : 'ult30';
  const {criados, fechados} = hdDados(), dias = hdDias(periodo);
  const SEM = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'], INI = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
  const info = dias.map(d => { const [y, m, dd] = d.split('-').map(Number), dow = new Date(Date.UTC(y, m - 1, dd)).getUTCDay(); return {d, dd: String(dd).padStart(2, '0'), m: String(m).padStart(2, '0'), dow, ini: INI[dow], a: criados[d] || 0, f: fechados[d] || 0}; });
  const totA = info.reduce((s, x) => s + x.a, 0), totF = info.reduce((s, x) => s + x.f, 0);
  const uteis = info.filter(x => x.dow !== 0 && x.dow !== 6).length || 1;
  const kpis = `<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));">
    ${gmKpi(totA, 'Abertos no período', '')}${gmKpi(totF, 'Fechados no período', '')}
    ${gmKpi((totA - totF > 0 ? '+' : '') + (totA - totF), 'Saldo (abertos − fechados)', totA - totF > 0 ? 'warn' : '')}
    ${gmKpi((totA / uteis).toFixed(1).replace('.', ','), 'Abertos por dia útil', '')}${gmKpi((totF / uteis).toFixed(1).replace('.', ','), 'Fechados por dia útil', '')}</div>`;
  const grafico = hdTipo === 'barras' && typeof hmlBarras === 'function'
    ? hmlBarras(info.map(x => x.dd), [{nome: 'Abertos', cor: 'var(--pink)', v: info.map(x => x.a)}, {nome: 'Fechados', cor: 'var(--navy)', v: info.map(x => x.f)}], info.map(x => x.ini))
    : hdLinhas(info);
  const linhas = info.slice().reverse().map(x => { const s = x.a - x.f; return `<tr class="${x.dow === 0 || x.dow === 6 ? 'hd-fim' : ''}"><td>${x.dd}/${x.m} <small style="color:var(--text3);">${SEM[x.dow]}</small></td><td class="num">${x.a}</td><td class="num">${x.f}</td><td class="num ${s > 0 ? 'hd-pos' : s < 0 ? 'hd-neg' : ''}">${s > 0 ? '+' : ''}${s}</td></tr>`; }).join('');
  const tg = document.getElementById('hdTipoToggle'); if (tg) tg.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.t === hdTipo));
  box.innerHTML = `${kpis}<div class="hml-graf hd-grafico">${grafico}</div>
    <details class="hd-det"><summary>Ver tabela por dia</summary><div class="hd-tabela"><table><thead><tr><th>Dia</th><th class="num">Abertos</th><th class="num">Fechados</th><th class="num">Saldo</th></tr></thead><tbody>${linhas}
      <tr class="hd-total"><td>Total</td><td class="num">${totA}</td><td class="num">${totF}</td><td class="num">${totA - totF > 0 ? '+' : ''}${totA - totF}</td></tr></tbody></table></div></details>`;
}
function hdMudaTipo(t) { hdTipo = t; hdRender(); }
{
  const sel = document.getElementById('hdPeriodo');
  if (sel) {
    const meses = Object.keys(MONTH_YM).sort((a, b) => Number(a) - Number(b)).map(k => [MONTH_YM[k], MONTH_LABELS[k]]);
    sel.innerHTML = '<option value="ult30">Últimos 30 dias</option>' + meses.map(m => `<option value="${m[0]}">${m[1]}</option>`).join('');
    sel.addEventListener('change', hdRender);
  }
  const cli = document.getElementById('selClienteHistorico'); if (cli) cli.addEventListener('change', hdRender);
  const _s = showTab; showTab = function(name, skip) { _s(name, skip); if (name === 'hist') hdRender(); };
  hdRender();
}
"""


def aplicar_v13(html):
    painel = ('<div class="panel" id="histDiario" style="margin-top: 18px;"><div class="hd-topo"><div><h2>Chamados abertos e fechados por dia</h2>'
              '<div class="panel-sub">Abertos = chamados criados no dia. Fechados = chamados resolvidos no dia. Time Suporte, sem cancelados, e segue o filtro de cliente desta aba. '
              'Saldo positivo significa que a fila cresceu naquele dia.</div></div>'
              '<div style="display:flex; gap:10px; align-items:center;"><span class="seg-toggle" id="hdTipoToggle" role="group" aria-label="Tipo de gráfico"><button type="button" class="active" data-t="linhas" onclick="hdMudaTipo(\'linhas\')">Linhas</button><button type="button" data-t="barras" onclick="hdMudaTipo(\'barras\')">Barras</button></span>'
              '<select id="hdPeriodo" class="itil-select" title="Período" style="max-width:200px; font-size:12px; padding:4px 8px;"></select></div></div>'
              '<div id="hdCorpo"></div></div>\n    ')
    return html.replace('<div class="grid" id="gridHist"', painel + '<div class="grid" id="gridHist"', 1)
