// Faturamento mes a mes (jan/2025 em diante), por cliente. Os dados ficam so' no Vercel Blob (armazenamento privado da Vercel):
// nada vai para o git. Variaveis na Vercel: BLOB_READ_WRITE_TOKEN (criada ao criar o Blob Store) e FATURAMENTO_INGEST_TOKEN
// (chave usada so' pela rotina diaria das 09:00 para ENVIAR os dados). Para LER, exige o token da senha de configuracao.
const {put, get} = require('@vercel/blob');
const {tokenValido, tokenDe, iguais} = require('./_comum');

const CAMINHO = 'faturamento/dados.json';
const ORIGEM_ROTINA = 'https://webhook-devops.emiteai.com.br';

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  // A rotina roda dentro da pagina do faturamento do devops, entao o envio e' entre origens diferentes.
  res.setHeader('Access-Control-Allow-Origin', ORIGEM_ROTINA);
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Ingest-Key');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Vary', 'Origin');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (!process.env.BLOB_READ_WRITE_TOKEN) return res.status(503).json({erro: 'O Vercel Blob não está criado neste projeto (falta BLOB_READ_WRITE_TOKEN).'});

  if (req.method === 'POST') {
    const chave = process.env.FATURAMENTO_INGEST_TOKEN;
    if (!chave) return res.status(503).json({erro: 'FATURAMENTO_INGEST_TOKEN não está configurada na Vercel.'});
    if (!iguais(String(req.headers['x-ingest-key'] || ''), chave)) {
      await new Promise(r => setTimeout(r, 800));
      return res.status(401).json({erro: 'Chave de envio inválida.'});
    }
    try {
      const c = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
      if (!Array.isArray(c.dados) || !c.dados.length || !Array.isArray(c.meses)) return res.status(400).json({erro: 'Dados inválidos.'});
      const corpo = JSON.stringify({atualizado_em: new Date().toISOString(), meses: c.meses, dados: c.dados});
      await put(CAMINHO, corpo, {access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true});
      return res.status(200).json({ok: true, meses: c.meses.length, linhas: c.dados.length});
    } catch (e) {
      return res.status(500).json({erro: 'Falha ao salvar: ' + (e.message || e)});
    }
  }

  if (req.method !== 'GET') return res.status(405).json({erro: 'Use GET ou POST.'});
  if (!tokenValido(tokenDe(req))) return res.status(401).json({erro: 'Sessão expirada. Informe a senha novamente.'});
  try {
    const r = await get(CAMINHO, {access: 'private', useCache: false});
    if (!r || r.statusCode !== 200) return res.status(200).json({atualizado_em: null, meses: [], dados: []});
    const texto = await new Response(r.stream).text();
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', 'private, max-age=300');
    return res.status(200).send(texto);
  } catch (e) {
    return res.status(502).json({erro: 'Não foi possível ler os dados do faturamento (' + (e.code || e.message || 'erro') + ').'});
  }
};
