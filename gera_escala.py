# -*- coding: utf-8 -*-
"""Atualiza escala.json (quadros de escala do Ao Vivo) SOMENTE com dados lidos do SharePoint.

Uso:  python -I gera_escala.py <distribuicao.txt> [<dashboard.txt>]
  distribuicao.txt = texto da aba "Distribuição de Atividades" (pagina 4) da planilha Atividades_Suporte_EmiteAi,
                     como o conector Microsoft 365 devolve. O conector corta o fim da aba (por volta do dia 21).
  dashboard.txt    = (opcional) texto da aba "Dashboard" (pagina 1). Serve para o dia de HOJE quando ele esta
                     alem do corte: traz so' o Principal de cada atividade, hora a hora. So' e' usado se a data
                     selecionada na planilha for a de hoje (Brasilia).
Dias/horas que o SharePoint nao devolveu NAO sao inventados: ficam sem escala publicada.
Grava o arquivo apenas se o conteudo mudou. Imprime MUDOU, SEM MUDANCA ou ERRO."""
import datetime
import json
import os
import re
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'escala.json')
ATIV = ['Guias Shopee', 'Chat', 'Whatsapp', '55PBX', 'Chamados Novos', 'Chamados priorizados',
        'N2 Tasks (abertura, validação e impedimento)', 'N2 Apoio']
BRT = datetime.timezone(datetime.timedelta(hours=-3))


def idx(hora):
    """A aba usa a DATA DO CALENDARIO em todas as linhas (00h..23h): a posicao e a propria hora."""
    return hora


def celulas(vals):
    """24 valores (8 atividades x P,2a,3a) -> 8 strings 'P|2a|3a' (vazio = ninguem; 'fora' = fora da janela)."""
    v = [(str(x).strip() if x is not None else '') for x in vals]
    v += [''] * (24 - len(v))
    return ['|'.join(v[i * 3:i * 3 + 3]).rstrip('|') for i in range(8)]


def le_distribuicao(caminho):
    linhas = {}
    for l in open(caminho, encoding='utf-8').read().split('\n'):
        m = re.match(r'(\d{2})/(\d{2})/(\d{4})\t[^\t]*\t(\d{2}):00\t?(.*)$', l)
        if m:
            linhas[('%s-%s-%s' % (m.group(3), m.group(2), m.group(1)), int(m.group(4)))] = celulas(m.group(5).split('\t'))
    return linhas


def le_dashboard(caminho):
    """-> (data ISO, {indice da atividade: [24 principais na ordem 06h..05h]}) ou (None, {})"""
    L = open(caminho, encoding='utf-8').read().split('\n')
    data = None
    grade = {}
    for i, l in enumerate(L):
        if l.startswith('Formulas'):
            break
        m = re.match(r'Selecione a data:\t(\d{2})/(\d{2})/(\d{4})', l)
        if m:
            data = '%s-%s-%s' % (m.group(3), m.group(2), m.group(1))
        if l.startswith('Atividade\t06h\t07h'):
            for k in L[i + 1:i + 9]:
                c = k.split('\t')
                nome = c[0].strip()
                achou = [a for a, n in enumerate(ATIV) if n == nome or n.split(' (')[0] == nome.split(' (')[0]]
                if achou and len(c) >= 25:
                    grade[achou[0]] = [('' if x.strip() in ('—', '-') else x.strip()) for x in c[1:25]]
            break
    return data, grade


if len(sys.argv) < 2:
    print('ERRO: informe o arquivo de texto da aba Distribuição de Atividades')
    sys.exit(2)
sp = le_distribuicao(sys.argv[1])
if not sp:
    print('ERRO: nenhuma linha lida do SharePoint; nada foi alterado')
    sys.exit(2)

try:
    ant = json.load(open(OUT, encoding='utf-8'))
except Exception:
    ant = {}

corte_d, corte_h = max(sp, key=lambda k: (k[0], idx(k[1])))      # ultima data/hora devolvida pelo conector
dias = {}
for (d, h), v in sp.items():
    dias.setdefault(d, [None] * 24)[idx(h)] = v

# dias vindos do Dashboard em execucoes anteriores continuam valendo (sao do SharePoint), se estiverem alem do corte
so_principal = []
for d in (ant.get('so_principal') or []):
    velho = (ant.get('dias') or {}).get(d)
    if not velho or d < corte_d:
        continue
    lst = dias.setdefault(d, [None] * 24)
    usou = False
    for h in range(24):
        if lst[h] is None and velho[h] is not None:
            lst[h] = velho[h]
            usou = True
    if usou:
        so_principal.append(d)

hoje = datetime.datetime.now(BRT).date().isoformat()
aviso = ''
if len(sys.argv) > 2:
    d_dash, grade = le_dashboard(sys.argv[2])
    if d_dash != hoje:
        aviso = 'Dashboard com data %s (hoje e %s): ignorado' % (d_dash, hoje)
    elif len(grade) == 8:
        # o Dashboard cobre o dia operacional: 06h..23h de hoje e 00h..05h de amanha (datas do calendario)
        amanha = (datetime.date.fromisoformat(hoje) + datetime.timedelta(days=1)).isoformat()
        for pos in range(24):
            hora = (pos + 6) % 24
            d = hoje if hora >= 6 else amanha
            lst = dias.setdefault(d, [None] * 24)
            if lst[hora] is None:
                lst[hora] = [grade[a][pos] for a in range(8)]
                if d not in so_principal:
                    so_principal.append(d)
    else:
        aviso = 'Dashboard sem a grade completa: ignorado'

for d in dias:
    dias[d] = [x if x is not None else None for x in dias[d]]      # None = hora nao publicada

# horas alem do corte de hoje que uma leitura anterior do SharePoint ja trouxe continuam valendo (o corte da aba varia de leitura para leitura)
for d, velho in (ant.get('dias') or {}).items():
    if d < corte_d:
        continue
    lst = dias.setdefault(d, [None] * 24)
    for h in range(24):
        if lst[h] is None and velho[h] is not None and (d, h) > (corte_d, corte_h):
            lst[h] = list(velho[h])

# REGRA DA OPERACAO (pedida em 18/11/2026): em dia util, na janela do 55PBX, quando o Vitor nao esta na escala daquela hora,
# o 55PBX fica com Augusto Geisler (principal) e Gustavo Lange (2o). O Whatsapp nao muda: continua com outro N1, como na planilha.
# So' vale onde a planilha ja tem a hora publicada e o 55PBX nao esta "fora"; fins de semana e feriados seguem a planilha.
REGRA_55PBX = 'Augusto Geisler|Gustavo Lange'
for d, lst in dias.items():
    if datetime.date.fromisoformat(d).weekday() >= 5:
        continue
    for h, cel in enumerate(lst):
        if not cel or cel[3].split('|')[0].strip().lower() == 'fora':
            continue
        if any('vitor' in n.lower() for c in cel for n in c.split('|')):
            continue
        cel[3] = REGRA_55PBX

# REGRAS DA OPERACAO (pedidas em 24/11/2026), aplicadas por cima da planilha, so' onde a hora ja esta publicada:
# 1) Guias Shopee: das 06h as 11h ficam Maria Paula (principal) e Joao Matoso (2o); das 11h as 16h fica Guilherme Paredes.
#    Cada um so' entra dentro do proprio horario de trabalho e se aparece na escala daquele dia (ausencia/folga na planilha vale).
# 2) Bruna Rocha, so' nas sextas: comeca as 16h em vez de 18h (Chamados Novos principal; no Chat entra de 2a, pois ja ha principal).
def _nomes_dia(lst, h0, h1):
    s = set()
    for h in range(h0, h1 + 1):
        for c in (lst[h] or []):
            for n in c.split('|'):
                s.add(n.strip())
    return s


def _poe_bruna(txt, so_se_principal_ocupado=False):
    """Poe a Bruna na celula 'P|2a|3a': principal se estiver vazio (Novos); 2o se o principal ja estiver ocupado (Chat)."""
    vazio = lambda x: x.strip() in ('', '—', '-')
    p = (txt.split('|') + ['—', '—', '—'])[:3]
    if 'Bruna Rocha' in p:
        return txt
    if vazio(p[0]):
        p[0] = 'Bruna Rocha'
    elif vazio(p[1]):
        p[1] = 'Bruna Rocha'
    return '|'.join(p)


# horas (inicio inclusive) em que cada pessoa pode assumir Guias Shopee, por dia da semana (0 = segunda)
HORAS_SHOPEE = {
    'Maria Paula': {1: range(6, 11), 2: range(6, 11), 3: range(6, 11), 4: range(6, 11), 5: range(6, 11)},
    'João Matoso': {0: range(6, 11), 1: range(6, 11), 2: range(6, 11), 3: range(6, 11), 4: range(6, 11)},
    'Guilherme Paredes': {0: (11, 13, 14, 15), 1: (11, 13, 14, 15), 2: (11, 13, 14, 15), 3: (11, 13, 14, 15), 4: (11, 12)},
}
for d, lst in dias.items():
    wd = datetime.date.fromisoformat(d).weekday()
    presentes = {'Maria Paula': _nomes_dia(lst, 6, 10), 'João Matoso': _nomes_dia(lst, 6, 10),
                 'Guilherme Paredes': _nomes_dia(lst, 8, 18), 'Bruna Rocha': _nomes_dia(lst, 18, 23)}
    antes = [list(c) if c else c for c in lst]
    for h in range(24):
        cel = lst[h]
        if not cel or cel[0].split('|')[0].strip().lower() == 'fora':
            continue
        if 6 <= h <= 10:
            quem = [n for n in ('Maria Paula', 'João Matoso') if h in HORAS_SHOPEE[n].get(wd, ()) and n in presentes[n]]
            if quem:
                cel[0] = '|'.join(quem)
        elif 11 <= h <= 15:
            g = 'Guilherme Paredes'
            if h in HORAS_SHOPEE[g].get(wd, ()) and g in presentes[g]:
                cel[0] = g
        if wd == 4 and h in (16, 17) and 'Bruna Rocha' in presentes['Bruna Rocha']:
            b = 'Bruna Rocha'
            cel[4] = _poe_bruna(cel[4])
            cel[1] = _poe_bruna(cel[1], so_se_principal_ocupado=True)

saida = {
    'gerado_em': datetime.datetime.now(BRT).strftime('%d/%m/%Y %H:%M') + ' (Brasília)',
    'fonte': 'Planilhas Atividades_Suporte_EmiteAi e Programação de Alocação de Sobreaviso (SharePoint, time Operações/Suporte)',
    'atividades': ATIV,
    'dias': dict(sorted(dias.items())),
    'conferido_ate': '%s %02dh' % (corte_d, corte_h),
    'so_principal': sorted(so_principal),
    'sobreaviso': ant.get('sobreaviso', {}),
}
chaves = ('atividades', 'dias', 'conferido_ate', 'so_principal', 'sobreaviso')
if ant and all(ant.get(k) == saida[k] for k in chaves):
    print('SEM MUDANCA: escala igual a ja salva; arquivo nao alterado.', aviso)
    sys.exit(0)
mudou = sum(1 for d, hs in saida['dias'].items() for i, v in enumerate(hs) if ((ant.get('dias') or {}).get(d) or [None] * 24)[i] != v)
open(OUT, 'w', encoding='utf-8', newline=chr(10)).write(json.dumps(saida, ensure_ascii=False, separators=(',', ':')) + chr(10))
print('MUDOU: %d horas diferentes do salvo | dias: %d (%s a %s) | SharePoint devolveu ate %s | dias so com Principal: %s' % (
    mudou, len(dias), min(dias), max(dias), saida['conferido_ate'], saida['so_principal'] or 'nenhum'), aviso)
