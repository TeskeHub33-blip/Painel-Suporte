// Valida a senha da aba Configuracao. A senha fica na variavel de ambiente PAINEL_CONFIG_SENHA (Vercel),
// nunca no codigo nem na pagina. Devolve um token assinado que vale por 8 horas.
const {chave, geraToken, iguais} = require('./_comum');

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  if (!chave()) return res.status(503).json({erro: 'Senha não configurada na Vercel (variável PAINEL_CONFIG_SENHA).'});
  const senha = (req.body && req.body.senha) || '';
  if (!iguais(senha, chave())) {
    await new Promise(r => setTimeout(r, 800));
    return res.status(401).json({erro: 'Senha incorreta.'});
  }
  return res.status(200).json({ok: true, token: geraToken()});
};
