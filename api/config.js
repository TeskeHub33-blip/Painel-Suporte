// Entrega a configuracao da automacao e o ultimo relatorio (sem senha, a pedido).
const {REPO} = require('./_comum');

async function le(arquivo) {
  const r = await fetch(`https://raw.githubusercontent.com/${REPO}/main/${arquivo}?t=${Date.now()}`);
  if (!r.ok) return {};
  try { return await r.json(); } catch (e) { return {}; }
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  const [config, relatorio, analises] = await Promise.all([le('config_automacao.json'), le('automacao_relatorio.json'), le('analises_horus.json')]);
  return res.status(200).json({config, relatorio, analises});
};
