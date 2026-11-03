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
function hdRender() {
  const box = document.getElementById('hdCorpo'); if (!box) return;
  const sel = document.getElementById('hdPeriodo'), periodo = sel ? sel.value : 'ult30';
  const {criados, fechados} = hdDados(), dias = hdDias(periodo);
  const SEM = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'], INI = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
  const info = dias.map(d => { const [y, m, dd] = d.split('-').map(Number), dow = new Date(Date.UTC(y, m - 1, dd)).getUTCDay(); return {d, dd: String(dd).padStart(2, '0'), m: String(m).padStart(2, '0'), dow, a: criados[d] || 0, f: fechados[d] || 0}; });
  const totA = info.reduce((s, x) => s + x.a, 0), totF = info.reduce((s, x) => s + x.f, 0);
  const uteis = info.filter(x => x.dow !== 0 && x.dow !== 6).length || 1;
  const kpis = `<div class="kpi-row" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));">
    ${gmKpi(totA, 'Abertos no período', '')}${gmKpi(totF, 'Fechados no período', '')}
    ${gmKpi((totA - totF > 0 ? '+' : '') + (totA - totF), 'Saldo (abertos − fechados)', totA - totF > 0 ? 'warn' : '')}
    ${gmKpi((totA / uteis).toFixed(1).replace('.', ','), 'Abertos por dia útil', '')}${gmKpi((totF / uteis).toFixed(1).replace('.', ','), 'Fechados por dia útil', '')}</div>`;
  const grafico = typeof hmlBarras === 'function' ? hmlBarras(info.map(x => x.dd), [{nome: 'Abertos', cor: 'var(--pink)', v: info.map(x => x.a)}, {nome: 'Fechados', cor: 'var(--navy)', v: info.map(x => x.f)}], info.map(x => INI[x.dow])) : '';
  const linhas = info.slice().reverse().map(x => { const s = x.a - x.f; return `<tr class="${x.dow === 0 || x.dow === 6 ? 'hd-fim' : ''}"><td>${x.dd}/${x.m} <small style="color:var(--text3);">${SEM[x.dow]}</small></td><td class="num">${x.a}</td><td class="num">${x.f}</td><td class="num ${s > 0 ? 'hd-pos' : s < 0 ? 'hd-neg' : ''}">${s > 0 ? '+' : ''}${s}</td></tr>`; }).join('');
  box.innerHTML = `${kpis}<div class="hml-graf" style="margin-top:14px;">${grafico}</div>
    <div class="hd-tabela"><table><thead><tr><th>Dia</th><th class="num">Abertos</th><th class="num">Fechados</th><th class="num">Saldo</th></tr></thead><tbody>${linhas}
      <tr class="hd-total"><td>Total</td><td class="num">${totA}</td><td class="num">${totF}</td><td class="num">${totA - totF > 0 ? '+' : ''}${totA - totF}</td></tr></tbody></table></div>`;
}
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
              '<select id="hdPeriodo" class="itil-select" title="Período" style="max-width:200px; font-size:12px; padding:4px 8px;"></select></div>'
              '<div id="hdCorpo"></div></div>\n    ')
    return html.replace('<div class="grid" id="gridHist"', painel + '<div class="grid" id="gridHist"', 1)
