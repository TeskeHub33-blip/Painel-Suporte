// "Remover do painel": chamado que NAO e' indisponibilidade geral sai do alerta de indisponibilidade.
// 1) grava uma acao INTERNA no chamado do Movidesk (log) e 2) guarda o protocolo em indisponibilidade_removidos.json
// (branch "config" do GitHub), que o painel le para todo mundo. So' vale depois de 5 minutos da abertura do chamado.
// Variaveis na Vercel: MOVIDESK_TOKEN e GITHUB_TOKEN_CONFIG (token com permissao de escrita em Contents).
const {REPO} = require('./_comum');

const MD = 'https://api.movidesk.com/public/v1';
const GH = `https://api.github.com/repos/${REPO}`;
const ARQUIVO = 'indisponibilidade_removidos.json';
const BRANCH = 'config';
const MIN_MS = 5 * 60 * 1000;
const mascara = t => String(t).replace(/token=[^&\s']+/g, 'token=***');

async function md(metodo, caminho, params, corpo) {
  const q = new URLSearchParams(Object.assign({token: process.env.MOVIDESK_TOKEN}, params));
  const r = await fetch(`${MD}${caminho}?${q}`, {method: metodo, headers: {'Content-Type': 'application/json'}, body: corpo ? JSON.stringify(corpo) : undefined});
  if (!r.ok) throw new Error(`Movidesk respondeu ${r.status}`);
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

async function gh(metodo, caminho, corpo) {
  const r = await fetch(GH + caminho, {
    method: metodo,
    headers: {Accept: 'application/vnd.github+json', 'User-Agent': 'painel-suporte', Authorization: 'Bearer ' + process.env.GITHUB_TOKEN_CONFIG, 'Content-Type': 'application/json'},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const texto = await r.text();
  let json = null;
  try { json = texto ? JSON.parse(texto) : null; } catch (e) { /* ignora */ }
  return {status: r.status, ok: r.ok, json};
}

async function autorId() {
  try {
    const r = await fetch(`https://raw.githubusercontent.com/${REPO}/main/config_automacao.json?t=${Date.now()}`);
    if (r.ok) return String((await r.json()).autor_id || '').trim();
  } catch (e) { /* sem autor: o Movidesk usa o dono do token */ }
  return '';
}

async function garanteBranch() {
  const ref = await gh('GET', `/git/ref/heads/${BRANCH}`);
  if (ref.ok) return null;
  if (ref.status !== 404) return 'GitHub respondeu ' + ref.status + ' (confira a permissão do token).';
  const main = await gh('GET', '/git/ref/heads/main');
  if (!main.ok) return 'Não consegui ler a main do GitHub (' + main.status + ').';
  const novo = await gh('POST', '/git/refs', {ref: `refs/heads/${BRANCH}`, sha: main.json.object.sha});
  return novo.ok ? null : 'Não consegui criar a branch de configuração (' + novo.status + ').';
}

async function guardaRemovido(protocolo, quem) {
  for (let tentativa = 0; tentativa < 3; tentativa++) {
    const atual = await gh('GET', `/contents/${ARQUIVO}?ref=${BRANCH}`);
    let lista = {};
    let sha;
    if (atual.ok && atual.json) {
      sha = atual.json.sha;
      try { lista = JSON.parse(Buffer.from(atual.json.content, 'base64').toString('utf8')).removidos || {}; } catch (e) { lista = {}; }
    }
    const limite = Date.now() - 7 * 24 * 3600 * 1000;
    Object.keys(lista).forEach(k => { if (new Date(lista[k]).getTime() < limite) delete lista[k]; });
    lista[protocolo] = new Date().toISOString();
    const conteudo = JSON.stringify({salvo_em: new Date().toISOString(), removidos: lista}, null, 2) + '\n';
    const put = await gh('PUT', `/contents/${ARQUIVO}`, {message: 'Painel: chamado ' + protocolo + ' fora do alerta de indisponibilidade', content: Buffer.from(conteudo, 'utf8').toString('base64'), branch: BRANCH, sha});
    if (put.ok) return null;
    if (put.status !== 409 && put.status !== 422) return 'Não consegui salvar no GitHub (' + put.status + ').';
  }
  return 'O GitHub está ocupado, tente de novo.';
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  try {
    if (!process.env.MOVIDESK_TOKEN) return res.status(503).json({erro: 'MOVIDESK_TOKEN não configurado na Vercel.'});
    if (!process.env.GITHUB_TOKEN_CONFIG) return res.status(503).json({erro: 'A variável GITHUB_TOKEN_CONFIG não está configurada na Vercel.'});
    const corpo = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const protocolo = String(corpo.protocolo || '').replace(/[^0-9A-Za-z_-]/g, '');
    if (!protocolo) return res.status(400).json({erro: 'Informe o protocolo.'});

    const r = await md('GET', '/tickets', {'$select': 'id,protocol,createdDate,baseStatus', '$filter': `protocol eq '${protocolo}'`, '$top': '1'});
    const t = r && r[0];
    if (!t) return res.status(404).json({erro: 'Chamado não encontrado entre os abertos do Movidesk.'});
    if (Date.now() - new Date(t.createdDate).getTime() < MIN_MS) return res.status(409).json({erro: 'Só dá para remover depois de 5 minutos da abertura do chamado.'});

    const msg = 'Chamado removido do alerta de indisponibilidade do Painel Diário: não se trata de indisponibilidade geral.';
    const nova = {type: 1, description: `<p><strong>[PAINEL]</strong></p><p>${msg}</p>`};
    const id = await autorId();
    if (id) nova.createdBy = {id};
    await md('PATCH', '/tickets', {id: t.id}, {actions: [nova]});

    const erroBranch = await garanteBranch();
    if (erroBranch) return res.status(502).json({erro: 'Log gravado no Movidesk, mas: ' + erroBranch, logGravado: true});
    const erroSalvar = await guardaRemovido(protocolo);
    if (erroSalvar) return res.status(502).json({erro: 'Log gravado no Movidesk, mas: ' + erroSalvar, logGravado: true});
    return res.status(200).json({ok: true, protocolo});
  } catch (e) {
    return res.status(500).json({erro: mascara(e.message || e)});
  }
};
