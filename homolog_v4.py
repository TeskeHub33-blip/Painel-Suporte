# -*- coding: utf-8 -*-
"""Homologacao v4: alinhamento ao padrao visual EmiteAi (skill emiteai-prototype-builder).

SO' a versao de homologacao usa este CSS (ver homolog_extras.aplicar_homologacao com badge=True); a producao nao muda.

Regras aplicadas (do design-system.md e do emiteai-base.css da skill):
  - cards/panels/KPIs: sombra (--shadow / --shadow2 no hover), sem borda; raio 6px
  - KPI: barra superior de 3px pela cor do estado, valor 22/700 com letter-spacing -0.5px, rotulo 11/600 em CAIXA ALTA com 0.6px
  - status pills: raio 6px, 12/600, trio dim/texto/borda, ponto de 6px
  - botoes de acao: outlined navy (1.25px #878799, 43px, 15/600); preenchido so' em modal/drawer; nada de rosa preenchido
  - estado ativo marcado em rosa (aba, chip, sublinhado de 2px); rosa nunca como preenchimento de botao
  - cabecalho de tabela em surface2, linha com hover sutil; inputs com borda fina e foco de 1.5px
  - transicoes de 0.15s
"""

V4_CSS = """
/* ===== HOMOLOGACAO v4: padrao visual EmiteAi ===== */
:root { --shadow: rgba(0,0,0,0.12) 0px 2px 6px 0px; --shadow2: rgba(0,0,0,0.18) 0px 4px 12px 0px; }
html[data-tema="dark"] { --shadow: rgba(0,0,0,0.35) 0px 2px 8px 0px; --shadow2: rgba(0,0,0,0.5) 0px 6px 18px 0px; }

/* superficies: sombra, sem borda */
.panel, .kpi, .emis-card, .hml-exec, .fl-lane { border: none !important; border-radius: 6px; box-shadow: var(--shadow); transition: box-shadow .15s; }
.kpi:hover, .panel:hover { box-shadow: var(--shadow2); }
.panel h2 { font-size: 13px; font-weight: 600; letter-spacing: 0; }
.panel .panel-sub { font-size: 12px; }

/* KPI: barra superior de 3px, valor 22/700, rotulo em caixa alta */
.kpi { padding: 18px 20px; position: relative; overflow: hidden; }
.kpi::before { display: block !important; content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--text3); }
.kpi.ok::before { background: var(--ok-solid, var(--ok)); } .kpi.warn::before { background: var(--warn-solid); } .kpi.danger::before { background: var(--danger); }
.kpi .value { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }
.kpi .label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); margin-top: 6px; }

/* status pills: raio 6px, 12/600, trio dim/texto/borda, ponto de 6px */
.gm-selo, .hml-chip { display: inline-flex; align-items: center; gap: 5px; border-radius: 6px; font-size: 12px; font-weight: 600; padding: 3px 10px; border: 1px solid var(--panel-border); background: var(--surface2); color: var(--text-dim); white-space: nowrap; }
.gm-selo::before, .hml-chip.ok::before, .hml-chip.warn::before, .hml-chip.bad::before, .hml-chip.pink::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.gm-ok, .hml-chip.ok { background: var(--ok-dim); color: var(--ok); border-color: var(--ok-bord); }
.gm-warn, .hml-chip.warn { background: var(--warn-dim); color: var(--warn); border-color: var(--warn-bord); }
.gm-bad, .hml-chip.bad, .gb-urg-alta { background: var(--danger-dim); color: var(--danger); border-color: var(--danger-bord); }
.gm-info, .hml-chip.pink { background: var(--pink-dim); color: var(--pink); border-color: rgba(237,109,162,.35); }
.gb-urg-media { background: var(--warn-dim); color: var(--warn); border-color: var(--warn-bord); }
.hml-badge { background: var(--pink-dim); color: var(--pink); border: 1px solid rgba(237,109,162,.35); border-radius: 6px; font-size: 11px; letter-spacing: .8px; }

/* tabelas: cabecalho em surface2, linha com hover sutil */
#giSub_melhorias .panel table th, #giSub_bugs .panel table th { background: var(--surface2) !important; color: var(--text); font-size: 13px; font-weight: 600; text-transform: none; letter-spacing: 0; padding: 10px 14px; border-bottom: 1px solid rgba(135,135,153,.15); }
#giSub_melhorias .panel table td, #giSub_bugs .panel table td { padding: 11px 14px; border-bottom: 1px solid rgba(135,135,153,.12); font-size: 13px; }
#giSub_melhorias .panel table tbody tr:hover td, #giSub_bugs .panel table tbody tr:hover td { background: rgba(36,36,62,.025); }
html[data-tema="dark"] #giSub_melhorias .panel table tbody tr:hover td, html[data-tema="dark"] #giSub_bugs .panel table tbody tr:hover td { background: rgba(255,255,255,.03); }

/* botoes de acao: outlined navy; nada de rosa preenchido */
.hml-busca button, #tabFluxo .flow-search-row .export-btn, .hml-tema {
  background: transparent !important; color: var(--navy) !important; border: 1.25px solid #878799 !important; border-radius: 6px; font-size: 15px; font-weight: 600;
  height: 43px; padding: 7px 21px; transition: background .15s, border-color .15s; display: inline-flex; align-items: center; gap: 6px; }
.hml-busca button:hover, #tabFluxo .flow-search-row .export-btn:hover, .hml-tema:hover { background: rgba(36,36,62,.05) !important; border-color: var(--navy) !important; filter: none; }
html[data-tema="dark"] .hml-busca button:hover, html[data-tema="dark"] #tabFluxo .flow-search-row .export-btn:hover, html[data-tema="dark"] .hml-tema:hover { background: rgba(255,255,255,.06) !important; }
.hml-tema { height: 34px; padding: 4px 12px; font-size: 13px; margin-right: 14px; }
.hml-exec-acoes a, .hml-exec-acoes button { height: auto; padding: 4px 12px; font-size: 13px; font-weight: 600; color: var(--navy); border: 1.25px solid #878799; border-radius: 6px; transition: background .15s, border-color .15s; }
.hml-exec-acoes a:hover, .hml-exec-acoes button:hover { background: rgba(36,36,62,.05); border-color: var(--navy); color: var(--navy); }

/* campos: borda fina, foco de 1.5px */
.hml-busca input, #tabFluxo .flow-search-row input, #tabFluxo .flow-search-row select { font-size: 16px; padding: 10px 14px; border: .625px solid rgba(135,135,153,.7); border-radius: 6px; background: var(--panel); color: var(--text); outline: none; transition: border-color .15s; }
.hml-busca input:focus, #tabFluxo .flow-search-row input:focus, #tabFluxo .flow-search-row select:focus { border: 1.5px solid var(--navy); padding: 9.4px 13.4px; }
#tabFluxo .flow-search-row { border-radius: 6px; }

/* estado ativo sempre em rosa (aba, chip, sublinhado de 2px) */
.tab-btn.active { background: var(--pink-dim) !important; color: var(--navy) !important; border-color: var(--pink) !important; }
.seg-toggle button.active { background: var(--pink-dim); color: var(--text); box-shadow: inset 0 0 0 1px var(--pink); }
.gi-nav button { border-bottom: 2px solid transparent; transition: color .15s, border-color .15s; }
.gi-nav button.active { border-bottom-color: var(--pink); }
.gi-nav button::before { width: 16px; height: 16px; }

/* kanban: cartao com sombra e faixa de estado, coluna em surface2 */
.gm-card { border: none !important; box-shadow: var(--shadow), inset 3px 0 0 var(--ok); background: var(--panel); border-radius: 6px; }
.gm-card.gm-b-warn { box-shadow: var(--shadow), inset 3px 0 0 var(--warn-solid); }
.gm-card.gm-b-danger { box-shadow: var(--shadow), inset 3px 0 0 var(--danger); }
.gm-col { background: var(--surface2); border: none; box-shadow: none; border-radius: 6px; }
.gm-col.gm-key { background: var(--pink-dim); }
.gm-col h3 em { background: var(--panel); color: var(--text); border-radius: 6px; padding: 1px 9px; font-weight: 600; box-shadow: var(--shadow); }

/* fluxo: no, linha e decisao no mesmo padrao */
.fl-node { background: var(--panel); border: none; box-shadow: var(--shadow); border-radius: 6px; transition: transform .15s, box-shadow .15s; }
.fl-node:hover, .fl-node:focus-visible { transform: translateY(-2px); box-shadow: var(--shadow2); border: none; }
.fl-node.fl-ponto { background: var(--navy); }
.fl-node.fl-dec { background: var(--pink-dim); box-shadow: inset 0 0 0 1px var(--pink); }
.fl-node.fl-fim { background: var(--surface2); }
.fl-node .fl-n { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
.fl-lane h3, .hml-exec-grid .k, .hml-exec-bloco .k { letter-spacing: .6px; }

/* resumo executivo: cartao sem faixa lateral */
.hml-exec { border-left: none !important; }

/* etapa da melhoria selecionada: passos no resumo e destaque no no do Fluxo */
.hml-passos { display: flex; flex-wrap: wrap; gap: 6px; }
.hml-passo { flex: 1 1 120px; padding: 8px 12px; border-radius: 6px; background: var(--surface2); color: var(--text3); font-size: 12px; font-weight: 600; transition: background .15s; }
.hml-passo small { display: block; font-size: 10px; font-weight: 600; letter-spacing: .6px; text-transform: uppercase; color: var(--pink); }
.hml-passo.feito { color: var(--ok); box-shadow: inset 3px 0 0 var(--ok); }
.hml-passo.atual { background: var(--pink-dim); color: var(--text); box-shadow: inset 0 0 0 1.5px var(--pink); }
.fl-node.fl-atual { box-shadow: var(--shadow2), inset 0 0 0 2px var(--pink); background: var(--pink-dim); }
.fl-node.fl-atual::before { content: 'Etapa atual'; position: absolute; top: -9px; left: 12px; padding: 1px 8px; border-radius: 6px; background: var(--pink); color: #fff; font-size: 10px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; }

/* ===== Fluxograma (aba) na mesma identidade do fluxo de melhorias ===== */
#tabFluxo #flowDiagram { gap: 14px; }
#tabFluxo .flow-row { gap: 0; align-items: stretch; padding: 8px 2px 10px; }
#tabFluxo #flowRowMain::before, #tabFluxo #flowRowSecundaria::before { flex-basis: 100%; margin-bottom: 12px; font-size: 12px; font-weight: 600; letter-spacing: .8px; text-transform: uppercase; color: var(--text3); }
#tabFluxo #flowRowMain::before { content: 'Fluxo de atendimento'; }
#tabFluxo #flowRowSecundaria::before { content: 'Desvio do fluxo'; }
#tabFluxo .flow-box { background: var(--panel); border: none; border-radius: 6px; box-shadow: var(--shadow); padding: 12px 14px; min-width: 168px; transition: transform .15s, box-shadow .15s;
  animation: flIn .45s ease both; overflow: visible; }
#tabFluxo .flow-box.resizable { overflow: visible; }
#tabFluxo .flow-box .flow-title { font-size: 12.5px; font-weight: 600; color: var(--text); min-height: 32px; align-items: flex-start; }
#tabFluxo .flow-box .flow-sub { font-size: 11px; color: var(--text3); line-height: 1.35; }
#tabFluxo .flow-box .flow-time { font-size: 11px; color: var(--text-dim); }
#tabFluxo .flow-box .flow-count { margin-top: 8px; border-radius: 6px; font-size: 12px; font-weight: 600; padding: 3px 10px; background: var(--surface2); color: var(--text); }
#tabFluxo .flow-box.flow-done { background: var(--panel); box-shadow: var(--shadow), inset 3px 0 0 var(--ok); }
#tabFluxo .flow-box.flow-done .flow-title { color: var(--ok); }
#tabFluxo .flow-box.flow-current { background: var(--pink-dim); box-shadow: var(--shadow2), inset 0 0 0 2px var(--pink); }
#tabFluxo .flow-box.flow-current .flow-title { color: var(--text); }
#tabFluxo .flow-box.flow-current::before { content: 'Etapa atual'; position: absolute; top: -9px; left: 12px; padding: 1px 8px; border-radius: 6px; background: var(--pink); color: #fff; font-size: 10px; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; }
#tabFluxo .flow-box.flow-blocked { background: var(--danger-dim); box-shadow: var(--shadow), inset 0 0 0 2px var(--danger); }
#tabFluxo .flow-box.flow-blocked .flow-title { color: var(--danger); }
#tabFluxo .flow-box.flow-clickable:hover { transform: translateY(-2px); box-shadow: var(--shadow2); border: none; }
#tabFluxo .flow-box.flow-clickable:focus-visible { outline: 2px solid var(--pink); outline-offset: 2px; }
#tabFluxo .flow-row .flow-box { margin-right: 44px; }
#tabFluxo .flow-row .flow-box:last-child { margin-right: 0; }
#tabFluxo .flow-row .flow-box:not(:last-child)::after { content: ''; position: absolute; right: -38px; top: 50%; width: 30px; height: 2px; transform: none; font-size: 0;
  background: repeating-linear-gradient(90deg, var(--navy-lt) 0 6px, transparent 6px 11px); background-size: 22px 2px; animation: flFlow 1s linear infinite; }
#tabFluxo .flow-row .flow-box:not(:last-child) .flow-title::after { content: ''; position: absolute; right: -44px; top: calc(50% - 5px); border-left: 7px solid var(--navy-lt); border-top: 5px solid transparent; border-bottom: 5px solid transparent; }
#tabFluxo .flow-next-pill { background: transparent; border: 1.25px solid #878799; border-radius: 6px; color: var(--navy); font-weight: 600; font-size: 11.5px; transition: background .15s, border-color .15s; }
#tabFluxo .flow-next-pill:hover { background: var(--pink-dim); border-color: var(--pink); }
#tabFluxo .flow-next-steps { background: var(--surface2); border-left: none; border-radius: 6px; }
@media (prefers-reduced-motion: reduce) { #tabFluxo .flow-box, #tabFluxo .flow-row .flow-box:not(:last-child)::after { animation: none; } }
"""


def aplicar_v4_css():
    return V4_CSS
