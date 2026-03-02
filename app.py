"""
════════════════════════════════════════════════════════════════════
  RASTREAMENTO KPIs — APLICAÇÃO WEB
  Flask + Python  |  Multi-página com observações
════════════════════════════════════════════════════════════════════
"""

import os
import re
import json
import glob
import pandas as pd
from datetime import datetime
from pathlib import Path
from flask import (Flask, request, render_template,
                   redirect, url_for, jsonify)

app = Flask(__name__)
app.secret_key = "rastreamento_truss_2026"

UPLOAD_FOLDER = "uploads"
DATA_FILE     = os.path.join(UPLOAD_FOLDER, "current_data.json")
OBS_FILE      = os.path.join(UPLOAD_FOLDER, "observacoes.json")

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────────
MESES_PTBR = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março",    4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho",     8:"Agosto",
    9:"Setembro",10:"Outubro",  11:"Novembro", 12:"Dezembro",
}
MESES_ABREV = {
    1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
    7:"Jul", 8:"Ago", 9:"Set", 10:"Out",11:"Nov", 12:"Dez",
}

# Tipos de observação com metadados visuais
TIPOS_OBS = {
    "manutencao":    {"label": "Manutenção",           "cor": "amber",  "cobrar": False},
    "cliente":       {"label": "Problema do cliente",  "cor": "orange", "cobrar": False},
    "equipamento":   {"label": "Falha no equipamento", "cor": "red",    "cobrar": True},
    "sem_sinal":     {"label": "Sem sinal/cobertura",  "cor": "blue",   "cobrar": False},
    "desativado":    {"label": "Ativo desativado",     "cor": "muted",  "cobrar": False},
    "outro":         {"label": "Outro",                "cor": "cyan",   "cobrar": True},
}

# ──────────────────────────────────────────────────────────────────
#  PERSISTÊNCIA DE DADOS
# ──────────────────────────────────────────────────────────────────

def save_current_data(data: dict):
    """Salva o resultado do processamento das planilhas em JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_current_data() -> dict | None:
    """Carrega os dados do último processamento. Retorna None se não existe."""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_observacoes() -> dict:
    """Carrega o arquivo de observações dos ativos sem comunicação."""
    if not os.path.exists(OBS_FILE):
        return {}
    with open(OBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_observacoes(obs: dict):
    """Salva o arquivo de observações."""
    with open(OBS_FILE, "w", encoding="utf-8") as f:
        json.dump(obs, f, ensure_ascii=False, indent=2)


def obs_key(cliente: str, nome_ativo: str, mes: int, ano: int) -> str:
    """Gera chave única para identificar a observação de um ativo em um mês."""
    slug = re.sub(r'[^a-zA-Z0-9]', '_', nome_ativo)
    return f"{cliente}__{slug}__{mes}_{ano}"


# ──────────────────────────────────────────────────────────────────
#  CONTEXT PROCESSOR — injeta dados de navegação em todos os templates
# ──────────────────────────────────────────────────────────────────

@app.context_processor
def inject_nav():
    """Disponibiliza variáveis de navegação em todos os templates automaticamente."""
    dados = load_current_data()
    if dados:
        total_no_comm = sum(c["sem_comunicacao"] for c in dados["clientes"].values())
        return {
            "nav_tem_dados":   True,
            "nav_sem_comm":    total_no_comm,
            "nav_mes_nome":    MESES_PTBR.get(dados["mes"], ""),
            "nav_ano":         dados["ano"],
        }
    return {
        "nav_tem_dados": False,
        "nav_sem_comm":  0,
        "nav_mes_nome":  "",
        "nav_ano":       "",
    }


# ──────────────────────────────────────────────────────────────────
#  PROCESSAMENTO DOS DADOS
# ──────────────────────────────────────────────────────────────────

def extrair_data(texto):
    if not isinstance(texto, str):
        return None
    match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})", texto.strip())
    if match:
        d, m, a, h, mi, s = match.groups()
        try:
            return datetime(int(a), int(m), int(d), int(h), int(mi), int(s))
        except ValueError:
            return None
    return None


def ler_planilha(caminho):
    df = pd.read_excel(caminho, dtype=str)
    mapa = {
        "nome": "Nome",
        "id": "ID",
        "últimos dados processados": "UltimoDado",
        "ultimos dados processados": "UltimoDado",
        "último dado": "UltimoDado",
        "último dado processado": "UltimoDado",
    }
    df = df.rename(columns={
        c: mapa[c.strip().lower()]
        for c in df.columns if c.strip().lower() in mapa
    })
    df = df.dropna(subset=["Nome"])
    df["Nome"]       = df["Nome"].astype(str).str.strip()
    df["ID"]         = df.get("ID", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    df["UltimoDado"] = df.get("UltimoDado", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    df["DataComunicacao"] = df["UltimoDado"].apply(extrair_data)
    return df[["Nome", "ID", "UltimoDado", "DataComunicacao"]]


def calcular_status(df, mes, ano):
    def status(data):
        if data and data.month == mes and data.year == ano:
            return "Comunicante"
        return "Sem Comunicação"
    df = df.copy()
    df["Status"] = df["DataComunicacao"].apply(status)
    return df


def calcular_kpis(clientes):
    kpis = {"total": 0, "comunicantes": 0, "sem_comunicacao": 0, "taxa": 0.0, "clientes": {}}
    for nome, df in clientes.items():
        total   = len(df)
        comm    = int((df["Status"] == "Comunicante").sum())
        no_comm = total - comm
        taxa    = comm / total if total > 0 else 0.0
        kpis["total"]           += total
        kpis["comunicantes"]    += comm
        kpis["sem_comunicacao"] += no_comm
        kpis["clientes"][nome] = {
            "total": total, "comunicantes": comm,
            "sem_comunicacao": no_comm, "taxa": taxa,
            "df_comm":    df[df["Status"] == "Comunicante"].reset_index(drop=True),
            "df_no_comm": df[df["Status"] == "Sem Comunicação"].reset_index(drop=True),
        }
    t = kpis["total"]
    kpis["taxa"] = kpis["comunicantes"] / t if t > 0 else 0.0
    return kpis


def serializar_dados(kpis, clientes, mes, ano):
    """Converte kpis + DataFrames para formato JSON-serializável e persistível."""
    dados = {
        "mes":            mes,
        "ano":            ano,
        "total":          kpis["total"],
        "comunicantes":   kpis["comunicantes"],
        "sem_comunicacao":kpis["sem_comunicacao"],
        "taxa":           round(kpis["taxa"] * 100, 1),
        "nomes":          list(clientes.keys()),
        "clientes":       {}
    }
    for nome, c in kpis["clientes"].items():
        dados["clientes"][nome] = {
            "total":          c["total"],
            "comunicantes":   c["comunicantes"],
            "sem_comunicacao":c["sem_comunicacao"],
            "taxa":           round(c["taxa"] * 100, 1),
            "lista_comm":     c["df_comm"][["Nome","ID","UltimoDado"]].to_dict("records"),
            "lista_no_comm":  c["df_no_comm"][["Nome","ID","UltimoDado"]].to_dict("records"),
        }
    return dados


def enriquecer_com_obs(dados, observacoes):
    """
    Adiciona dados de observação em cada ativo sem comunicação.
    Modifica uma cópia dos dados — não persiste nada.
    """
    mes = dados["mes"]
    ano = dados["ano"]
    for nome_cliente, c in dados["clientes"].items():
        for ativo in c["lista_no_comm"]:
            key = obs_key(nome_cliente, ativo["Nome"], mes, ano)
            obs = observacoes.get(key, {})
            tipo = obs.get("tipo", "")
            tipo_meta = TIPOS_OBS.get(tipo, {})
            ativo["obs_key"]    = key
            ativo["obs_texto"]  = obs.get("texto", "")
            ativo["obs_tipo"]   = tipo
            ativo["obs_label"]  = tipo_meta.get("label", "")
            ativo["obs_cor"]    = tipo_meta.get("cor", "")
            # cobrar: usa o valor salvo; se não há obs, default = True
            ativo["obs_cobrar"] = obs.get("cobrar", True) if tipo else True
    return dados


# ──────────────────────────────────────────────────────────────────
#  ROTAS
# ──────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Página inicial: dashboard se houver dados, formulário de upload se não houver."""
    dados = load_current_data()
    if dados is None:
        hoje = datetime.now()
        return render_template("index.html",
                               mes_atual=hoje.month,
                               ano_atual=hoje.year,
                               meses=MESES_PTBR,
                               sem_dados=True)

    mes_nome  = MESES_PTBR.get(dados["mes"], str(dados["mes"]))
    mes_abrev = MESES_ABREV.get(dados["mes"], str(dados["mes"]))

    return render_template("dashboard.html",
        dados=dados,
        mes_nome=mes_nome,
        mes_abrev=mes_abrev,
        pagina="dashboard",
    )


@app.route("/sem-comunicacao", methods=["GET"])
def sem_comunicacao():
    """Página de ativos sem comunicação com gerenciamento de observações."""
    dados = load_current_data()
    if dados is None:
        return redirect(url_for("index"))

    import copy
    dados_enriq = enriquecer_com_obs(copy.deepcopy(dados), load_observacoes())
    mes_nome    = MESES_PTBR.get(dados["mes"], str(dados["mes"]))

    return render_template("sem_comunicacao.html",
        dados=dados_enriq,
        mes_nome=mes_nome,
        tipos_obs=TIPOS_OBS,
        pagina="sem_comunicacao",
    )


@app.route("/cobranca", methods=["GET"])
def cobranca():
    """Página de cobrança mensal com inputs de valor por ativo."""
    dados = load_current_data()
    if dados is None:
        return redirect(url_for("index"))

    import copy
    dados_enriq = enriquecer_com_obs(copy.deepcopy(dados), load_observacoes())
    mes_nome    = MESES_PTBR.get(dados["mes"], str(dados["mes"]))

    return render_template("cobranca.html",
        dados=dados_enriq,
        mes_nome=mes_nome,
        pagina="cobranca",
    )


@app.route("/nova-planilha", methods=["GET"])
def nova_planilha():
    """Formulário de upload para gerar um novo relatório."""
    hoje = datetime.now()
    return render_template("index.html",
                           mes_atual=hoje.month,
                           ano_atual=hoje.year,
                           meses=MESES_PTBR,
                           sem_dados=False)


@app.route("/gerar", methods=["POST"])
def gerar():
    """Recebe os arquivos Excel, processa e salva o resultado."""
    mes      = int(request.form.get("mes", datetime.now().month))
    ano      = int(request.form.get("ano", datetime.now().year))
    arquivos = request.files.getlist("planilhas")

    if not arquivos or all(f.filename == "" for f in arquivos):
        return render_template("index.html",
                               erro="Nenhum arquivo enviado.",
                               mes_atual=mes, ano_atual=ano,
                               meses=MESES_PTBR, sem_dados=False)

    clientes = {}
    erros    = []

    for f in arquivos:
        if not f.filename.endswith(".xlsx"):
            erros.append(f"'{f.filename}' não é um arquivo .xlsx")
            continue
        nome_cliente = Path(f.filename).stem
        caminho      = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(caminho)
        try:
            df = ler_planilha(caminho)
            df = calcular_status(df, mes, ano)
            clientes[nome_cliente] = df
        except Exception as e:
            erros.append(f"Erro em '{f.filename}': {str(e)}")

    if not clientes:
        return render_template("index.html",
                               erro="Nenhuma planilha válida. " + " | ".join(erros),
                               mes_atual=mes, ano_atual=ano,
                               meses=MESES_PTBR, sem_dados=False)

    kpis  = calcular_kpis(clientes)
    dados = serializar_dados(kpis, clientes, mes, ano)
    save_current_data(dados)

    return redirect(url_for("index"))


# ── API: salvar observação (chamada via fetch/AJAX do front-end) ───

@app.route("/api/observacao", methods=["POST"])
def salvar_observacao():
    """
    Recebe JSON com { key, texto, tipo, cobrar } e persiste em observacoes.json.
    Retorna { ok: true } em caso de sucesso.
    """
    body = request.get_json()
    if not body:
        return jsonify({"ok": False, "erro": "Dados inválidos"}), 400

    key    = body.get("key", "").strip()
    texto  = body.get("texto", "").strip()
    tipo   = body.get("tipo", "").strip()
    cobrar = body.get("cobrar", True)

    if not key:
        return jsonify({"ok": False, "erro": "Chave inválida"}), 400

    obs = load_observacoes()

    if texto or tipo:
        obs[key] = {"texto": texto, "tipo": tipo, "cobrar": cobrar}
    else:
        # Se apagou tudo, remove a entrada para não poluir o arquivo
        obs.pop(key, None)

    save_observacoes(obs)
    return jsonify({"ok": True})


# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
