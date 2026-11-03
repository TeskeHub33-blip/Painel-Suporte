# -*- coding: utf-8 -*-
"""Aba "Configuração": automacao de log interno nos chamados (comeca DESABILITADA, so' atua nos chamados informados).

O painel e' uma pagina estatica: ele NAO escreve no Movidesk e nao guarda chave nenhuma. A aba serve para
  1) informar os chamados autorizados e validar se existem,
  2) definir os parametros (habilitar, modo, busca automatica, modelo do log),
  3) pre-visualizar o log que seria gravado (com os dados do painel),
  4) gerar o config_automacao.json para colar no GitHub e, depois, rodar o workflow manualmente.
Quem grava no Movidesk e' o workflow 'Automação de chamados (log interno)' (automacao_chamados.py), que usa o segredo
MOVIDESK_TOKEN do GitHub.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

V14_CSS = """
/* ===== Aba Configuracao (automacao de chamados) ===== */
#tabConfig .cfg-aviso { background: var(--warn-dim); color: var(--text); border-radius: 6px; padding: 12px 16px; font-size: 13px; line-height: 1.5; margin: 0 0 16px 0; }
#tabConfig .cfg-aviso.ok { background: var(--ok-dim); }
#tabConfig .cfg-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px 24px; margin-top: 10px; }
#tabConfig label.cfg-c { display: block; font-size: 12px; color: var(--text3); }
#tabConfig label.cfg-c > span { display: block; margin-bottom: 4px; }
#tabConfig input[type=text], #tabConfig input[type=number], #tabConfig select, #tabConfig textarea { width: 100%; box-sizing: border-box; font: 400 14px inherit; font-family: inherit; padding: 9px 12px; color: var(--text); background: var(--panel); border: .625px solid rgba(135,135,153,.7); border-radius: 6px; outline: none; }
#tabConfig textarea { min-height: 96px; resize: vertical; line-height: 1.45; }
#tabConfig input:focus, #tabConfig select:focus, #tabConfig textarea:focus { border: 1.5px solid var(--navy); padding: 8.4px 11.4px; }
#tabConfig .cfg-chave { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text); cursor: pointer; }
#tabConfig .cfg-chave input { width: 18px; height: 18px; accent-color: var(--pink); }
#tabConfig .cfg-acoes { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
#tabConfig .cfg-btn { padding: 8px 18px; border-radius: 6px; border: 1.25px solid #878799; background: transparent; color: var(--navy); font: 600 13px inherit; font-family: inherit; cursor: pointer; text-decoration: none; display: inline-block; }
#tabConfig .cfg-btn:hover { background: rgba(36,36,62,.05); border-color: var(--navy); }
#tabConfig .cfg-log { white-space: pre-wrap; font: 12.5px/1.55 ui-monospace, Consolas, monospace; background: var(--surface2); border-radius: 6px; padding: 12px 14px; margin: 8px 0 0 0; color: var(--text); }
#tabConfig table { width: 100%; border-collapse: collapse; margin-top: 8px; }
#tabConfig .cfg-passos { margin: 8px 0 0 18px; padding: 0; font-size: 13px; line-height: 1.7; color: var(--text-dim); }
"""

V14_JS = r"""
// ===== Aba Configuracao: automacao de chamados =====
const CFG_REPO = 'TeskeHub33-blip/Painel-Suporte';
function cfgLeJson(id, padrao) { try { return JSON.parse(document.getElementById(id).textContent); } catch (e) { return padrao; } }
let AUTO_CFG = {}, AUTO_REL = {}, CFG_PADRAO_LOG = '';
const CFG_VERCEL = /\.vercel\.app$/.test(location.hostname);
function cfgRascunho() { try { return JSON.parse(localStorage.getItem('cfgAutomacaoRascunho') || 'null'); } catch (e) { return null; } }
function cfgSalvaRascunho(o) { try { localStorage.setItem('cfgAutomacaoRascunho', JSON.stringify(o)); } catch (e) {} }
function cfgToken() { try { return sessionStorage.getItem('cfgToken') || ''; } catch (e) { return ''; } }
function cfgGuardaToken(t) { try { if (t) sessionStorage.setItem('cfgToken', t); else sessionStorage.removeItem('cfgToken'); } catch (e) {} }
async function cfgCarrega() {
  try {
    const r = await fetch('/api/config', {headers: {Authorization: 'Bearer ' + cfgToken()}});
    if (!r.ok) { cfgGuardaToken(''); return false; }
    const d = await r.json(); AUTO_CFG = d.config || {}; AUTO_REL = d.relatorio || {}; CFG_PADRAO_LOG = AUTO_CFG.modelo_log || CFG_PADRAO_LOG; return true;
  } catch (e) { return false; }
}
function cfgTelaSenha(msg) {
  const root = document.getElementById('cfgCorpo'); if (!root) return;
  root.innerHTML = `<div class="panel" style="max-width:380px; margin:30px auto; text-align:center;"><h2>Configuração protegida</h2>
    <div class="panel-sub" style="margin-bottom:14px;">Informe a senha para abrir a configuração da automação.</div>
    <input id="cfgSenha" type="password" class="itil-select" style="width:100%; text-align:center; margin-bottom:10px;" placeholder="Senha" autocomplete="current-password" onkeydown="if(event.key==='Enter')cfgEntrar()">
    <div class="cfg-acoes" style="justify-content:center;"><button type="button" class="cfg-btn" onclick="cfgEntrar()">Entrar</button></div>
    <div id="cfgSenhaErro" style="color:var(--danger); font-size:12px; margin-top:10px; min-height:16px;">${msg ? esc(msg) : ''}</div></div>`;
  const i = document.getElementById('cfgSenha'); if (i) i.focus();
}
async function cfgEntrar() {
  const i = document.getElementById('cfgSenha'), er = document.getElementById('cfgSenhaErro'); if (!i) return;
  er.textContent = 'Verificando...';
  try {
    const r = await fetch('/api/auth', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({senha: i.value})});
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { er.textContent = d.erro || 'Não foi possível validar a senha.'; i.value = ''; return; }
    cfgGuardaToken(d.token);
    cfgGate();
  } catch (e) { er.textContent = 'Falha de conexão com o servidor.'; }
}
function cfgSair() { cfgGuardaToken(''); AUTO_CFG = {}; AUTO_REL = {}; cfgTelaSenha(''); }
async function cfgGate() {
  const root = document.getElementById('cfgCorpo'); if (!root) return;
  if (!CFG_VERCEL) { root.innerHTML = '<div class="cfg-aviso">A configuração só está disponível no endereço do painel na Vercel.</div>'; return; }
  if (cfgToken() && await cfgCarrega()) { cfgRender(); root.insertAdjacentHTML('afterbegin', '<div class="cfg-acoes" style="justify-content:flex-end; margin:0 0 8px 0;"><button type="button" class="cfg-btn" onclick="cfgSair()">Sair da configuração</button></div>'); return; }
  cfgTelaSenha('');
}
function cfgForm() {
  const v = id => { const e = document.getElementById(id); return e ? e.value : ''; }, c = id => { const e = document.getElementById(id); return !!(e && e.checked); };
  const protocolos = Array.from(new Set((v('cfgProtocolos').match(/\d{6,}/g) || [])));
  return {habilitada: c('cfgHabilitada'), modo: v('cfgModo') || 'simulacao', protocolos_autorizados: protocolos, autor_id: v('cfgAutor').trim(), tipo_acao: Number(v('cfgTipo') || 2),
    busca_automatica: {habilitada: false, status: v('cfgStatus').trim() || 'Novo', limite_por_execucao: Math.max(1, Math.min(50, Number(v('cfgLimite') || 5)))},
    modelo_log: v('cfgModelo') || CFG_PADRAO_LOG, observacao: 'Começa desabilitada. Só atua em chamados listados em protocolos_autorizados. Em modo simulacao nada é gravado no Movidesk.'};
}
function cfgEtapa(t) {
  const tg = t.tags || [], tem = p => tg.some(x => (x || '').toLowerCase().indexOf(p) !== -1), tec = tem('estimativa t'), com = tem('estimativa c'), apr = tem('aprovado'), st = t.status || '';
  if (t.category === 'Melhoria') {
    if (st === 'Refinamento Suporte Melhoria') return apr ? 'Aprovado pelo produto, task a abrir' : tec ? 'Aguardando estimativa técnica' : 'Aguardando reunião de alinhamento';
    if (st === 'Em atendimento - CS' && tec && com) return 'Aguardando orçamento';
    if (st === 'Aguardando Cliente') return com ? 'Aguardando assinatura do cliente' : tec ? 'Aguardando aprovação comercial' : 'Pendente usuário';
    if (st === 'Aguardando Desenvolvimento' && (apr || com)) return t.slaSolutionDate ? 'Entrega agendada' : 'Aguardando previsão de entrega';
  }
  return {'Novo': 'Fila inicial, aguardando o N1', 'Em atendimento': 'N1', 'Em atendimento - N2': 'N2', 'Aguardando Cliente': 'Pendente usuário', 'Aguardando Desenvolvimento': 'Task no desenvolvimento', 'Resolvido': 'Validação do cliente', 'Fechado': 'Encerrado', 'Cancelado': 'Encerrado'}[st] || st || 'não informado';
}
const CFG_PROXIMO = {'Novo': 'O N1 deve iniciar a análise; o N3 pode apoiar se for preciso.', 'Em atendimento': 'O N1 pode resolver, colocar em Pendente usuário (falta informação) ou repassar para Em atendimento - N2.',
  'Em atendimento - N2': 'O N2 pode resolver e devolver ao N1, ou abrir task para o desenvolvimento.', 'Aguardando Cliente': 'Aguardar o cliente; se responder, volta ao N1. Sem resposta, fecha sozinho em 3 dias corridos.',
  'Aguardando Desenvolvimento': 'A task está com o desenvolvimento; acompanhar o log do Azure DevOps (validação ou impedimento).', 'Resolvido': 'Aguardar a confirmação do cliente; sem resposta, fecha sozinho em 3 dias corridos.',
  'Refinamento Suporte Melhoria': 'Aguardar a reunião de alinhamento com o Produto (quarta, 14:00) e a decisão: roadmap ou cobrada.'};
function cfgFmt(h) { return h === null || h === undefined ? 'não informado' : h < 24 ? h.toFixed(1) + ' h' : (h / 24).toFixed(1) + ' dias'; }
function cfgCampos(t) {
  const achados = [], h = t._hoursSinceUpdate;
  if (h !== null && h !== undefined && h >= 48 && ['Em atendimento', 'Em atendimento - N2', 'Aguardando Terceiros'].indexOf(t.status) !== -1) achados.push('Aging: ' + cfgFmt(h) + ' sem atualização');
  let sla = 'sem SLA definido';
  if (t._sla) { const hh = (t._sla - NOW) / 36e5; sla = (hh < 0 ? 'venceu há ' + cfgFmt(-hh) : 'vence em ' + cfgFmt(hh)) + ' (' + hmlDt(t.slaSolutionDate) + ')'; if (hh < 0) achados.push('SLA vencido'); }
  if (t.category === 'Bug' && (t.urgency === 'Alta' || t.urgency === 'Média')) achados.push('Bug de urgência ' + t.urgency + ': conferir o prazo de repasse ao N2');
  if (t.category === 'Melhoria' && !(t.tags || []).length && t.status === 'Refinamento Suporte Melhoria') achados.push('Melhoria sem tag: entra na pauta da reunião de alinhamento');
  return {protocolo: t.protocol, categoria: t.category || 'Sem categoria', urgencia: t.urgency || 'não informada', status: t.status || '-', etapa: cfgEtapa(t), parado: cfgFmt(h), sla: sla,
    analise: achados.length ? achados.join('; ') : 'Nenhum alerta pelas regras automáticas.', proximo_passo: CFG_PROXIMO[t.status] || 'Seguir o fluxo de atendimento conforme o status.', data_hora: hmlDt(new Date().toISOString())};
}
function cfgMontaLog(modelo, campos) { let s = modelo || ''; Object.keys(campos).forEach(k => { s = s.split('{' + k + '}').join(campos[k]); }); return s; }
function cfgEsc(s) { return esc(s); }

function cfgRender() {
  const root = document.getElementById('cfgCorpo'); if (!root) return;
  const base = Object.assign({}, AUTO_CFG, cfgRascunho() || {}), b = base.busca_automatica || {};
  const repoHab = !!AUTO_CFG.habilitada, rel = AUTO_REL || {};
  root.innerHTML = `
    <div class="cfg-aviso ${repoHab ? '' : 'ok'}"><b>Estado atual no repositório:</b> automação <b>${repoHab ? 'HABILITADA' : 'desabilitada'}</b>, modo <b>${esc(AUTO_CFG.modo || 'simulacao')}</b>, ${(AUTO_CFG.protocolos_autorizados || []).length} chamado(s) autorizado(s).
      Esta página <b>não grava nada no Movidesk</b>: ela monta a configuração. Quem executa é o workflow do GitHub, e só quando você o dispara.</div>

    <div class="panel"><h2>1. Chamados autorizados</h2>
      <div class="panel-sub">A automação só atua nos chamados informados aqui. Digite ou cole os protocolos (separados por vírgula, espaço ou linha).</div>
      <textarea id="cfgProtocolos" placeholder="Ex.: 202610001540, 202610001541">${esc((base.protocolos_autorizados || []).join('\n'))}</textarea>
      <div class="cfg-acoes"><button type="button" class="cfg-btn" onclick="cfgValida()">Validar no painel</button><button type="button" class="cfg-btn" onclick="cfgPrevia()">Pré-visualizar o log</button></div>
      <div id="cfgValida"></div></div>

    <div class="panel" style="margin-top:18px;"><h2>2. Parâmetros</h2>
      <div class="panel-sub">Tudo começa desligado. Para gravar de verdade são necessárias três condições juntas: habilitada, modo gravar e a confirmação ao disparar o workflow.</div>
      <div class="cfg-grid">
        <label class="cfg-chave"><input type="checkbox" id="cfgHabilitada" ${base.habilitada ? 'checked' : ''}> Habilitar a automação</label>
        <label class="cfg-c"><span>Modo</span><select id="cfgModo"><option value="simulacao" ${base.modo !== 'gravar' ? 'selected' : ''}>Simulação (lê e monta o log, não grava)</option><option value="gravar" ${base.modo === 'gravar' ? 'selected' : ''}>Gravar nota no chamado</option></select></label>
        <label class="cfg-c"><span>Tipo da ação no Movidesk</span><select id="cfgTipo"><option value="2" ${Number(base.tipo_acao) !== 1 ? 'selected' : ''}>2 · nota interna (esperado)</option><option value="1" ${Number(base.tipo_acao) === 1 ? 'selected' : ''}>1 · resposta pública (ATENÇÃO: o cliente vê)</option></select></label>
        <label class="cfg-c"><span>Id do agente autor (createdBy.id no Movidesk)</span><input type="text" id="cfgAutor" value="${esc(base.autor_id || '')}" placeholder="obrigatório para gravar"></label>
        <label class="cfg-chave" style="opacity:.55;"><input type="checkbox" id="cfgBusca" disabled> Busca automática (desativada por enquanto)</label>
        <label class="cfg-c"><span>Status procurado</span><input type="text" id="cfgStatus" value="${esc(b.status || 'Novo')}"></label>
        <label class="cfg-c"><span>Limite por execução</span><input type="number" id="cfgLimite" min="1" max="50" value="${esc(b.limite_por_execucao || 5)}"></label>
      </div></div>

    <div class="panel" style="margin-top:18px;"><h2>3. Modelo do log</h2>
      <div class="panel-sub">Campos disponíveis: {data_hora} {protocolo} {categoria} {urgencia} {status} {etapa} {parado} {sla} {analise} {proximo_passo}</div>
      <textarea id="cfgModelo" style="min-height:170px;">${esc(base.modelo_log || CFG_PADRAO_LOG)}</textarea>
      <div class="cfg-acoes"><button type="button" class="cfg-btn" onclick="document.getElementById('cfgModelo').value = CFG_PADRAO_LOG">Restaurar o modelo padrão</button></div>
      <div id="cfgPrevia"></div></div>

    <div class="panel" style="margin-top:18px;"><h2>4. Aplicar a configuração</h2>
      <div class="panel-sub">O painel não pode salvar no repositório. Gere o arquivo, cole no GitHub e dispare o workflow.</div>
      <div class="cfg-acoes"><button type="button" class="cfg-btn" onclick="cfgGera()">Gerar configuração</button></div>
      <textarea id="cfgJson" readonly style="min-height:200px; margin-top:10px; font-family:ui-monospace,Consolas,monospace; font-size:12.5px;" placeholder="Clique em Gerar configuração"></textarea>
      <div class="cfg-acoes"><button type="button" class="cfg-btn" onclick="cfgCopia()">Copiar</button>
        <a class="cfg-btn" target="_blank" rel="noopener" href="https://github.com/${CFG_REPO}/edit/main/config_automacao.json">Editar o arquivo no GitHub</a>
        <a class="cfg-btn" target="_blank" rel="noopener" href="https://github.com/${CFG_REPO}/actions/workflows/automacao_chamados.yml">Abrir o workflow</a></div>
      <ol class="cfg-passos"><li>Clique em Gerar configuração e depois em Copiar.</li><li>Em Editar o arquivo no GitHub, apague o conteúdo, cole e salve (commit).</li>
        <li>Em Abrir o workflow, clique em Run workflow. Deixe <b>gravar desligado</b> para só simular. Ligue só quando o modo e o autor estiverem certos.</li>
        <li>Depois da execução, o relatório aparece abaixo na próxima atualização do painel.</li></ol></div>

    <div class="panel" style="margin-top:18px;"><h2>Últimas execuções da automação</h2>
      ${(rel.historico || []).length ? `<table><thead><tr><th>Quando</th><th>Modo</th><th>Chamados buscados</th></tr></thead><tbody>${rel.historico.map(h => `<tr><td>${esc(h.executado_em || '-')}</td><td>${h.habilitada ? esc(h.modo || '-') : 'desabilitada'}</td><td>${(h.chamados || []).length ? h.chamados.map(c => esc(c.protocolo) + ' <small style="color:var(--text3);">(' + esc(c.resultado || '-') + ')</small>').join(', ') : 'nenhum'}</td></tr>`).join('')}</tbody></table>` : '<div class="panel-sub">Ainda não houve execução.</div>'}</div>
    <div class="panel" style="margin-top:18px;"><h2>Último relatório da automação</h2>
      ${rel.executado_em ? `<div class="panel-sub">Executado em ${esc(rel.executado_em)} · automação ${rel.habilitada ? 'habilitada' : 'desabilitada'} · modo ${esc(rel.modo || '-')}</div>
        ${(rel.avisos || []).map(a => `<div class="cfg-aviso">${esc(a)}</div>`).join('')}
        ${(rel.resultados || []).length ? `<table><thead><tr><th>Chamado</th><th>Resultado</th><th>Detalhe</th></tr></thead><tbody>${rel.resultados.map(r => `<tr><td>${esc(r.protocolo)}</td><td>${esc(r.resultado)}</td><td>${esc(r.erro || r.conferencia || r.assunto || '')}</td></tr>`).join('')}</tbody></table>` : ''}
        ${(rel.candidatos_novos || []).length ? `<div class="panel-sub" style="margin-top:10px;">Candidatos encontrados pela busca automática (nada foi gravado neles):</div><table><tbody>${rel.candidatos_novos.map(c => `<tr><td>${esc(c.protocolo)}</td><td>${esc(c.assunto || '')}</td><td>${esc(c.categoria || '')}</td></tr>`).join('')}</tbody></table>` : ''}`
        : '<div class="panel-sub">Ainda não houve execução.</div>'}</div>`;
  root.querySelectorAll('input, select, textarea').forEach(e => e.addEventListener('change', () => cfgSalvaRascunho(cfgForm())));
}
function cfgAchados() {
  const protos = cfgForm().protocolos_autorizados;
  return protos.map(p => ({p, t: findTicketByProtocol(p)}));
}
function cfgValida() {
  const lista = cfgAchados(), box = document.getElementById('cfgValida');
  if (!lista.length) { box.innerHTML = '<div class="cfg-aviso" style="margin-top:10px;">Nenhum protocolo informado.</div>'; return; }
  box.innerHTML = `<table><thead><tr><th>Protocolo</th><th>No painel?</th><th>Status</th><th>Categoria</th><th>Cliente</th></tr></thead><tbody>${lista.map(({p, t}) => t
    ? `<tr><td>${ticketLink(t.id, t.protocol)}</td><td>sim</td><td>${esc(t.status || '')}</td><td>${esc(t.category || '')}</td><td>${esc(t.clientOrg || '–')}</td></tr>`
    : `<tr><td>${esc(p)}</td><td>não encontrado</td><td colspan="3" style="color:var(--text3);">O painel só tem chamados abertos e os resolvidos dos meses carregados. A automação consulta o Movidesk direto, então ainda pode achar.</td></tr>`).join('')}</tbody></table>`;
}
function cfgPrevia() {
  const modelo = document.getElementById('cfgModelo').value, lista = cfgAchados().filter(x => x.t), box = document.getElementById('cfgPrevia');
  box.innerHTML = lista.length ? lista.map(({t}) => `<div class="panel-sub" style="margin-top:12px;">${esc(t.protocol)} · ${esc((t.subject || '').slice(0, 70))}</div><div class="cfg-log">${esc(cfgMontaLog(modelo, cfgCampos(t)))}</div>`).join('') + '<div class="panel-sub" style="margin-top:8px;">Pré-visualização com os dados do painel. O texto gravado pela automação é montado pelo workflow, com os dados do Movidesk no momento da execução.</div>'
    : '<div class="cfg-aviso" style="margin-top:10px;">Nenhum dos protocolos informados está no painel para pré-visualizar.</div>';
}
function cfgGera() { document.getElementById('cfgJson').value = JSON.stringify(cfgForm(), null, 2); }
function cfgCopia() {
  const ta = document.getElementById('cfgJson'); if (!ta.value) cfgGera();
  const ok = () => { ta.select(); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).catch(ok); else ok();
}
{
  const _s = showTab;
  showTab = function(name, skip) {
    _s(name, skip);
    const p = document.getElementById('tabConfig'), b = document.getElementById('tabBtnConfig');
    if (p) p.classList.toggle('active', name === 'config'); if (b) b.classList.toggle('active', name === 'config');
    if (name === 'config') { window._hmlAba = 'config'; if (typeof hmlAtualizaBarra === 'function') hmlAtualizaBarra(); cfgGate(); }
  };
  if (CFG_VERCEL) { const b = document.getElementById('tabBtnConfig'); if (b) b.style.display = ''; }
}
"""


def _json(nome, padrao):
    try:
        with open(os.path.join(BASE, nome), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return padrao


def aplicar_v14(html):
    dados = ''  # a configuracao NAO vai mais dentro da pagina: so /api/config entrega, com senha
    painel = ('<div class="tab-panel" id="tabConfig"><div class="panel-sub" style="margin-bottom:12px;">Acompanhe a atualização do painel e configure a automação de log nos chamados. '
              'A automação começa desabilitada e só atua nos chamados que você informar.</div><div id="cfgCorpo"></div></div>\n\n  ')
    botao = '<button class="tab-btn" id="tabBtnConfig" style="display:none;" onclick="showTab(\'config\')">Configuração e andamento</button>\n    '
    marca = '<button class="tab-btn" id="tabBtnFluxo" onclick="showTab(\'fluxo\')">Fluxograma</button>'
    html = html.replace(marca, marca + '\n    ' + botao.strip(), 1)
    return html.replace('<div class="tab-panel" id="tabFluxo">', dados + painel + '<div class="tab-panel" id="tabFluxo">', 1)
