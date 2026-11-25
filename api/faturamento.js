// Faturamento detalhado (view faturamento_det_v do banco azure_board), lido direto do banco a cada consulta e guardado so'
// no cache da Vercel: nada vai para o git. Variaveis na Vercel: PG_BOARD_HOST, PG_BOARD_DATABASE, PG_BOARD_USER, PG_BOARD_PASSWORD
// (usuario de leitura). Exige o token da senha de configuracao (mesmo login da aba Configuracao).
// O job do banco recalcula o mes corrente 1x por dia (02:00 BRT) ate ONTEM; "d-1" = ultimo dia fechado em faturamento_exec_controle.
const {Pool} = require('pg');
const {tokenValido, tokenDe} = require('./_comum');

let pool = null;
function getPool() {
  if (!pool) {
    pool = new Pool({
      host: process.env.PG_BOARD_HOST,
      database: process.env.PG_BOARD_DATABASE || 'azure_board',
      user: process.env.PG_BOARD_USER,
      password: process.env.PG_BOARD_PASSWORD,
      port: 5432,
      ssl: {rejectUnauthorized: false},
      max: 2,
      idleTimeoutMillis: 10000,
      connectionTimeoutMillis: 8000,
      statement_timeout: 20000,
    });
    pool.on('error', () => { pool = null; });
  }
  return pool;
}

const SQL_DET = `
  SELECT to_char(f.mes, 'YYYY-MM-DD') AS mes, f.corp, f.nome, f.cnpj_matriz, f.regime_trib, f.usuario,
         f.qtd_cnpj_emi_nfse, f.cnpj, f.municipio, f.uf,
         f.cte_aut, f.cte_can, f.cte_rej, f.cte_sist, f.cte_proc, f.cte_total,
         f.nfse_aut, f.nfse_can, f.nfse_rej, f.nfse_sist, f.nfse_proc, f.nfse_total,
         f.gnre_aut, f.gnre_can, f.gnre_rej, f.gnre_proc, f.gnre_total, f.gnre_pix,
         f.mdfe_aut, f.mdfe_can, f.mdfe_rej, f.mdfe_proc, f.mdfe_total,
         f.ciot_aut, f.ciot_can, f.ciot_rej, f.ciot_proc, f.ciot_total
  FROM faturamento_det_v f
  WHERE f.mes::date = $1::date
  ORDER BY f.nome, f.cnpj`;

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'private, no-store');
  if (req.method !== 'GET') return res.status(405).json({erro: 'Use GET.'});
  if (!tokenValido(tokenDe(req))) return res.status(401).json({erro: 'Sessão expirada. Informe a senha novamente.'});
  if (!process.env.PG_BOARD_HOST || !process.env.PG_BOARD_USER || !process.env.PG_BOARD_PASSWORD) {
    return res.status(503).json({erro: 'As variáveis PG_BOARD_* não estão configuradas na Vercel.'});
  }
  try {
    const db = getPool();
    const ctl = await db.query(`SELECT to_char(dt_fim, 'YYYY-MM-DD') AS dt_fim, status, qtd_ok, qtd_erro, to_char(dt_execucao, 'YYYY-MM-DD"T"HH24:MI:SS') AS dt_execucao
                                FROM faturamento_exec_controle ORDER BY dt_execucao DESC LIMIT 1`);
    const exec = ctl.rows[0] || null;
    const meses = (await db.query(`SELECT DISTINCT to_char(mes::date, 'YYYY-MM') AS mes FROM faturamento_geral ORDER BY 1 DESC LIMIT 24`)).rows.map(r => r.mes);
    let mes = String((req.query && req.query.mes) || '');
    if (!/^\d{4}-\d{2}$/.test(mes)) mes = exec ? exec.dt_fim.slice(0, 7) : (meses[0] || '');
    if (!mes) return res.status(200).json({mes: null, meses, execucao: exec, dados: []});
    const r = await db.query(SQL_DET, [mes + '-01']);
    res.setHeader('Cache-Control', 'private, max-age=300');
    return res.status(200).json({mes, meses, execucao: exec, colunas: r.fields.map(f => f.name), dados: r.rows});
  } catch (e) {
    return res.status(502).json({erro: 'Não foi possível consultar o banco do faturamento (' + (e.code || e.message || 'erro') + ').'});
  }
};
