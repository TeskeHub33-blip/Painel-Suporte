// Salva a lista de clientes TMS Admin (e as partes do painel de onde eles saem) no GitHub:
// branch "config", arquivo painel_config.json. Exige o token da sessao de configuracao (senha) e a variavel de
// ambiente GITHUB_TOKEN_CONFIG na Vercel (token com permissao de escrita em "Contents" deste repositorio).
const {REPO, tokenValido, tokenDe} = require('./_comum');

const API = `https://api.github.com/repos/${REPO}`;
const ARQUIVO = 'painel_config.json';
const BRANCH = 'config';

async function gh(metodo, caminho, corpo) {
  const r = await fetch(API + caminho, {
    method: metodo,
    headers: {Accept: 'application/vnd.github+json', 'User-Agent': 'painel-suporte', Authorization: 'Bearer ' + process.env.GITHUB_TOKEN_CONFIG, 'Content-Type': 'application/json'},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const texto = await r.text();
  let json = null;
  try { json = texto ? JSON.parse(texto) : null; } catch (e) { /* ignora */ }
  return {status: r.status, ok: r.ok, json};
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  if (!tokenValido(tokenDe(req))) return res.status(401).json({erro: 'Sessão expirada. Entre de novo com a senha.'});
  if (!process.env.GITHUB_TOKEN_CONFIG) return res.status(500).json({erro: 'A variável GITHUB_TOKEN_CONFIG não está configurada na Vercel.'});

  const corpo = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const lista = Array.isArray(corpo.clientes) ? corpo.clientes : [];
  const clientes = Array.from(new Set(lista.map(c => String(c || '').trim()).filter(c => c && c.length <= 120))).slice(0, 200);
  const excluir = {abertos: !(corpo.excluir && corpo.excluir.abertos === false), historico: !(corpo.excluir && corpo.excluir.historico === false)};
  const salvoEm = new Date().toISOString();
  const conteudo = JSON.stringify({salvo_em: salvoEm, tms_admin: {clientes, excluir}}, null, 2) + '\n';

  try {
    // garante a branch "config" (criada a partir da main na primeira vez)
    const ref = await gh('GET', `/git/ref/heads/${BRANCH}`);
    if (ref.status === 404) {
      const main = await gh('GET', '/git/ref/heads/main');
      if (!main.ok) return res.status(502).json({erro: 'Não consegui ler a main do GitHub (' + main.status + ').'});
      const novo = await gh('POST', '/git/refs', {ref: `refs/heads/${BRANCH}`, sha: main.json.object.sha});
      if (!novo.ok) return res.status(502).json({erro: 'Não consegui criar a branch de configuração (' + novo.status + ').'});
    } else if (!ref.ok) {
      return res.status(502).json({erro: 'GitHub respondeu ' + ref.status + ' (confira a permissão do token).'});
    }
    const atual = await gh('GET', `/contents/${ARQUIVO}?ref=${BRANCH}`);
    const sha = atual.ok && atual.json ? atual.json.sha : undefined;
    const put = await gh('PUT', `/contents/${ARQUIVO}`, {
      message: 'Painel: configuração TMS Admin (' + clientes.length + ' cliente(s))', content: Buffer.from(conteudo, 'utf8').toString('base64'), branch: BRANCH, sha,
    });
    if (!put.ok) return res.status(502).json({erro: 'Não consegui salvar no GitHub (' + put.status + ').'});
    return res.status(200).json({ok: true, salvo_em: salvoEm, clientes: clientes.length});
  } catch (e) {
    return res.status(500).json({erro: 'Falha ao salvar: ' + e.message});
  }
};
