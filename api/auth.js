// Login por senha (PAINEL_CONFIG_SENHA na Vercel): devolve um token assinado, valido por 8 horas, usado pelas funcoes protegidas.
const {chave, geraToken, iguais} = require('./_comum');

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  if (!chave()) return res.status(503).json({erro: 'PAINEL_CONFIG_SENHA não está configurada na Vercel.'});
  let corpo = {};
  try { corpo = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {}); } catch (e) { corpo = {}; }
  if (!iguais(String(corpo.senha || ''), chave())) {
    await new Promise(r => setTimeout(r, 800));   // freia tentativa em sequencia
    return res.status(401).json({erro: 'Senha incorreta.'});
  }
  return res.status(200).json({token: geraToken()});
};
