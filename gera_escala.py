# -*- coding: utf-8 -*-
"""Monta escala.json com o mes inteiro a partir da aba "Distribuição de Atividades".
Fonte 1 (atual): texto lido do SharePoint (o conector corta as ultimas linhas da aba).
Fonte 2 (complemento): copia local da planilha, so' para as linhas que o SharePoint nao devolveu."""
import datetime
import json
import os
import re
import sys

import openpyxl

SP_TXT = sys.argv[1]
LOCAL = r'C:\Users\WellingtonErvinoTesk\Downloads\Atividades_Suporte_EmiteAi_4.xlsx'
OUT = r'C:\Users\WellingtonErvinoTesk\Documents\Claude\manual_suporte\escala.json'
ATIV = ['Guias Shopee', 'Chat', 'Whatsapp', '55PBX', 'Chamados Novos', 'Chamados priorizados',
        'N2 Tasks (abertura, validação e impedimento)', 'N2 Apoio']


def celulas(vals):
    """24 valores (8 atividades x P,2a,3a) -> lista de 8 strings 'P|2a|3a' (vazio = ninguem; 'fora' = fora da janela)."""
    v = [(str(x).strip() if x is not None else '') for x in vals]
    v += [''] * (24 - len(v))
    return ['|'.join(v[i * 3:i * 3 + 3]).rstrip('|') for i in range(8)]


linhas = {}   # (data ISO, hora) -> [8 strings]
fonte = {}
# base: o que ja esta salvo (dias que o SharePoint nao devolver continuam como estavam)
try:
    _ant = json.load(open(OUT, encoding='utf-8'))
except Exception:
    _ant = {}
for _d, _horas in (_ant.get('dias') or {}).items():
    for _i, _v in enumerate(_horas):
        linhas[(_d, (_i + 6) % 24)] = _v
        fonte[(_d, (_i + 6) % 24)] = 'salvo'
n_local = len(linhas)
if not _ant.get('dias') and os.path.exists(LOCAL):      # primeira carga: completa o fim do mes com a copia local
    wb = openpyxl.load_workbook(LOCAL, data_only=True)
    for r in wb.worksheets[3].iter_rows(min_row=3, values_only=True):
        if isinstance(r[0], datetime.datetime) and isinstance(r[2], datetime.time):
            linhas[(r[0].date().isoformat(), r[2].hour)] = celulas(r[3:27])
            fonte[(r[0].date().isoformat(), r[2].hour)] = 'local'
    n_local = len(linhas)

dif = 0
n_sp = 0
for l in open(SP_TXT, encoding='utf-8').read().split('\n'):
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})\t[^\t]*\t(\d{2}):00\t?(.*)$', l)
    if not m:
        continue
    k = ('%s-%s-%s' % (m.group(3), m.group(2), m.group(1)), int(m.group(4)))
    novo = celulas(m.group(5).split('\t'))
    if k in linhas and linhas[k] != novo:
        dif += 1
    linhas[k] = novo
    fonte[k] = 'sharepoint'
    n_sp += 1

dias = {}
for (d, h), v in linhas.items():
    dias.setdefault(d, [None] * 24)[(h - 6) % 24] = v      # ordem do dia operacional: 06h..23h, 00h..05h
for d in dias:
    dias[d] = [x or [''] * 8 for x in dias[d]]

try:
    antigo = json.load(open(OUT, encoding='utf-8'))
except Exception:
    antigo = {}
agora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime('%d/%m/%Y %H:%M')
ultimo_sp = max(k for k, f in fonte.items() if f == 'sharepoint')
saida = {
    'gerado_em': agora + ' (Brasília)',
    'fonte': 'Planilhas Atividades_Suporte_EmiteAi (aba Distribuição de Atividades) e Programação de Alocação de Sobreaviso (SharePoint, time Operações/Suporte)',
    'atividades': ATIV,
    'dias': dict(sorted(dias.items())),
    'conferido_ate': '%s %02dh' % ultimo_sp,
    'sobreaviso': antigo.get('sobreaviso', {}),
}
igual = bool(_ant) and all(_ant.get(k) == saida[k] for k in ('atividades', 'dias', 'sobreaviso'))
if n_sp == 0:
    print('ERRO: nenhuma linha lida do SharePoint; nada foi alterado'); sys.exit(2)
if igual:
    print('SEM MUDANCA: escala igual a ja salva; arquivo nao alterado'); sys.exit(0)
if _ant.get('conferido_ate', '') > saida['conferido_ate']:
    saida['conferido_ate'] = _ant['conferido_ate']
open(OUT, 'w', encoding='utf-8', newline=chr(10)).write(json.dumps(saida, ensure_ascii=False, separators=(',', ':')) + chr(10))
print('MUDOU: horas alteradas em relacao ao salvo:', dif, '| linhas lidas do SharePoint:', n_sp)
print('dias', len(dias), min(dias), max(dias), '| sharepoint ate', saida['conferido_ate'])
