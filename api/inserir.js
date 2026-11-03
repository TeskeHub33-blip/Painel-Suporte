// Insere o log analisado como acao no chamado do Movidesk.
// So grava quando a configuracao do repositorio permitir (habilitada, modo "gravar", autor_id) e o chamado
// estiver em protocolos_autorizados. Alterar essa configuracao exige commit no GitHub.
// Variavel de ambiente necessaria na Vercel: MOVIDESK_TOKEN.
const {REPO} = require('./_comum');

const API = 'https://api.movidesk.com/public/v1';
const PREFIXO = 'LOG DE ANÁLISE AUTOMÁTICA';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const negrito = s => s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
const mascara = t => String(t).replace(/token=[^&\s']+/g, 'token=***');

async function md(metodo, caminho, params, corpo) {
  const q = new URLSearchParams(Object.assign({token: process.env.MOVIDESK_TOKEN}, params));
  const r = await fetch(`${API}${caminho}?${q}`, {method: metodo, headers: {'Content-Type': 'application/json'}, body: corpo ? JSON.stringify(corpo) : undefined});
  if (!r.ok) throw new Error(`Movidesk respondeu ${r.status}`);
  const t = await r.text();
  return t ? JSON.parse(t) : null;
}

async function configRepo() {
  const r = await fetch(`https://raw.githubusercontent.com/${REPO}/main/config_automacao.json?t=${Date.now()}`);
  if (!r.ok) throw new Error('Não consegui ler a configuração do repositório.');
  return r.json();
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({erro: 'Use POST.'});
  const fim = (codigo, erro, extra) => res.status(codigo).json(Object.assign({ok: !erro, erro}, extra));
  try {
    if (!process.env.MOVIDESK_TOKEN) return fim(503, 'MOVIDESK_TOKEN não configurado na Vercel.');
    const protocolo = String((req.body && req.body.protocolo) || '').replace(/[^0-9A-Za-z_-]/g, '');
    const texto = String((req.body && req.body.texto) || '').trim();
    if (!protocolo || !texto) return fim(400, 'Informe o protocolo e o texto do log.');
    if (texto.length > 8000) return fim(400, 'Texto grande demais.');
    const cfg = await configRepo();
    if (!cfg.habilitada) return fim(403, 'Automação desabilitada na configuração do repositório (habilitada = false). Nada foi gravado.');
    if (cfg.modo !== 'gravar') return fim(403, 'Modo "simulacao" na configuração. Para inserir de verdade, mude para "gravar" e salve no GitHub.');
    if (!(cfg.protocolos_autorizados || []).map(String).includes(protocolo)) return fim(403, 'Este chamado não está em "Chamados autorizados" na configuração salva.');

    let t = null;
    for (const c of ['/tickets', '/tickets/past']) {
      const r = await md('GET', c, {'$select': 'id,protocol', '$filter': `protocol eq '${protocolo}'`, '$top': '1'});
      if (r && r.length) { t = r[0]; break; }
    }
    if (!t) return fim(404, 'Chamado não encontrado no Movidesk.');
    const antes = await md('GET', '/tickets', {id: t.id, '$select': 'id', '$expand': 'actions($select=id,type,description,createdDate)'});
    const recente = ((antes && antes.actions) || []).some(a => ((a.description || '').indexOf(PREFIXO) !== -1 || (a.description || '').indexOf('[ANÁLISE IA]') !== -1) && Date.now() - new Date(a.createdDate).getTime() < 60 * 60 * 1000);
    if (recente) return fim(409, 'Este chamado já recebeu um log automático na última hora. Nada foi gravado.');

    // Movidesk nao da margem entre <p>: uma linha por <p> e <p><br></p> como linha em branco.
    const html = texto.split(/\r?\n/).map(l => l.trim() ? `<p>${negrito(esc(l))}</p>` : '<p><br></p>').join('');
    const tipo = Number(cfg.tipo_acao || 1);
    const acaoNova = {type: tipo, description: html};
    if (String(cfg.autor_id || '').trim()) acaoNova.createdBy = {id: String(cfg.autor_id).trim()};
    await md('PATCH', '/tickets', {id: t.id}, {actions: [acaoNova]});
    const depois = await md('GET', '/tickets', {id: t.id, '$select': 'id', '$expand': 'actions($select=id,type,description,createdDate)'});
    const marca = ((texto.match(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}/) || [])[0]) || esc(texto.split('\n')[0].replace(/\*\*/g, '').trim());
    const acao = ((depois && depois.actions) || []).filter(a => (a.description || '').indexOf(marca) !== -1).pop();
    if (!acao) return fim(200, null, {aviso: 'Gravado, mas não consegui reler a ação para conferir o tipo.'});
    const ok = Number(acao.type) === tipo;
    return fim(200, null, {tipoGravado: acao.type, tipoEsperado: tipo, aviso: ok ? '' : `Atenção: a ação ficou com tipo ${acao.type} (esperado ${tipo}). Confira no Movidesk se ficou interna.`});
  } catch (e) {
    return fim(500, mascara(e.message || e));
  }
};
