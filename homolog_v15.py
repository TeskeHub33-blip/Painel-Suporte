# -*- coding: utf-8 -*-
"""Aba "Andamento" (ultima aba, depois do Fluxograma): acompanha a atualizacao do painel em tempo real.

So' aparece no endereco da Vercel. Consulta /api/andamento (funcao da Vercel), que le o GitHub Actions
(workflow atualizar.yml): se ha uma execucao em curso, mostra as etapas e o tempo; senao, mostra a ultima e a proxima.
"""

V15_CSS = """
/* ===== Aba Andamento da atualizacao ===== */
#tabAndamento .and-topo { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
#tabAndamento .and-selo { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font: 600 13px inherit; font-family: inherit; background: var(--surface2); color: var(--text); }
#tabAndamento .and-selo i { width: 9px; height: 9px; border-radius: 50%; background: var(--text3); display: inline-block; }
#tabAndamento .and-selo.rodando i { background: var(--pink); animation: andPulso 1.2s ease-in-out infinite; }
#tabAndamento .and-selo.ok i { background: #2e9e6b; }
#tabAndamento .and-selo.erro i { background: var(--danger); }
@keyframes andPulso { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .35; transform: scale(1.5); } }
#tabAndamento .and-barra { height: 10px; border-radius: 999px; background: var(--surface2); overflow: hidden; margin: 14px 0 4px 0; }
#tabAndamento .and-barra > div { height: 100%; background: var(--pink); border-radius: 999px; transition: width .6s ease; }
#tabAndamento .and-etapas { list-style: none; margin: 10px 0 0 0; padding: 0; }
#tabAndamento .and-etapas li { display: flex; align-items: center; gap: 10px; padding: 7px 0; font-size: 13.5px; border-bottom: .5px solid rgba(135,135,153,.25); }
#tabAndamento .and-etapas li .pt { width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--text3); box-sizing: border-box; flex: none; }
#tabAndamento .and-etapas li.feito .pt { background: #2e9e6b; border-color: #2e9e6b; }
#tabAndamento .and-etapas li.atual .pt { border-color: var(--pink); animation: andPulso 1.2s ease-in-out infinite; }
#tabAndamento .and-etapas li.falhou .pt { background: var(--danger); border-color: var(--danger); }
#tabAndamento .and-etapas li .tp { margin-left: auto; color: var(--text3); font-size: 12px; font-variant-numeric: tabular-nums; }
#tabAndamento .and-etapas li.espera { color: var(--text3); }
#tabAndamento table { width: 100%; border-collapse: collapse; margin-top: 8px; }
#tabAndamento .and-nota { font-size: 12px; color: var(--text3); margin-top: 10px; line-height: 1.5; }
"""

V15_JS = r"""
// ===== Aba Andamento da atualizacao =====
const AND_VERCEL = /\.vercel\.app$/.test(location.hostname);
let andTimer = null, andUltimo = null;
function andDur(ms) { if (ms === null || ms === undefined || isNaN(ms)) return '-'; const s = Math.max(0, Math.round(ms / 1000)), m = Math.floor(s / 60); return m ? m + ' min ' + String(s % 60).padStart(2, '0') + ' s' : s + ' s'; }
function andHora(iso) { return iso ? new Date(iso).toLocaleString('pt-BR', {timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'}) : '-'; }
function andProxima(agora) { const d = new Date(agora); d.setUTCSeconds(0, 0); d.setUTCMinutes(Math.floor(d.getUTCMinutes() / 20) * 20 + 20); return d; }
function andSelo(r) {
  if (!r) return '<span class="and-selo"><i></i>Sem informação</span>';
  if (r.status !== 'completed') return '<span class="and-selo rodando"><i></i>' + (r.status === 'queued' ? 'Na fila' : 'Atualizando agora') + '</span>';
  return r.conclusao === 'success' ? '<span class="and-selo ok"><i></i>Concluída</span>' : r.conclusao === 'cancelled' ? '<span class="and-selo"><i></i>Cancelada</span>' : '<span class="and-selo erro"><i></i>Falhou</span>';
}
function andRender(d) {
  const root = document.getElementById('andCorpo'); if (!root) return;
  if (!d || d.erro) {
    root.innerHTML = `<div class="cfg-aviso">${d && d.limite ? 'O GitHub limitou as consultas por alguns minutos. Configure a variável GITHUB_TOKEN na Vercel para remover o limite.' : 'Não foi possível consultar o andamento agora (' + esc((d && d.erro) || 'sem resposta') + '). Tentando de novo.'}</div>`; return;
  }
  const agora = new Date(d.agora).getTime(), rodando = d.emAndamento, ult = d.historico.find(r => r.status === 'completed'), ref = rodando || d.historico[0];
  const etapas = (d.etapas || []).filter(e => !/^(Set up job|Post |Complete job)/.test(e.nome));
  const feitas = etapas.filter(e => e.status === 'completed').length, pct = rodando && etapas.length ? Math.round(feitas * 100 / etapas.length) : (ult ? 100 : 0);
  const dec = rodando ? agora - new Date(rodando.inicio).getTime() : (ult ? new Date(ult.atualizado) - new Date(ult.inicio) : null);
  const lista = etapas.map(e => {
    const cls = e.status === 'completed' ? (e.conclusao === 'failure' ? 'falhou' : 'feito') : e.status === 'in_progress' ? 'atual' : 'espera';
    const t = e.inicio ? andDur((e.fim ? new Date(e.fim).getTime() : agora) - new Date(e.inicio).getTime()) : '';
    return `<li class="${cls}"><span class="pt"></span>${esc(e.nome)}<span class="tp">${t}</span></li>`;
  }).join('');
  const hist = d.historico.map(r => `<tr><td>#${r.numero}</td><td>${andHora(r.inicio)}</td><td>${r.status === 'completed' ? esc({success: 'Concluída', failure: 'Falhou', cancelled: 'Cancelada'}[r.conclusao] || r.conclusao) : 'Em andamento'}</td><td>${r.status === 'completed' ? andDur(new Date(r.atualizado) - new Date(r.inicio)) : andDur(agora - new Date(r.inicio).getTime())}</td><td>${r.evento === 'schedule' ? 'Automática' : 'Manual'}</td></tr>`).join('');
  root.innerHTML = `
    <div class="panel"><div class="and-topo">${andSelo(ref)}
      <span style="font-size:13px; color:var(--text-dim);">${rodando ? 'Rodando há <b>' + andDur(dec) + '</b> · iniciada em ' + andHora(rodando.inicio) : (ult ? 'Última atualização concluída em <b>' + andHora(ult.atualizado) + '</b> (levou ' + andDur(dec) + ')' : '')}</span>
      <span style="margin-left:auto; font-size:12px; color:var(--text3);">Próxima automática: ~${andHora(andProxima(d.agora).toISOString())}</span></div>
      ${rodando ? `<div class="and-barra"><div style="width:${pct}%"></div></div><div class="and-nota">${feitas} de ${etapas.length} etapas · a busca mensal do Movidesk costuma ser a parte mais demorada. Depois de concluir, a Vercel publica em cerca de 1 minuto.</div>` : ''}
      ${lista ? `<ul class="and-etapas">${lista}</ul>` : ''}</div>
    <div class="panel" style="margin-top:18px;"><h2>Últimas execuções</h2><table><thead><tr><th>Nº</th><th>Início</th><th>Resultado</th><th>Duração</th><th>Origem</th></tr></thead><tbody>${hist}</tbody></table>
      <div class="and-nota">Atualiza sozinho a cada 20 segundos enquanto esta aba estiver aberta.${d.comToken ? '' : ' Sem GITHUB_TOKEN na Vercel, o GitHub permite poucas consultas por hora.'}</div></div>`;
}
async function andBusca() {
  try { const r = await fetch('/api/andamento'); andUltimo = await r.json(); } catch (e) { andUltimo = {erro: 'falha de conexão'}; }
  andRender(andUltimo);
}
function andLiga() { andBusca(); if (andTimer) clearInterval(andTimer); andTimer = setInterval(andBusca, 20000); }
function andDesliga() { if (andTimer) { clearInterval(andTimer); andTimer = null; } }
{
  const _s2 = showTab;
  showTab = function(name, skip) {
    _s2(name, skip);
    const p = document.getElementById('tabAndamento'), b = document.getElementById('tabBtnAndamento');
    if (p) p.classList.toggle('active', name === 'andamento'); if (b) b.classList.toggle('active', name === 'andamento');
    if (name === 'andamento') { window._hmlAba = 'andamento'; if (typeof hmlAtualizaBarra === 'function') hmlAtualizaBarra(); andLiga(); } else andDesliga();
  };
  if (AND_VERCEL) { const b = document.getElementById('tabBtnAndamento'); if (b) b.style.display = ''; }
}
"""


def aplicar_v15(html):
    botao = '<button class="tab-btn" id="tabBtnAndamento" style="display:none;" onclick="showTab(\'andamento\')">Andamento</button>'
    painel = ('<div class="tab-panel" id="tabAndamento"><div class="panel-sub" style="margin-bottom:12px;">Acompanhe a atualização do painel em tempo real: '
              'etapas, tempo decorrido e histórico das últimas execuções.</div><div id="andCorpo"><div class="panel-sub">Carregando...</div></div></div>\n\n  ')
    marca = '<button class="tab-btn" id="tabBtnFluxo" onclick="showTab(\'fluxo\')">Fluxograma</button>'
    if marca in html:
        html = html.replace(marca, marca + '\n    ' + botao, 1)
    return html.replace('<div class="tab-panel" id="tabFluxo">', painel + '<div class="tab-panel" id="tabFluxo">', 1)
