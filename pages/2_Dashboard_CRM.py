import sys
from datetime import datetime, timedelta, date
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.design import get_theme, inject_css, render_header

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN = st.secrets["KOMMO_TOKEN"]
BASE = "https://kommogooden.kommo.com/api/v4"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

PIPELINE_VENDAS = 13777443
STATUS_GANHO = 142
STATUS_PERDIDO = 143

STAGES = {
    106301839: "Novo Lead",
    106301843: "Lead Qualificado",
    106301847: "Proposta Enviada",
    106301851: "Negociação",
    STATUS_GANHO: "Vendas Válidas",
    STATUS_PERDIDO: "Cancelado",
}
FUNNEL_ORDER = [106301839, 106301843, 106301847, 106301851, STATUS_GANHO]

USERS = {
    15299487: "Piero",
    15321431: "Patrícia Guerra",
    15376335: "Priscila Oliveira",
    15376351: "Michele Santos",
    15640059: "Maria Eduarda",
    15696963: "UGAH",
}

VENDEDORES_ATIVOS = {"Patrícia Guerra", "Priscila Oliveira", "Michele Santos"}

CF_EMBARQUE = 1558660
CF_FONTE = 2439154
CF_VEICULO = 1558596


# ── Helpers ───────────────────────────────────────────────────────────────────
def fix_enc(s: str) -> str:
    if not s:
        return s
    try:
        fixed = s.encode("iso-8859-1").decode("utf-8")
        if fixed != s:
            return fixed
    except Exception:
        pass
    return s


def cf_val(lead: dict, field_id: int):
    for cf in lead.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            vals = cf.get("values") or []
            return vals[0]["value"] if vals else None
    return None


def ts_to_dt(ts) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ts)) if ts else None
    except Exception:
        return None


# ── API calls ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_leads() -> list[dict]:
    leads, page = [], 1
    while True:
        r = requests.get(
            f"{BASE}/leads",
            headers=HEADERS,
            params={
                "limit": 250,
                "page": page,
                "with": "custom_fields",
                "filter[pipeline_id]": PIPELINE_VENDAS,
            },
            timeout=15,
        )
        data = r.json()
        batch = data.get("_embedded", {}).get("leads", [])
        leads.extend(batch)
        if page >= (data.get("_page_count") or 1) or not batch:
            break
        page += 1
    return leads


# ── Build DataFrame ───────────────────────────────────────────────────────────
def build_df(leads: list[dict]) -> pd.DataFrame:
    rows = []
    for ld in leads:
        embarque_dt = ts_to_dt(cf_val(ld, CF_EMBARQUE))
        fonte_raw = cf_val(ld, CF_FONTE)
        veiculo_raw = cf_val(ld, CF_VEICULO)
        rows.append(
            {
                "id": ld["id"],
                "nome": fix_enc(ld.get("name") or ""),
                "valor": float(ld.get("price") or 0),
                "status_id": ld.get("status_id"),
                "vendedor_id": ld.get("responsible_user_id"),
                "vendedor": USERS.get(ld.get("responsible_user_id"), "Outro"),
                "criado_em": ts_to_dt(ld.get("created_at")),
                "fechado_em": ts_to_dt(ld.get("closed_at")),
                "embarque_em": embarque_dt,
                "fonte": fix_enc(fonte_raw) if fonte_raw else "Não informado",
                "veiculo": fix_enc(veiculo_raw) if veiculo_raw else "Não informado",
            }
        )
    return pd.DataFrame(rows)


def fmt_brl(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard CRM — Gooden",
    page_icon="📊",
    layout="wide",
)
inject_css()

# Override container width for dashboard layout
st.markdown(
    "<style>.block-container { max-width: 1280px !important; }</style>",
    unsafe_allow_html=True,
)

render_header("Dashboard CRM", "Kommo · Métricas em tempo real", page_key="dashboard")

c = get_theme()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="g-section-label">Filtros</div>', unsafe_allow_html=True
    )

    periodo = st.selectbox(
        "Período",
        ["Todos", "Mês atual", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Este ano", "Personalizado"],
    )

    today = date.today()
    sem_filtro_data = False
    if periodo == "Todos":
        data_ini = date(2020, 1, 1)
        data_fim = today
        sem_filtro_data = True
    elif periodo == "Mês atual":
        data_ini = date(today.year, today.month, 1)
        data_fim = today
    elif periodo == "Últimos 7 dias":
        data_ini = today - timedelta(days=7)
        data_fim = today
    elif periodo == "Últimos 30 dias":
        data_ini = today - timedelta(days=30)
        data_fim = today
    elif periodo == "Últimos 90 dias":
        data_ini = today - timedelta(days=90)
        data_fim = today
    elif periodo == "Este ano":
        data_ini = date(today.year, 1, 1)
        data_fim = today
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            data_ini = st.date_input("De", value=date(today.year, today.month, 1), format="DD/MM/YYYY")
        with col_b:
            data_fim = st.date_input("Até", value=today, format="DD/MM/YYYY")

    tipo_data = st.radio(
        "Filtrar por",
        ["Data de criação", "Data do serviço (embarque)"],
        help="Data de criação = quando o lead entrou. Data do serviço = data da viagem.",
    )

    vendedor_opcoes = ["Todos"] + sorted(VENDEDORES_ATIVOS)
    vendedor_sel = st.selectbox("Vendedor", vendedor_opcoes)

    fonte_opcoes = [
        "Todas",
        "Base Gooden - Whatsapp",
        "Base VSI - Whatsapp",
        "Instagram",
        "Facebook",
        "Anuncio Google",
        "Site",
        "Indicação",
        "Motorista",
        "Telefone",
        "Linkedin",
        "Outros",
    ]
    fonte_sel = st.selectbox("Canal / Fonte", fonte_opcoes)

    if st.button("Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f'<div style="font-size:0.72rem;color:{c["text_faint"]};margin-top:12px">'
        f"Cache: 5 min · Última atualização: {datetime.now().strftime('%H:%M:%S')}</div>",
        unsafe_allow_html=True,
    )

# ── Load & filter data ────────────────────────────────────────────────────────
with st.spinner("Carregando dados do Kommo…"):
    raw_leads = load_leads()

df_all = build_df(raw_leads)
df_all = df_all[df_all["vendedor"].isin(VENDEDORES_ATIVOS)]

# Date filter
dt_ini = datetime.combine(data_ini, datetime.min.time())
dt_fim = datetime.combine(data_fim, datetime.max.time())

if sem_filtro_data:
    df = df_all.copy()
elif tipo_data == "Data de criação":
    df = df_all[df_all["criado_em"].between(dt_ini, dt_fim)]
else:
    df = df_all[df_all["embarque_em"].between(dt_ini, dt_fim)]

# Salesperson filter
if vendedor_sel != "Todos":
    df = df[df["vendedor"] == vendedor_sel]

# Source filter
if fonte_sel != "Todas":
    df = df[df["fonte"] == fonte_sel]

# Subsets
now = datetime.now()
df_ganho = df[df["status_id"] == STATUS_GANHO]
df_perdido = df[df["status_id"] == STATUS_PERDIDO]
df_concluido = df_ganho[df_ganho["embarque_em"].notna() & (df_ganho["embarque_em"] < now)]
df_pendente = df_ganho[df_ganho["embarque_em"].isna() | (df_ganho["embarque_em"] >= now)]
df_orcamento = df[df["status_id"].isin([106301847, 106301851, STATUS_GANHO, STATUS_PERDIDO])]

total_ganho = df_ganho["valor"].sum()
total_concluido = df_concluido["valor"].sum()
total_cancelado = df_perdido["valor"].sum()
total_orcado = df_orcamento[df_orcamento["status_id"] != STATUS_PERDIDO]["valor"].sum()

n_ganho = len(df_ganho)
n_concluido = len(df_concluido)
n_cancelado = len(df_perdido)
n_orcamento = len(df_orcamento[df_orcamento["status_id"] != STATUS_PERDIDO])

taxa = (n_ganho / n_orcamento * 100) if n_orcamento > 0 else 0
ticket = (total_ganho / n_ganho) if n_ganho > 0 else 0


# ── KPI Cards HTML helper ─────────────────────────────────────────────────────
def kpi_card(label: str, count: int, value: float | None, color: str, pct: float | None = None) -> str:
    pct_html = (
        f'<div style="font-family:Geologica,sans-serif;font-size:0.78rem;'
        f'color:{color};font-weight:700;margin-top:2px">{pct:.1f}%</div>'
        if pct is not None
        else ""
    )
    val_html = (
        f'<div style="font-family:Geologica,sans-serif;font-size:1.55rem;font-weight:900;'
        f'color:{c["text_primary"]};letter-spacing:-0.5px;line-height:1.1">{fmt_brl(value)}</div>'
        if value is not None
        else ""
    )
    bar_pct = min(pct or 0, 100)
    bar_html = (
        f'<div style="height:3px;background:{c["border"]};border-radius:2px;margin-top:10px">'
        f'<div style="width:{bar_pct:.0f}%;height:100%;background:{color};border-radius:2px"></div></div>'
        if pct is not None
        else ""
    )
    return f"""
    <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
        padding:18px 20px;box-shadow:0 2px 12px {c['shadow']}">
        <div style="font-family:Geologica,sans-serif;font-size:0.72rem;font-weight:600;
            letter-spacing:0.1em;text-transform:uppercase;color:{c['text_faint']};margin-bottom:6px">
            {label}</div>
        <div style="display:flex;align-items:baseline;gap:10px">
            <div style="font-family:Geologica,sans-serif;font-size:2.2rem;font-weight:900;
                color:{color};letter-spacing:-1px;line-height:1">{count}</div>
            {pct_html}
        </div>
        {val_html}
        {bar_html}
    </div>"""


def metric_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div style="background:{c['surface']};border:1px solid {c['border']};border-radius:14px;
        padding:18px 20px;box-shadow:0 2px 12px {c['shadow']}">
        <div style="font-family:Geologica,sans-serif;font-size:0.72rem;font-weight:600;
            letter-spacing:0.1em;text-transform:uppercase;color:{c['text_faint']};margin-bottom:6px">
            {label}</div>
        <div style="font-family:Geologica,sans-serif;font-size:1.7rem;font-weight:900;
            color:{c['text_primary']};letter-spacing:-0.5px">{value}</div>
        {f'<div style="font-size:0.78rem;color:{c["text_muted"]};margin-top:2px">{sub}</div>' if sub else ""}
    </div>"""


# ── KPI Row 1 ─────────────────────────────────────────────────────────────────
periodo_label = "Todos os dados" if sem_filtro_data else f'{data_ini.strftime("%d/%m/%Y")} – {data_fim.strftime("%d/%m/%Y")}'
st.markdown(
    f'<div class="g-section-label">Visão Geral · {periodo_label}</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.html(kpi_card("Vendas Válidas", n_ganho, total_ganho, c["success"]))
with c2:
    st.html(kpi_card("Viagens Concluídas", n_concluido, total_concluido, c["accent"]))
with c3:
    st.html(kpi_card("Viagens Pendentes", len(df_pendente), df_pendente["valor"].sum(), c["warning"]))
with c4:
    st.html(kpi_card("Canceladas", n_cancelado, total_cancelado, c["error"]))
with c5:
    st.html(metric_card("Taxa de Conversão", f"{taxa:.1f}%", f"{n_ganho} ganho / {n_orcamento} orçamentos"))

# ── KPI Row 2 ─────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
d1, d2, d3, d4, d5 = st.columns(5)
with d1:
    st.html(metric_card("Ticket Médio", fmt_brl(ticket)))
with d2:
    st.html(metric_card("Total Orçado", fmt_brl(total_orcado), f"{n_orcamento} propostas"))
with d3:
    n_novos = len(df[df["status_id"] == 106301839])
    st.html(metric_card("Novos Leads", str(n_novos)))
with d4:
    n_qualif = len(df[df["status_id"] == 106301843])
    st.html(metric_card("Qualificados", str(n_qualif)))
with d5:
    n_negoc = len(df[df["status_id"] == 106301851])
    st.html(metric_card("Em Negociação", str(n_negoc)))

st.divider()

# ── Charts Row 1: Funil + Por Vendedor ───────────────────────────────────────
col_funil, col_vend = st.columns([1, 1], gap="large")

with col_funil:
    st.markdown('<div class="g-section-label">Funil de Conversão</div>', unsafe_allow_html=True)

    funil_data = []
    for sid in FUNNEL_ORDER:
        count = len(df[df["status_id"] == sid])
        funil_data.append({"Etapa": STAGES[sid], "Leads": count, "order": FUNNEL_ORDER.index(sid)})

    df_funil = pd.DataFrame(funil_data).sort_values("order", ascending=False)

    chart_funil = (
        alt.Chart(df_funil)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            y=alt.Y("Etapa:N", sort=None, axis=alt.Axis(labelColor=c["text_secondary"], labelFontSize=12)),
            x=alt.X("Leads:Q", axis=alt.Axis(labelColor=c["text_muted"], labelFontSize=11, grid=False)),
            color=alt.value(c["accent"]),
            tooltip=["Etapa", "Leads"],
        )
        .properties(height=220, background="transparent")
        .configure_axis(domainColor=c["border"], tickColor=c["border"])
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart_funil, use_container_width=True)

with col_vend:
    st.markdown('<div class="g-section-label">Vendas Válidas por Vendedor</div>', unsafe_allow_html=True)

    if len(df_ganho) > 0:
        df_vend = (
            df_ganho.groupby("vendedor")
            .agg(Vendas=("id", "count"), Valor=("valor", "sum"))
            .reset_index()
            .sort_values("Vendas", ascending=True)
        )
        chart_vend = (
            alt.Chart(df_vend)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
            .encode(
                y=alt.Y("vendedor:N", sort=None, title="Vendedor",
                         axis=alt.Axis(labelColor=c["text_secondary"], labelFontSize=12)),
                x=alt.X("Vendas:Q", axis=alt.Axis(labelColor=c["text_muted"], labelFontSize=11, grid=False)),
                color=alt.value(c["success"]),
                tooltip=["vendedor", "Vendas", alt.Tooltip("Valor:Q", format=",.2f", title="Valor R$")],
            )
            .properties(height=220, background="transparent")
            .configure_axis(domainColor=c["border"], tickColor=c["border"])
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart_vend, use_container_width=True)
    else:
        st.info("Sem vendas no período selecionado.")

# ── Charts Row 2: Canais + Timeline ──────────────────────────────────────────
col_canal, col_time = st.columns([1, 1], gap="large")

with col_canal:
    st.markdown('<div class="g-section-label">Canais de Origem</div>', unsafe_allow_html=True)

    df_fonte = (
        df.groupby("fonte")
        .agg(Leads=("id", "count"))
        .reset_index()
        .sort_values("Leads", ascending=True)
        .tail(10)
    )

    chart_fonte = (
        alt.Chart(df_fonte)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            y=alt.Y("fonte:N", sort=None, title="Canal",
                     axis=alt.Axis(labelColor=c["text_secondary"], labelFontSize=11)),
            x=alt.X("Leads:Q", axis=alt.Axis(labelColor=c["text_muted"], labelFontSize=11, grid=False)),
            color=alt.value(c["accent_btn"]),
            tooltip=["fonte", "Leads"],
        )
        .properties(height=250, background="transparent")
        .configure_axis(domainColor=c["border"], tickColor=c["border"])
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart_fonte, use_container_width=True)

with col_time:
    st.markdown('<div class="g-section-label">Leads ao Longo do Tempo</div>', unsafe_allow_html=True)

    df_time = df[df["criado_em"].notna()].copy()
    if len(df_time) > 0:
        df_time["semana"] = df_time["criado_em"].dt.to_period("W").dt.start_time
        df_weekly = (
            df_time.groupby(["semana", "status_id"])
            .size()
            .reset_index(name="count")
        )
        df_weekly["status"] = df_weekly["status_id"].map(
            lambda x: "Ganho" if x == STATUS_GANHO else ("Perdido" if x == STATUS_PERDIDO else "Ativo")
        )
        df_weekly_agg = df_weekly.groupby(["semana", "status"])["count"].sum().reset_index()

        color_map = {"Ganho": c["success"], "Ativo": c["accent"], "Perdido": c["error"]}

        chart_time = (
            alt.Chart(df_weekly_agg)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X("semana:T", title="Semana", axis=alt.Axis(labelColor=c["text_muted"], format="%d/%m")),
                y=alt.Y("count:Q", title="Leads", axis=alt.Axis(labelColor=c["text_muted"], grid=False)),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(
                        domain=list(color_map.keys()),
                        range=list(color_map.values()),
                    ),
                    legend=alt.Legend(labelColor=c["text_secondary"], titleColor=c["text_muted"]),
                ),
                tooltip=["semana:T", "status", "count"],
            )
            .properties(height=250, background="transparent")
            .configure_axis(domainColor=c["border"], tickColor=c["border"])
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart_time, use_container_width=True)
    else:
        st.info("Sem dados no período.")

st.divider()

# ── Próximas Viagens ──────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Próximas Viagens (Reservas Pendentes)</div>', unsafe_allow_html=True)

df_prox = df_pendente[df_pendente["embarque_em"].notna()].sort_values("embarque_em")

if len(df_prox) > 0:
    df_prox_show = df_prox[["nome", "embarque_em", "valor", "vendedor", "veiculo"]].copy()
    df_prox_show["embarque_em"] = df_prox_show["embarque_em"].dt.strftime("%d/%m/%Y %H:%M")
    df_prox_show["valor"] = df_prox_show["valor"].apply(fmt_brl)
    df_prox_show.columns = ["Cliente", "Embarque", "Valor", "Vendedor", "Veículo"]
    st.dataframe(df_prox_show, use_container_width=True, hide_index=True)
else:
    st.markdown(
        f"""<div class="g-empty">
            <div class="g-empty-icon">🗓️</div>
            <div class="g-empty-title">Nenhuma viagem pendente no período</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Conversão Detalhada por Vendedor ──────────────────────────────────────────
st.markdown('<div class="g-section-label">Taxa de Conversão por Vendedor</div>', unsafe_allow_html=True)

vendedores_data = []
for vend in sorted(VENDEDORES_ATIVOS):
    df_v = df[df["vendedor"] == vend]
    df_v_orc = df_v[df_v["status_id"].isin([106301847, 106301851, STATUS_GANHO, STATUS_PERDIDO])]
    df_v_ganho = df_v[df_v["status_id"] == STATUS_GANHO]
    n_orc = len(df_v_orc[df_v_orc["status_id"] != STATUS_PERDIDO])
    n_g = len(df_v_ganho)
    t = (n_g / n_orc * 100) if n_orc > 0 else 0
    ticket_v = df_v_ganho["valor"].mean() if n_g > 0 else 0
    vendedores_data.append(
        {
            "Vendedor": vend,
            "Leads": len(df_v),
            "Orçamentos": n_orc,
            "Vendas": n_g,
            "Conversão": f"{t:.1f}%",
            "Ticket Médio": fmt_brl(ticket_v),
            "Total": fmt_brl(df_v_ganho["valor"].sum()),
        }
    )

df_vend_table = pd.DataFrame(vendedores_data)
st.dataframe(df_vend_table, use_container_width=True, hide_index=True)

st.markdown(
    f'<div class="g-footer">Gooden · Dashboard CRM · Dados via Kommo API · Cache 5 min</div>',
    unsafe_allow_html=True,
)
