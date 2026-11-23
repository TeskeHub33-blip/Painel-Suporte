// Preenchimento manual dos cartoes de atividade da escala (Ao Vivo). Guarda em escala_manual.json (branch "config" do GitHub);
// o painel le esse arquivo e ele vale sobre a planilha. Variavel na Vercel: GITHUB_TOKEN_CONFIG (Contents: leitura e escrita).
const {REPO} = require('./_comum');

const GH = `https://api.github.com/repos/${REPO}`;
const ARQUIVO = 'escala_manual.json';
const BRANCH = 'config';

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

async function garanteBranch() {
  const ref = await gh('GET', `/git/ref/heads/${BRANCH}`);
  if (ref.ok) return null;
  if (ref.status !== 404) return 'GitHub respondeu ' + ref.status + ' (confira a permissão do token).';
  const main = await gh('GET', '/git/ref/heads/main');
  if (!main.ok) return 'Não consegui ler a main do GitHub (' + main.status + ').';
  const novo = await gh('POST', '/git/refs', {ref: `refs/heads/${BRANCH}`, sha: main.json.object.sha});
  return novo.ok ? null : 'Não consegui criar a branch de configuração (' + novo.status + ').';
}

const nome = x => String(x || '').replace(/[|]/g, ' ').trim().slice(0, 60);

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  try {
    if (!process.env.GITHUB_TOKEN_CONFIG) return res.status(503).json({erro: 'GITHUB_TOKEN_CONFIG não está configurada na Vercel.'});
    const c = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const data = String(c.data || '');
    const de = Number(c.de), ate = Number(c.ate), ai = Number(c.atividade);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(data)) return res.status(400).json({erro: 'Data inválida.'});
    if (![de, ate, ai].every(Number.isInteger) || de < 0 || ate > 23 || de > ate || ai < 0 || ai > 7) return res.status(400).json({erro: 'Hora ou atividade inválida.'});
    const limpar = c.nomes === null;
    let valor = '';
    if (!limpar) {
      const n = (Array.isArray(c.nomes) ? c.nomes : []).slice(0, 3).map(nome);
      while (n.length < 3) n.push('');
      if (!n[0] && (n[1] || n[2])) return res.status(400).json({erro: 'Preencha o Principal antes do 2º e do 3º.'});
      valor = n.join('|');
    }
    const hoje = Date.now();
    const dentro = Math.abs(new Date(data + 'T12:00:00Z').getTime() - hoje) <= 3 * 24 * 3600 * 1000;
    if (!dentro) return res.status(400).json({erro: 'Só dá para preencher datas próximas de hoje.'});

    const erroBranch = await garanteBranch();
    if (erroBranch) return res.status(502).json({erro: erroBranch});
    for (let tentativa = 0; tentativa < 3; tentativa++) {
      const atual = await gh('GET', `/contents/${ARQUIVO}?ref=${BRANCH}`);
      let manual = {};
      let sha;
      if (atual.ok && atual.json) {
        sha = atual.json.sha;
        try { manual = JSON.parse(Buffer.from(atual.json.content, 'base64').toString('utf8')).manual || {}; } catch (e) { manual = {}; }
      }
      const limite = new Date(hoje - 14 * 24 * 3600 * 1000).toISOString().slice(0, 10);
      Object.keys(manual).forEach(d => { if (d < limite) delete manual[d]; });
      manual[data] = manual[data] || {};
      for (let h = de; h <= ate; h++) {
        manual[data][h] = manual[data][h] || {};
        if (limpar) delete manual[data][h][ai]; else manual[data][h][ai] = valor;
        if (!Object.keys(manual[data][h]).length) delete manual[data][h];
      }
      if (!Object.keys(manual[data]).length) delete manual[data];
      const salvoEm = new Date().toISOString();
      const conteudo = JSON.stringify({salvo_em: salvoEm, manual}, null, 2) + '\n';
      const put = await gh('PUT', `/contents/${ARQUIVO}`, {message: 'Painel: escala manual ' + data, content: Buffer.from(conteudo, 'utf8').toString('base64'), branch: BRANCH, sha});
      if (put.ok) return res.status(200).json({ok: true, salvo_em: salvoEm});
      if (put.status !== 409 && put.status !== 422) return res.status(502).json({erro: 'Não consegui salvar no GitHub (' + put.status + ').'});
    }
    return res.status(502).json({erro: 'O GitHub está ocupado, tente de novo.'});
  } catch (e) {
    return res.status(500).json({erro: 'Falha ao salvar: ' + (e.message || e)});
  }
};
