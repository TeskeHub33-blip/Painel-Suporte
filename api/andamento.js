// Andamento da atualizacao do painel: consulta o GitHub Actions (workflow atualizar.yml).
// Sem GITHUB_TOKEN o GitHub limita a 60 consultas/hora; com um token somente leitura sobe para 5000.
const {REPO} = require('./_comum');

const API = `https://api.github.com/repos/${REPO}/actions`;

async function gh(caminho) {
  const h = {Accept: 'application/vnd.github+json', 'User-Agent': 'painel-suporte'};
  if (process.env.GITHUB_TOKEN) h.Authorization = 'Bearer ' + process.env.GITHUB_TOKEN;
  const r = await fetch(API + caminho, {headers: h});
  if (!r.ok) { const e = new Error('GitHub respondeu ' + r.status); e.status = r.status; throw e; }
  return r.json();
}

const resumo = r => ({id: r.id, numero: r.run_number, status: r.status, conclusao: r.conclusion, inicio: r.run_started_at, atualizado: r.updated_at, evento: r.event, link: r.html_url});

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
  try {
    const dados = await gh('/workflows/atualizar.yml/runs?per_page=8');
    const runs = (dados.workflow_runs || []).map(resumo);
    const emAndamento = runs.find(r => r.status === 'in_progress' || r.status === 'queued' || r.status === 'waiting');
    let etapas = [];
    if (emAndamento) {
      const j = await gh(`/runs/${emAndamento.id}/jobs`);
      const job = (j.jobs || [])[0];
      if (job) etapas = (job.steps || []).map(s => ({nome: s.name, status: s.status, conclusao: s.conclusion, inicio: s.started_at, fim: s.completed_at}));
    }
    let automacao = [], automacaoEtapas = [];
    try {
      const da = await gh('/workflows/automacao_chamados.yml/runs?per_page=3');
      automacao = (da.workflow_runs || []).map(resumo);
      const rodandoA = automacao.find(r => r.status !== 'completed');
      if (rodandoA) {
        const ja = await gh(`/runs/${rodandoA.id}/jobs`);
        const jobA = (ja.jobs || [])[0];
        if (jobA) automacaoEtapas = (jobA.steps || []).map(x => ({nome: x.name, status: x.status, conclusao: x.conclusion, inicio: x.started_at, fim: x.completed_at}));
      }
    } catch (e) { /* sem a automacao nao quebra o andamento */ }
    res.status(200).json({agora: new Date().toISOString(), emAndamento: emAndamento || null, etapas, historico: runs, automacao, automacaoEtapas, comToken: !!process.env.GITHUB_TOKEN});
  } catch (e) {
    res.status(200).json({erro: e.message, limite: e.status === 403 || e.status === 429});
  }
};
