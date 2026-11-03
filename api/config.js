// Entrega a configuracao da automacao e o ultimo relatorio, so' com token valido (senha informada).
const {REPO, tokenValido, tokenDe} = require('./_comum');

async function le(arquivo) {
  const r = await fetch(`https://raw.githubusercontent.com/${REPO}/main/${arquivo}?t=${Date.now()}`);
  if (!r.ok) return {};
  try { return await r.json(); } catch (e) { return {}; }
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (!tokenValido(tokenDe(req))) return res.status(401).json({erro: 'Sessão expirada. Informe a senha novamente.'});
  const [config, relatorio] = await Promise.all([le('config_automacao.json'), le('automacao_relatorio.json')]);
  return res.status(200).json({config, relatorio});
};
