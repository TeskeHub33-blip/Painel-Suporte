// Utilitarios das funcoes da Vercel (o prefixo _ impede que vire rota).
const crypto = require('crypto');

const REPO = 'TeskeHub33-blip/Painel-Suporte';
const VALIDADE_MS = 8 * 60 * 60 * 1000;

function chave() {
  return process.env.PAINEL_CONFIG_SENHA || '';
}

function assina(exp) {
  return crypto.createHmac('sha256', 'painel-config:' + chave()).update(String(exp)).digest('hex');
}

function geraToken() {
  const exp = Date.now() + VALIDADE_MS;
  return exp + '.' + assina(exp);
}

function iguais(a, b) {
  const x = Buffer.from(String(a)), y = Buffer.from(String(b));
  return x.length === y.length && crypto.timingSafeEqual(x, y);
}

function tokenValido(token) {
  if (!chave() || !token) return false;
  const [exp, sig] = String(token).split('.');
  if (!exp || !sig || Number(exp) < Date.now()) return false;
  return iguais(sig, assina(exp));
}

function tokenDe(req) {
  const h = req.headers['authorization'] || '';
  return h.startsWith('Bearer ') ? h.slice(7) : '';
}

module.exports = {REPO, chave, geraToken, iguais, tokenValido, tokenDe};
