# -*- coding: utf-8 -*-
"""Homologacao v12: textos do Fluxograma de atendimento reescritos (frases curtas, voz ativa, acentuacao correta).

SO' a versao de homologacao usa este JS (homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.
Os textos originais ficam no build_dashboard.py; aqui eles sao sobrescritos em tempo de carga, sem mudar chaves nem regras.
"""

V12_JS = r"""
// ===== HOMOLOGACAO v12: textos do Fluxograma de atendimento =====
{
  const TEXTO = {
    entrada: ['Entrada', 'O cliente abre o chamado por e-mail, WhatsApp, chat ou portal do Movidesk.'],
    triagem: ['Triagem inicial', 'Vendas, Implantação ou Suporte recebem o chamado e fazem a triagem inicial.'],
    n1: ['N1', 'O N1 faz a análise inicial, com apoio do N3 (Multiplicador) quando precisa.'],
    n2: ['N2', 'O N2 faz o repasse técnico. Status Em atendimento - N2.'],
    task_dev: ['Task no desenvolvimento', 'A task está na fila do desenvolvimento. Status Aguardando Desenvolvimento.'],
    validacao_impedimento: ['Validação ou impedimento', 'O log do Azure DevOps mostra a task em validação ou com impedimento.'],
    validacao_cliente: ['Validação do cliente', 'Chamado Resolvido, esperando o cliente confirmar a solução.'],
    encerrado: ['Encerramento', 'O chamado fecha quando o cliente confirma, ou sozinho depois de 3 dias sem resposta.'],
    pendente_usuario: ['Pendente usuário', 'Status Aguardando Cliente. Volta ao N1 quando o cliente responde e fecha sozinho depois de 3 dias sem resposta.'],
  };
  FLOW_MAIN_STAGES.concat([FLOW_SECONDARY_STAGE]).forEach(s => { const t = TEXTO[s.key]; if (t) { s.title = t[0]; s.sub = t[1]; } });
  const ROTULO = {
    entrada: {triagem: 'Segue para a triagem inicial'},
    triagem: {n1: 'Segue para o N1 (Suporte)'},
    n1: {n2: 'Repassa ao N2', pendente_usuario: 'Coloca em Pendente usuário', validacao_cliente: 'Resolve (validação do cliente)'},
    pendente_usuario: {n1: 'Volta ao N1', n2: 'Volta ao N2', encerrado: 'Encerra sem resposta (3 dias)'},
    n2: {validacao_cliente: 'Resolve (task retornada)', n1: 'Resolve e devolve ao N1', task_dev: 'Abre task no desenvolvimento'},
    task_dev: {validacao_impedimento: 'Vai para validação ou impedimento'},
    validacao_impedimento: {pendente_usuario: 'Validado: Pendente usuário', task_dev: 'Volta ao desenvolvimento'},
    validacao_cliente: {encerrado: 'Encerra o chamado'},
  };
  Object.keys(FLOW_NEXT_OPTIONS).forEach(k => (FLOW_NEXT_OPTIONS[k] || []).forEach(o => { if (ROTULO[k] && ROTULO[k][o[0]]) o[1] = ROTULO[k][o[0]]; }));
  proximosPassosTexto = function(status) {
    if (status === 'Novo') return 'O chamado está na fila, esperando o N1 começar a análise. O N3 pode apoiar quando for preciso.';
    if (status === 'Em atendimento') return 'O N1 pode <b>resolver direto</b> (o chamado vai para a validação do cliente), <b>colocar em Aguardando Cliente</b> (Pendente usuário, quando falta informação) ou <b>repassar para Em atendimento - N2</b> quando o caso pede um nível técnico mais fundo. O N3 (Multiplicador) pode apoiar o N1 em qualquer um desses passos.';
    if (status === 'Aguardando Cliente') return 'Se o cliente responder, o chamado volta para o N1 (status Em atendimento). Sem resposta, <b>fecha sozinho em 3 dias corridos</b>.';
    if (status === N2_HANDOFF_STATUS) return 'O N2 pode <b>resolver direto</b>, avisar o cliente e devolver ao N1 (fila Em atendimento), ou <b>abrir uma task para o desenvolvimento</b> (Aguardando Desenvolvimento). Nesse caso, o N2 continua responsável pelo chamado e pela task.';
    if (isDevQueueStatus(status)) return 'A task volta para o N2 de três formas: <b>em validação</b> (o N2 testa a entrega e pede ao cliente para validar), <b>em impedimento</b> (o N2 trata o motivo antes de seguir) ou <b>de volta para A Fazer</b>, quando a task não tem a análise de negócio e a solução do problema claras. Nesse caso, o desenvolvedor responsável é mencionado no comentário do Azure DevOps.';
    if (status === 'Resolvido') return 'O chamado espera a validação do cliente. Se ele confirmar a solução, o chamado é <b>fechado manualmente</b>. Sem resposta, <b>fecha sozinho depois de 3 dias corridos</b>.';
    if (status === 'Fechado' || status === 'Cancelado') return 'Fluxo encerrado. Não há próximos passos.';
    if (isGovWaitStatus(status)) return 'O chamado espera o retorno de um órgão governamental (SEFAZ, ANTT ou Portal Nacional da GNRE). Por contrato, o SLA fica pausado nesse status. Quando o órgão responde, o chamado volta para o atendimento (N1 ou N2).';
    if (status === 'Em atendimento - CS') return 'O time de Implantação ou o CS atende este chamado, fora do fluxo de Suporte.';
    return 'O chamado espera o retorno de um terceiro ou de uma etapa intermediária (' + esc(status || '-') + ') antes de seguir no atendimento técnico.';
  };
  try { renderFluxoAgregado(); } catch (e) {}
}
"""
