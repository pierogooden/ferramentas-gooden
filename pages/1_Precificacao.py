import math
import requests
from datetime import date, datetime
from urllib.parse import quote

import streamlit as st

st.set_page_config(
    page_title="Gooden Tool Kit · Precificação",
    page_icon="🚌",
    layout="centered",
)

# ── Design System Gooden ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geologica:wght@300;400;600;700;900&family=Abhaya+Libre:wght@400;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Abhaya Libre', Georgia, serif;
    background-color: #FAFBFF !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 800px !important; }

.g-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 0 24px 0; margin-bottom: 8px; border-bottom: 1.5px solid #E8EAFF;
}
.g-logo {
    font-family: 'Geologica', sans-serif; font-weight: 900; font-size: 2rem;
    color: #020066; letter-spacing: -1.5px; line-height: 1;
}
.g-logo span {
    display: inline-block; width: 6px; height: 6px; background: #5450FF;
    border-radius: 50%; margin-left: 3px; vertical-align: super;
}
.g-header-right { text-align: right; }
.g-header-title {
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.85rem;
    color: #020066; letter-spacing: 0.02em;
}
.g-header-sub {
    font-family: 'Abhaya Libre', serif; font-size: 0.78rem; color: #ACB0F8; margin-top: 1px;
}
.g-section-label {
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: #ACB0F8;
    margin-bottom: 10px; margin-top: 24px;
}
.g-addr-chip {
    background: #F0F1FF; border-radius: 8px; padding: 8px 12px;
    font-family: 'Abhaya Libre', serif; font-size: 0.88rem; color: #3D3F8F;
    margin-top: 4px; display: flex; align-items: flex-start; gap: 6px;
    border: 1px solid #E0E2FF;
}
.g-addr-chip-icon { flex-shrink: 0; margin-top: 1px; }
.g-km-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #EAFFF2; border: 1px solid #86EFAC; border-radius: 8px;
    padding: 8px 14px; font-family: 'Geologica', sans-serif; font-weight: 700;
    font-size: 0.88rem; color: #166534; margin-top: 4px;
}
.g-result-price {
    font-family: 'Geologica', sans-serif; font-weight: 900; font-size: 2.6rem;
    letter-spacing: -1px; line-height: 1.1; color: #020066;
}
.g-result-price.red { color: #D93025; }
.g-result-label {
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: #ACB0F8; margin-bottom: 4px;
}
.g-margin-ok { font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 1.1rem; color: #1B7F3A; }
.g-margin-warn { font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 1.1rem; color: #D93025; }
.g-breakdown-row {
    display: flex; justify-content: space-between; padding: 6px 0;
    border-bottom: 1px solid #F0F1FF;
    font-family: 'Abhaya Libre', serif; font-size: 0.95rem; color: #3D3F8F;
}
.g-breakdown-row:last-child { border-bottom: none; }
.g-breakdown-label { color: #8386C8; }
.g-breakdown-value { font-weight: 600; color: #020066; }
.g-breakdown-value.negative { color: #D93025; }
.g-badge-type {
    font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 0.68rem;
    letter-spacing: 0.06em; padding: 4px 12px; border-radius: 20px;
    display: inline-block; margin-bottom: 16px;
}
.badge-fds { background: #FFF0F0; color: #D93025; }
.badge-semana { background: #F0F1FF; color: #5450FF; }
.g-link-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #F4F5FF; border: 1px solid #C4C7F8; border-radius: 8px;
    padding: 8px 14px; font-family: 'Geologica', sans-serif; font-weight: 600;
    font-size: 0.78rem; color: #5450FF; text-decoration: none; transition: all 0.15s;
}
.stButton > button {
    background: #020066 !important; color: white !important; border: none !important;
    border-radius: 10px !important; font-family: 'Geologica', sans-serif !important;
    font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.03em !important;
    padding: 10px 24px !important; width: 100% !important; transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(2,0,102,0.18) !important;
}
.stButton > button:hover {
    background: #3500D8 !important; box-shadow: 0 4px 16px rgba(53,0,216,0.28) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stExpander"] {
    background: white !important; border: 1px solid #EAECFF !important;
    border-radius: 14px !important; box-shadow: 0 2px 16px rgba(84,80,255,0.06) !important;
    overflow: hidden !important; margin-top: 16px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Geologica', sans-serif !important; font-weight: 700 !important;
    color: #020066 !important; font-size: 0.88rem !important; padding: 14px 20px !important;
}
hr[data-testid="stDivider"] { border-color: #EAECFF !important; margin: 20px 0 !important; }
.g-footer {
    text-align: center; margin-top: 48px; padding-top: 20px; border-top: 1px solid #EAECFF;
    font-family: 'Geologica', sans-serif; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: #D0D2F0;
}
</style>
""", unsafe_allow_html=True)

# ── Constantes ───────────────────────────────────────────────────────────────
COMISSOES_IMPOSTOS = 0.2765

VEICULOS = {
    "Ônibus Executivo - Motor Traseiro": 3.12,
    "Ônibus Convencional - Motor Traseiro": 2.78,
    "Ônibus Executivo - Motor Dianteiro": 2.65,
    "Ônibus Convencional - Motor Dianteiro": 2.48,
    "Microônibus Executivo": 1.82,
    "Microônibus Convencional": 1.73,
}

MARGEM_MIN_SEMANA = 700.0
MARGEM_MIN_FDS = 1000.0

DETALHAMENTO_COMISSOES = {
    "Comissão de Vendas (2%)": 0.02,
    "Comissão do Motorista (10%)": 0.10,
    "PIS (0,65%)": 0.0065,
    "COFINS (3%)": 0.03,
    "ICMS (12%)": 0.12,
}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"


# ── Geocoding & Rota ─────────────────────────────────────────────────────────
def buscar_enderecos(query: str) -> list[dict]:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 6, "countrycodes": "br", "addressdetails": 1},
            headers={"User-Agent": "GoodenToolKit/1.0 (contato@gooden.com.br)"},
            timeout=6,
        )
        return [
            {"nome": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"])}
            for r in resp.json()
        ]
    except Exception:
        return []


def calcular_km_rota(coords: list[tuple[float, float]]) -> float | None:
    try:
        waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
        resp = requests.get(
            f"{OSRM_URL}/{waypoints}",
            params={"overview": "false"},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == "Ok":
            return round(data["routes"][0]["distance"] / 1000, 1)
        return None
    except Exception:
        return None


# ── Componente de endereço ───────────────────────────────────────────────────
def campo_endereco(label: str, key: str, placeholder: str = "Ex: Av. Paulista, 1000, São Paulo") -> dict | None:
    for k, v in [
        (f"addr_{key}", None),
        (f"addr_{key}_sugs", []),
        (f"addr_{key}_erro", False),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown(
        f'<div style="font-family:Geologica,sans-serif;font-weight:600;font-size:0.8rem;'
        f'color:#3D3F8F;margin-bottom:4px;">{label}</div>',
        unsafe_allow_html=True,
    )

    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        texto = st.text_input(
            label, placeholder=placeholder,
            key=f"_ti_{key}", label_visibility="collapsed",
        )
    with col_btn:
        st.markdown("<div style='margin-top:4px'>", unsafe_allow_html=True)
        buscar_clicked = st.button("🔍", key=f"_bb_{key}", help="Buscar endereço", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if buscar_clicked:
        if texto.strip():
            with st.spinner("Buscando..."):
                sugs = buscar_enderecos(texto)
            if sugs:
                st.session_state[f"addr_{key}_sugs"] = sugs
                st.session_state[f"addr_{key}"] = None
                st.session_state[f"addr_{key}_erro"] = False
            else:
                st.session_state[f"addr_{key}_sugs"] = []
                st.session_state[f"addr_{key}_erro"] = True
            st.rerun()

    if st.session_state[f"addr_{key}_erro"]:
        st.markdown(
            '<div style="font-family:Geologica,sans-serif;font-size:0.75rem;color:#D93025;margin-top:2px;">'
            '⚠️ Nenhum resultado encontrado. Tente um endereço mais específico.</div>',
            unsafe_allow_html=True,
        )

    sugs = st.session_state[f"addr_{key}_sugs"]
    if sugs:
        nomes = [s["nome"] for s in sugs]
        escolha = st.selectbox(
            "Resultados", ["— selecione o endereço —"] + nomes,
            key=f"_sel_{key}", label_visibility="collapsed",
        )
        if escolha != "— selecione o endereço —":
            idx = nomes.index(escolha)
            st.session_state[f"addr_{key}"] = sugs[idx]
            st.session_state[f"addr_{key}_sugs"] = []
            st.session_state[f"addr_{key}_erro"] = False
            st.rerun()

    sel = st.session_state[f"addr_{key}"]
    if sel:
        col_chip, col_clr = st.columns([11, 1])
        with col_chip:
            st.markdown(
                f'<div class="g-addr-chip">'
                f'<span class="g-addr-chip-icon">📍</span>'
                f'<span>{sel["nome"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_clr:
            st.markdown("<div style='margin-top:6px'>", unsafe_allow_html=True)
            if st.button("✕", key=f"_clr_{key}", help="Limpar endereço"):
                st.session_state[f"addr_{key}"] = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state[f"addr_{key}"]


# ── Cálculo ──────────────────────────────────────────────────────────────────
def eh_final_de_semana(d: date) -> bool:
    return d.weekday() >= 5


def calcular_margem(receita, km, custo_km, pedagio, estacionamento, agua):
    receita_liquida = receita * (1 - COMISSOES_IMPOSTOS)
    custo_variavel = km * custo_km
    balanco = receita_liquida - custo_variavel - pedagio - estacionamento - agua
    margem = receita_liquida * (balanco / receita) if receita > 0 else 0.0
    return {
        "receita_bruta": receita, "receita_liquida": receita_liquida,
        "custo_variavel": custo_variavel, "balanco": balanco, "margem": margem,
        "pedagio": pedagio, "estacionamento": estacionamento, "agua": agua,
    }


def calcular_preco_minimo(km, custo_km, pedagio, estacionamento, agua, margem_minima):
    fator = 1 - COMISSOES_IMPOSTOS
    custos = km * custo_km + pedagio + estacionamento + agua
    return math.ceil((margem_minima / fator + custos) / fator)


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="g-header">
    <div class="g-logo">Gooden<span></span></div>
    <div class="g-header-right">
        <div class="g-header-title">Precificação de Fretamento</div>
        <div class="g-header-sub">Gooden Tool Kit · Margem de contribuição</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tipo de viagem ────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Tipo de serviço</div>', unsafe_allow_html=True)
tipo_viagem = st.radio(
    "Tipo", ["Ida e Volta", "Somente Ida"],
    horizontal=True, label_visibility="collapsed",
)

# ── Endereços ─────────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Rota</div>', unsafe_allow_html=True)

col_orig, col_dest = st.columns(2)

with col_orig:
    origem = campo_endereco("Origem", "origem", "Ex: Av. Paulista, 1000, São Paulo")
    col_d1, col_h1 = st.columns(2)
    with col_d1:
        data_saida = st.date_input("Data de saída", value=date.today(), format="DD/MM/YYYY", key="data_saida")
    with col_h1:
        hora_saida = st.time_input("Hora de saída", value=datetime.strptime("08:00", "%H:%M").time(), key="hora_saida", step=300)

with col_dest:
    destino = campo_endereco("Destino", "destino", "Ex: Rua das Flores, 50, Campinas")
    if tipo_viagem == "Ida e Volta":
        col_d2, col_h2 = st.columns(2)
        with col_d2:
            data_volta = st.date_input("Data de volta", value=date.today(), format="DD/MM/YYYY", key="data_volta")
        with col_h2:
            hora_volta = st.time_input("Hora de volta", value=datetime.strptime("18:00", "%H:%M").time(), key="hora_volta", step=300)

# ── Paradas intermediárias ────────────────────────────────────────────────────
if "n_paradas" not in st.session_state:
    st.session_state.n_paradas = 0

with st.expander("➕  Adicionar paradas intermediárias", expanded=False):
    st.markdown(
        '<div style="font-family:Abhaya Libre,serif;font-size:0.88rem;color:#8386C8;margin-bottom:12px">'
        'Endereços adicionais de embarque ou desembarque (incluídos no cálculo de km).'
        '</div>',
        unsafe_allow_html=True,
    )
    for i in range(st.session_state.n_paradas):
        campo_endereco(f"Parada {i + 1}", f"parada_{i}", "Ex: Terminal Tietê, São Paulo")

    col_add, col_rem = st.columns(2)
    with col_add:
        if st.button("+ Adicionar parada", key="btn_add_parada"):
            st.session_state.n_paradas += 1
            st.rerun()
    with col_rem:
        if st.session_state.n_paradas > 0:
            if st.button("− Remover última", key="btn_rem_parada"):
                st.session_state.n_paradas -= 1
                st.session_state[f"addr_parada_{st.session_state.n_paradas}"] = None
                st.rerun()

# ── Calcular km automaticamente ───────────────────────────────────────────────
if "km_auto" not in st.session_state:
    st.session_state.km_auto = None

tem_coords = (
    origem is not None and destino is not None
    and "lat" in (origem or {}) and "lat" in (destino or {})
)

if tem_coords:
    url_rotas = f"https://rotasbrasil.com.br/?origem={quote(origem['nome'])}&destino={quote(destino['nome'])}"

    col_calc, col_link = st.columns([2, 2])
    with col_calc:
        if st.button("📏 Calcular distância automaticamente", key="btn_calc_km"):
            coords = [(origem["lat"], origem["lon"])]
            for i in range(st.session_state.n_paradas):
                p = st.session_state.get(f"addr_parada_{i}")
                if p:
                    coords.append((p["lat"], p["lon"]))
            coords.append((destino["lat"], destino["lon"]))
            if tipo_viagem == "Ida e Volta":
                coords.append((origem["lat"], origem["lon"]))

            with st.spinner("Calculando rota..."):
                km_calc = calcular_km_rota(coords)

            if km_calc:
                st.session_state.km_auto = km_calc
                st.session_state["_km_val"] = km_calc
                st.rerun()
            else:
                st.error("Não foi possível calcular a rota. Insira o km manualmente.")
    with col_link:
        st.markdown(
            f'<div style="margin-top:8px">'
            f'<a href="{url_rotas}" target="_blank" class="g-link-btn">🛣️ Consultar pedágios no RotasBrasil</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.km_auto:
        label_km = "km total (ida e volta)" if tipo_viagem == "Ida e Volta" else "km total"
        st.markdown(
            f'<div class="g-km-badge">✅ Rota calculada: <strong>{st.session_state.km_auto} km</strong> {label_km}</div>',
            unsafe_allow_html=True,
        )

# ── Veículo e Distância ───────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Veículo e Distância</div>', unsafe_allow_html=True)

col_v, col_km = st.columns([3, 2])
with col_v:
    veiculo = st.selectbox("Tipo de veículo", list(VEICULOS.keys()), key="veiculo")

with col_km:
    km_default = float(st.session_state.get("_km_val") or 0.0)
    km_label = "Km total (ida e volta)" if tipo_viagem == "Ida e Volta" else "Km total (somente ida)"
    km = st.number_input(km_label, min_value=0.0, step=10.0, value=km_default, format="%.1f", key="km_input")

custo_km = VEICULOS[veiculo]
st.markdown(
    f'<div style="font-family:Geologica,sans-serif;font-size:0.78rem;color:#ACB0F8;margin-top:-8px;">'
    f'Custo variável: <strong style="color:#5450FF;">R$ {custo_km:.2f}/km</strong></div>',
    unsafe_allow_html=True,
)

# ── Custos adicionais ─────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Custos Adicionais</div>', unsafe_allow_html=True)

col_ped, col_est, col_agua = st.columns(3)
with col_ped:
    pedagio = st.number_input("Pedágio (R$)", min_value=0.0, step=5.0, value=0.0, format="%.2f", key="pedagio")
with col_est:
    estacionamento = st.number_input("Estacionamento (R$)", min_value=0.0, step=5.0, value=0.0, format="%.2f", key="estacionamento")
with col_agua:
    agua = st.number_input("Água / caixa (R$)", min_value=0.0, step=1.0, value=0.0, format="%.2f", key="agua")

# ── Dia e margem mínima ───────────────────────────────────────────────────────
is_fds = eh_final_de_semana(data_saida)
if tipo_viagem == "Ida e Volta":
    is_fds = is_fds or eh_final_de_semana(data_volta)

margem_minima = MARGEM_MIN_FDS if is_fds else MARGEM_MIN_SEMANA
tipo_dia_label = "Final de semana" if is_fds else "Dia de semana"

# ── Precificação ──────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Precificação</div>', unsafe_allow_html=True)

preco_minimo_sugerido = calcular_preco_minimo(km, custo_km, pedagio, estacionamento, agua, margem_minima) if km > 0 else 0.0

col_preco, col_sugestao = st.columns([2, 1])
with col_preco:
    preco_cobrado = st.number_input(
        "Valor cobrado do cliente (R$)", min_value=0.0, step=50.0,
        value=float(preco_minimo_sugerido), format="%.2f", key="preco_cobrado",
    )
with col_sugestao:
    st.markdown(
        f'<div style="margin-top:28px;font-family:Geologica,sans-serif;font-size:0.78rem;">'
        f'<span style="color:#ACB0F8;">Preço mínimo sugerido</span><br>'
        f'<strong style="color:#5450FF;font-size:1.1rem;">R$ {preco_minimo_sugerido:,.2f}</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Resultado ─────────────────────────────────────────────────────────────────
st.divider()

if km <= 0:
    st.markdown(
        '<div style="text-align:center;padding:32px 24px;color:#C4C7F8;'
        'font-family:Geologica,sans-serif;font-weight:600;">'
        'Informe a distância em km para calcular a precificação.</div>',
        unsafe_allow_html=True,
    )
else:
    resultado = calcular_margem(preco_cobrado, km, custo_km, pedagio, estacionamento, agua)
    margem = resultado["margem"]
    margem_ok = margem >= margem_minima

    badge_class = "badge-fds" if is_fds else "badge-semana"
    badge_icon = "📅" if is_fds else "📆"
    st.markdown(
        f'<span class="g-badge-type {badge_class}">'
        f'{badge_icon} {tipo_dia_label} · Margem mínima: R$ {margem_minima:,.0f}'
        f'</span>',
        unsafe_allow_html=True,
    )

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        price_class = "g-result-price" if margem_ok else "g-result-price red"
        st.markdown(
            f'<div class="g-result-label">Valor cobrado</div>'
            f'<div class="{price_class}">R$ {preco_cobrado:,.2f}</div>',
            unsafe_allow_html=True,
        )
    with col_res2:
        margin_class = "g-margin-ok" if margem_ok else "g-margin-warn"
        margem_icon = "✅" if margem_ok else "⚠️"
        st.markdown(
            f'<div class="g-result-label">Margem de Contribuição</div>'
            f'<div class="{margin_class}">{margem_icon} R$ {margem:,.2f}</div>',
            unsafe_allow_html=True,
        )
        if not margem_ok:
            diferenca = margem_minima - margem
            st.markdown(
                f'<div style="font-family:Geologica,sans-serif;font-size:0.75rem;color:#D93025;margin-top:4px;">'
                f'Abaixo do mínimo em R$ {diferenca:,.2f}. '
                f'Preço mínimo: <strong>R$ {preco_minimo_sugerido:,.2f}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with st.expander("Ver detalhamento do cálculo", expanded=False):
        comissoes_valor = resultado["receita_bruta"] * COMISSOES_IMPOSTOS
        linhas = [
            ("Receita bruta", resultado["receita_bruta"], False),
            (f"Comissões e impostos ({COMISSOES_IMPOSTOS*100:.2f}%)", -comissoes_valor, True),
        ]
        for nome, pct in DETALHAMENTO_COMISSOES.items():
            linhas.append((f"  └ {nome}", -resultado["receita_bruta"] * pct, True))
        linhas += [
            ("= Receita líquida", resultado["receita_liquida"], False),
            (f"Custo variável ({km:.0f} km × R$ {custo_km:.2f}/km)", -resultado["custo_variavel"], True),
            ("Pedágio", -pedagio, True) if pedagio else ("Pedágio", 0, False),
            ("Estacionamento", -estacionamento, True) if estacionamento else ("Estacionamento", 0, False),
            ("Água / caixa", -agua, True) if agua else ("Água / caixa", 0, False),
            ("= Margem de contribuição", margem, False),
        ]
        html_rows = ""
        for label_row, valor, is_custo in linhas:
            val_class = "g-breakdown-value negative" if is_custo and valor != 0 else "g-breakdown-value"
            if label_row.startswith("="):
                html_rows += (
                    f'<div class="g-breakdown-row" style="font-weight:700;border-top:2px solid #EAECFF;'
                    f'margin-top:4px;padding-top:10px;">'
                    f'<span class="g-breakdown-label" style="color:#3D3F8F;">{label_row}</span>'
                    f'<span class="{val_class}">R$ {valor:,.2f}</span></div>'
                )
            else:
                html_rows += (
                    f'<div class="g-breakdown-row">'
                    f'<span class="g-breakdown-label">{label_row}</span>'
                    f'<span class="{val_class}">R$ {valor:,.2f}</span></div>'
                )
        st.markdown(f'<div style="padding:4px 0">{html_rows}</div>', unsafe_allow_html=True)

    with st.expander("Ver resumo da viagem", expanded=False):
        saida_fmt = data_saida.strftime("%d/%m/%Y") + " às " + hora_saida.strftime("%H:%M")
        volta_fmt = (data_volta.strftime("%d/%m/%Y") + " às " + hora_volta.strftime("%H:%M")) if tipo_viagem == "Ida e Volta" else "—"
        origem_nome = (origem or {}).get("nome", "—")
        destino_nome = (destino or {}).get("nome", "—")
        paradas_lista = [
            st.session_state.get(f"addr_parada_{i}", {}) or {}
            for i in range(st.session_state.n_paradas)
        ]
        paradas_txt = ", ".join(p["nome"] for p in paradas_lista if p.get("nome")) or "Nenhuma"

        info = [
            ("Tipo de serviço", tipo_viagem),
            ("Origem", origem_nome),
            ("Saída", saida_fmt),
            ("Destino", destino_nome),
            ("Volta", volta_fmt),
            ("Paradas intermediárias", paradas_txt),
            ("Veículo", veiculo),
            ("Distância", f"{km:.1f} km"),
        ]
        html_info = "".join(
            f'<div class="g-breakdown-row"><span class="g-breakdown-label">{k}</span>'
            f'<span class="g-breakdown-value">{v}</span></div>'
            for k, v in info
        )
        st.markdown(f'<div style="padding:4px 0">{html_info}</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="g-footer">Gooden · Conduzindo tranquilidade</div>', unsafe_allow_html=True)
