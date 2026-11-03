# -*- coding: utf-8 -*-
"""Analise automatica de chamados do Movidesk, com log como nota interna.

Seguranca (tudo precisa estar de acordo para gravar):
  1. config_automacao.json com "habilitada": true
  2. config_automacao.json com "modo": "gravar"
  3. variavel GRAVAR=true (input do workflow)  -> sem isso roda sempre como simulacao
  4. so' atua nos chamados de "protocolos_autorizados" (a busca automatica apenas LISTA candidatos, nunca grava)
  5. "autor_id" e opcional (id de um AGENTE no Movidesk); vazio = a acao fica com o autor do token
O token vem da variavel de ambiente MOVIDESK_TOKEN e nunca e' impresso.
Cada gravacao e' conferida depois (o tipo da acao precisa ser o configurado em "tipo_acao").
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, "config_automacao.json")
REL_PATH = os.path.join(BASE_DIR, "automacao_relatorio.json")
API = os.environ.get("MOVIDESK_BASE_URL", "https://api.movidesk.com/public/v1")
BRT = timezone(timedelta(hours=-3))
CAMPOS = ("id,protocol,subject,category,urgency,status,ownerTeam,tags,createdDate,lastUpdate,"
          "lastActionDate,slaSolutionDate")
PASSO_S = 6.5                       # limite do Movidesk: 10 requisicoes por minuto
PREFIXO_LOG = "LOG DE ANÁLISE AUTOMÁTICA"


def agora():
    return datetime.now(BRT)


def mascara(txt):
    return re.sub(r"token=[^&\s']+", "token=***", str(txt))


def chamar(metodo, caminho, params=None, corpo=None):
    token = os.environ.get("MOVIDESK_TOKEN", "").strip()
    if not token:
        raise RuntimeError("MOVIDESK_TOKEN nao esta definido no ambiente")
    p = {"token": token}
    p.update(params or {})
    try:
        r = requests.request(metodo, API + caminho, params=p, json=corpo, timeout=60)
    except requests.RequestException as e:
        raise RuntimeError("erro de rede: " + type(e).__name__)
    time.sleep(PASSO_S)
    if r.status_code >= 400:
        raise RuntimeError("Movidesk respondeu HTTP %d em %s" % (r.status_code, caminho))
    return r.json() if r.text.strip() else None


# ---------------------------------------------------------------- analise (regras fixas, sem IA)
def parse_dt(s):
    if not s:
        return None
    return datetime.strptime(s.split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def fmt_dur(h):
    if h is None:
        return "não informado"
    return "%.1f h" % h if h < 24 else "%.1f dias" % (h / 24)


def tem_tag(tags, prefixo):
    return any(prefixo in (t or "").lower() for t in (tags or []))


def etapa_de(t):
    st, tags = t.get("status") or "", t.get("tags") or []
    tec, com, apr = tem_tag(tags, "estimativa t"), tem_tag(tags, "estimativa c"), tem_tag(tags, "aprovado")
    if t.get("category") == "Melhoria":
        if st == "Refinamento Suporte Melhoria":
            return "Aprovado pelo produto, task a abrir" if apr else ("Aguardando estimativa técnica" if tec else "Aguardando reunião de alinhamento")
        if st == "Em atendimento - CS" and tec and com:
            return "Aguardando orçamento"
        if st == "Aguardando Cliente":
            return "Aguardando assinatura do cliente" if com else ("Aguardando aprovação comercial" if tec else "Pendente usuário")
        if st == "Aguardando Desenvolvimento" and (apr or com):
            return "Entrega agendada" if t.get("slaSolutionDate") else "Aguardando previsão de entrega"
    return {"Novo": "Fila inicial, aguardando o N1", "Em atendimento": "N1", "Em atendimento - N2": "N2",
            "Aguardando Cliente": "Pendente usuário", "Aguardando Desenvolvimento": "Task no desenvolvimento",
            "Resolvido": "Validação do cliente", "Fechado": "Encerrado", "Cancelado": "Encerrado"}.get(st, st or "não informado")


PROXIMO = {
    "Novo": "O N1 deve iniciar a análise; o N3 pode apoiar se for preciso.",
    "Em atendimento": "O N1 pode resolver, colocar em Pendente usuário (falta informação) ou repassar para Em atendimento - N2.",
    "Em atendimento - N2": "O N2 pode resolver e devolver ao N1, ou abrir task para o desenvolvimento.",
    "Aguardando Cliente": "Aguardar o cliente; se responder, volta ao N1. Sem resposta, fecha sozinho em 3 dias corridos.",
    "Aguardando Desenvolvimento": "A task está com o desenvolvimento; acompanhar o log do Azure DevOps (validação ou impedimento).",
    "Resolvido": "Aguardar a confirmação do cliente; sem resposta, fecha sozinho em 3 dias corridos.",
    "Refinamento Suporte Melhoria": "Aguardar a reunião de alinhamento com o Produto (quarta, 14:00) e a decisão: roadmap ou cobrada.",
}


def analisar(t, ref=None):
    """Devolve os campos do log a partir de um chamado (dict da API)."""
    ref = ref or datetime.now(timezone.utc)
    ult = parse_dt(t.get("lastActionDate")) or parse_dt(t.get("lastUpdate"))
    parado_h = (ref - ult).total_seconds() / 3600 if ult else None
    sla_dt = parse_dt(t.get("slaSolutionDate"))
    if sla_dt:
        h = (sla_dt - ref).total_seconds() / 3600
        sla = "venceu há %s" % fmt_dur(-h) if h < 0 else "vence em %s" % fmt_dur(h)
        sla += " (%s)" % sla_dt.astimezone(BRT).strftime("%d/%m/%Y %H:%M")
    else:
        sla = "sem SLA definido"
    achados = []
    if parado_h is not None and parado_h >= 48 and t.get("status") in ("Em atendimento", "Em atendimento - N2", "Aguardando Terceiros"):
        achados.append("Aging: %s sem atualização" % fmt_dur(parado_h))
    if sla_dt and (sla_dt - ref).total_seconds() < 0:
        achados.append("SLA vencido")
    if t.get("category") == "Bug" and t.get("urgency") in ("Alta", "Média"):
        achados.append("Bug de urgência %s: conferir o prazo de repasse ao N2" % t.get("urgency"))
    if t.get("category") == "Melhoria" and not t.get("tags") and t.get("status") == "Refinamento Suporte Melhoria":
        achados.append("Melhoria sem tag: entra na pauta da reunião de alinhamento")
    return {
        "protocolo": t.get("protocol") or "-", "categoria": t.get("category") or "Sem categoria", "urgencia": t.get("urgency") or "não informada",
        "status": t.get("status") or "-", "etapa": etapa_de(t), "parado": fmt_dur(parado_h), "sla": sla,
        "analise": "; ".join(achados) if achados else "Nenhum alerta pelas regras automáticas.",
        "proximo_passo": PROXIMO.get(t.get("status"), "Seguir o fluxo de atendimento conforme o status."),
        "data_hora": agora().strftime("%d/%m/%Y %H:%M"),
    }


def montar_log(modelo, campos):
    texto = modelo
    for k, v in campos.items():
        texto = texto.replace("{" + k + "}", str(v))
    return texto


# ---------------------------------------------------------------- Movidesk
def buscar_chamado(protocolo):
    filtro = "protocol eq '%s'" % re.sub(r"[^0-9A-Za-z_-]", "", protocolo)
    for caminho in ("/tickets", "/tickets/past"):
        r = chamar("GET", caminho, {"$select": CAMPOS, "$filter": filtro, "$top": "1"})
        if r:
            return r[0]
    return None


def ja_tem_log_recente(ticket_id, minutos=60):
    r = chamar("GET", "/tickets", {"id": str(ticket_id), "$select": "id", "$expand": "actions($select=id,type,description,createdDate)"})
    for a in (r or {}).get("actions", []) or []:
        d = parse_dt(a.get("createdDate"))
        if (PREFIXO_LOG in (a.get("description") or "") or "[ANÁLISE IA]" in (a.get("description") or "")) and d and (datetime.now(timezone.utc) - d).total_seconds() < minutos * 60:
            return True
    return False


def gravar_log(ticket_id, texto, tipo, autor_id):
    acao = {"type": int(tipo), "description": texto_html(texto)}
    if str(autor_id or "").strip():
        acao["createdBy"] = {"id": str(autor_id).strip()}
    chamar("PATCH", "/tickets", {"id": str(ticket_id)}, {"actions": [acao]})


def texto_html(texto):
    """Movidesk nao da margem entre <p>: uma linha por <p> e <p><br></p> como linha em branco."""
    esc = lambda x: re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return "".join("<p>%s</p>" % esc(l) if l.strip() else "<p><br></p>" for l in texto.strip().splitlines())


def conferir(ticket_id, texto, tipo):
    r = chamar("GET", "/tickets", {"id": str(ticket_id), "$select": "id", "$expand": "actions($select=id,type,description,createdDate)"})
    acoes = [a for a in ((r or {}).get("actions") or []) if (a.get("description") or "").strip() == texto_html(texto)]
    if not acoes:
        return False, "ação não encontrada ao reler o chamado"
    a = acoes[-1]
    return int(a.get("type", -1)) == int(tipo), "tipo da ação gravada: %s (esperado %s)" % (a.get("type"), tipo)


# ---------------------------------------------------------------- execucao
BUSCA_LIBERADA = False  # a busca automatica so' sera liberada quando o usuario pedir


def analises_horus():
    """Analises feitas com o Horus (sob demanda, no Claude): analises_horus.json {protocolo: {analise, proximo_passo, gerado_em}}."""
    try:
        return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analises_horus.json"), encoding="utf-8"))
    except Exception:
        return {}


def historico_com(rel):
    try:
        antigo = json.load(open(REL_PATH, encoding="utf-8")).get("historico") or []
    except Exception:
        antigo = []
    atual = {"executado_em": rel.get("executado_em"), "modo": rel.get("modo"), "habilitada": rel.get("habilitada"),
             "chamados": [{"protocolo": r.get("protocolo"), "resultado": r.get("resultado")} for r in rel.get("resultados", [])]}
    return ([atual] + antigo)[:30]


def main():
    cfg = json.load(open(CFG_PATH, encoding="utf-8"))
    gravar_pedido = os.environ.get("GRAVAR", "false").strip().lower() == "true"
    rel = {"executado_em": agora().strftime("%Y-%m-%d %H:%M:%S") + " (Brasília)", "habilitada": bool(cfg.get("habilitada")), "modo": cfg.get("modo"),
           "gravar_pedido_no_workflow": gravar_pedido, "resultados": [], "candidatos_novos": [], "avisos": []}
    if not cfg.get("habilitada"):
        rel["avisos"].append("Automação desabilitada na configuração: nada foi lido nem gravado.")
        return salvar(rel)
    gravar = gravar_pedido and cfg.get("modo") == "gravar"
    if cfg.get("modo") == "gravar" and not gravar_pedido:
        rel["avisos"].append("Modo 'gravar' na configuração, mas o workflow foi iniciado sem confirmar a gravação: rodou como simulação.")
    protocolos = [str(p).strip() for p in cfg.get("protocolos_autorizados", []) if str(p).strip()]
    if not protocolos:
        rel["avisos"].append("Nenhum chamado autorizado na configuração.")
    for prot in protocolos:
        item = {"protocolo": prot}
        try:
            t = buscar_chamado(prot)
            if not t:
                item.update(resultado="nao_encontrado")
            else:
                campos = analisar(t)
                h = analises_horus().get(prot)
                if h and h.get("log"):
                    texto = h["log"]
                    item["analise_horus"] = h.get("gerado_em")
                else:
                    texto = montar_log(cfg.get("modelo_log", ""), campos)
                item.update(id=t.get("id"), assunto=t.get("subject"), log=texto)
                if not gravar:
                    item["resultado"] = "simulado"
                elif ja_tem_log_recente(t["id"]):
                    item["resultado"] = "ignorado_duplicado"
                else:
                    gravar_log(t["id"], texto, cfg.get("tipo_acao", 1), cfg.get("autor_id"))
                    ok, detalhe = conferir(t["id"], texto, cfg.get("tipo_acao", 1))
                    item.update(resultado="gravado" if ok else "gravado_tipo_diferente", conferencia=detalhe)
                    if not ok:
                        rel["avisos"].append("ATENÇÃO %s: %s. Confira se o log ficou interno e ajuste tipo_acao." % (prot, detalhe))
        except Exception as e:
            item.update(resultado="erro", erro=mascara(e))
        rel["resultados"].append(item)
    busca = cfg.get("busca_automatica") or {}
    if busca.get("habilitada") and not BUSCA_LIBERADA:
        rel["avisos"].append("A busca automática está desativada por enquanto: nenhum chamado foi procurado, só os protocolos informados foram lidos.")
    elif busca.get("habilitada"):
        try:
            r = chamar("GET", "/tickets", {"$select": "id,protocol,subject,category,urgency,status,createdDate", "$filter": "status eq '%s'" % str(busca.get("status", "Novo")).replace("'", ""),
                                           "$orderby": "id asc", "$top": str(int(busca.get("limite_por_execucao", 5)))})
            rel["candidatos_novos"] = [{"protocolo": x.get("protocol"), "assunto": x.get("subject"), "categoria": x.get("category"), "urgencia": x.get("urgency")} for x in (r or [])]
            rel["avisos"].append("A busca automática só LISTA candidatos. Para atuar num chamado, inclua o protocolo em protocolos_autorizados.")
        except Exception as e:
            rel["avisos"].append("Falha na busca automática: " + mascara(e))
    salvar(rel)


def salvar(rel):
    rel["historico"] = historico_com(rel)
    json.dump(rel, open(REL_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in rel.items() if k != "resultados"}, ensure_ascii=False))
    for it in rel["resultados"]:
        print("-", it.get("protocolo"), it.get("resultado"), it.get("erro", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERRO:", mascara(e))
        sys.exit(1)
