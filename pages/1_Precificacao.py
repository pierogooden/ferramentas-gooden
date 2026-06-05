import math
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.design import get_theme, inject_css, render_header

st.set_page_config(
    page_title="Gooden Tool Kit · Precificação",
    page_icon="🚌",
    layout="centered",
)

inject_css()
render_header("Precificação de Fretamento", "Margem de contribuição", page_key="prec")

# ── Constantes ────────────────────────────────────────────────────────────────
COMISSOES_IMPOSTOS = 0.2765

VEICULOS = {
    "Ônibus Executivo - Motor Traseiro": 3.12,
    "Ônibus Convencional - Motor Traseiro": 2.78,
    "Ônibus Executivo - Motor Dianteiro": 2.65,
    "Ônibus Convencional - Motor Dianteiro": 2.48,
    "Microônibus Executivo": 1.82,
    "Microônibus Convencional": 1.73,
}

MARGEM_MIN_SEMANA = 700.0    # piso dias de semana (seg–sex)
MARGEM_MIN_FDS    = 1000.0   # piso finais de semana (sáb–dom)
MARGEM_PCT_ALVO   = 0.40     # meta de 40% de (RL - Custos) / Receita

DETALHAMENTO_COMISSOES = {
    "Comissão de Vendas (2%)": 0.02,
    "Comissão do Motorista (10%)": 0.10,
    "PIS (0,65%)": 0.0065,
    "COFINS (3%)": 0.03,
    "ICMS (12%)": 0.12,
}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"


# ── Geocoding ─────────────────────────────────────────────────────────────────
def _nome_curto_api(r: dict) -> str:
    """Constrói nome legível a partir do addressdetails do Nominatim."""
    addr = r.get("address", {})
    road = addr.get("road") or addr.get("pedestrian") or addr.get("street") or ""
    num  = addr.get("house_number", "")
    sub  = addr.get("suburb") or addr.get("neighbourhood") or addr.get("quarter") or ""
    city = addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("village") or ""
    state = addr.get("state", "")
    partes = []
    if road:
        partes.append(f"{road}, {num}" if num else road)
    if sub:
        partes.append(sub)
    if city:
        partes.append(city)
    if state and state != city:
        partes.append(state)
    return ", ".join(partes) if partes else r.get("display_name", "")


def buscar_enderecos(query: str) -> list[dict]:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 6, "countrycodes": "br", "addressdetails": 1},
            headers={"User-Agent": "GoodenToolKit/1.0 (contato@gooden.com.br)"},
            timeout=6,
        )
        return [
            {"nome": _nome_curto_api(r), "lat": float(r["lat"]), "lon": float(r["lon"])}
            for r in resp.json()
        ]
    except Exception:
        return []


def calcular_km_rota(coords: list[tuple]) -> tuple[float | None, list[float]]:
    """Returns (total_km, list of leg distances in km)."""
    try:
        waypoints = ";".join(f"{lon},{lat}" for lat, lon in coords)
        resp = requests.get(f"{OSRM_URL}/{waypoints}", params={"overview": "false"}, timeout=10)
        data = resp.json()
        if data.get("code") == "Ok":
            route = data["routes"][0]
            total = round(route["distance"] / 1000, 1)
            legs = [round(leg["distance"] / 1000, 1) for leg in route.get("legs", [])]
            return total, legs
        return None, []
    except Exception:
        return None, []


# ── Componente de endereço ────────────────────────────────────────────────────
def _on_address_change(key: str):
    texto = st.session_state.get(f"_ti_{key}", "").strip()
    if len(texto) >= 3:
        sugs = buscar_enderecos(texto)
        st.session_state[f"addr_{key}_sugs"] = sugs
        st.session_state[f"addr_{key}_erro"] = len(sugs) == 0
    else:
        st.session_state[f"addr_{key}_sugs"] = []
        st.session_state[f"addr_{key}_erro"] = False
    st.session_state[f"addr_{key}"] = None
    st.session_state["km_auto"]  = None
    st.session_state["km_legs"]  = []
    st.session_state["km_input"] = 0.0


def _limpar_endereco(key: str):
    st.session_state[f"addr_{key}"] = None
    st.session_state[f"addr_{key}_sugs"] = []
    st.session_state[f"addr_{key}_erro"] = False
    st.session_state["km_auto"]  = None
    st.session_state["km_legs"]  = []
    st.session_state["km_input"] = 0.0


def campo_endereco(label: str, key: str, placeholder: str = "Ex: Av. Paulista, 1000, São Paulo") -> dict | None:
    c = get_theme()
    for k, v in [(f"addr_{key}", None), (f"addr_{key}_sugs", []), (f"addr_{key}_erro", False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    sel  = st.session_state[f"addr_{key}"]
    sugs = st.session_state[f"addr_{key}_sugs"]

    st.markdown(
        f'<div style="font-family:Geologica,sans-serif;font-weight:600;font-size:0.8rem;'
        f'color:{c["text_secondary"]};margin-bottom:4px;">{label}</div>',
        unsafe_allow_html=True,
    )

    if sel:
        # ── Estado 3: endereço confirmado → exibe chip com botão limpar ──────
        col_chip, col_clr = st.columns([11, 1])
        with col_chip:
            st.markdown(
                f'<div class="g-addr-chip"><span>📍</span><span>{sel["nome"]}</span></div>',
                unsafe_allow_html=True,
            )
        with col_clr:
            st.markdown("<div style='margin-top:6px'>", unsafe_allow_html=True)
            if st.button("✕", key=f"_clr_{key}", help="Editar endereço"):
                _limpar_endereco(key)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    elif sugs:
        # ── Estado 2: sugestões disponíveis → substitui o input pelo selectbox ──
        nomes = [s["nome"] for s in sugs]
        escolha = st.selectbox(
            label, ["— selecione o endereço —"] + nomes,
            key=f"_sel_{key}", label_visibility="collapsed",
        )
        if escolha != "— selecione o endereço —":
            idx = nomes.index(escolha)
            st.session_state[f"addr_{key}"] = sugs[idx]
            st.session_state[f"addr_{key}_sugs"] = []
            st.rerun()
        if st.button("← Nova busca", key=f"_cancel_{key}"):
            st.session_state[f"addr_{key}_sugs"] = []
            st.rerun()

    else:
        # ── Estado 1: campo de digitação ──────────────────────────────────────
        st.text_input(
            label, placeholder=placeholder,
            key=f"_ti_{key}", label_visibility="collapsed",
            on_change=_on_address_change, args=(key,),
            help="Digite rua, número e cidade — pressione Enter para buscar",
        )
        if st.session_state[f"addr_{key}_erro"]:
            st.markdown(
                f'<div style="font-size:0.75rem;color:{c["error"]};margin-top:2px;">'
                f'⚠️ Nenhum resultado. Tente incluir o nome da cidade.</div>',
                unsafe_allow_html=True,
            )

    return sel


# ── Cálculo ───────────────────────────────────────────────────────────────────
def calcular_margem(receita, km, custo_km, pedagio, estacionamento, agua):
    receita_liquida = receita * (1 - COMISSOES_IMPOSTOS)
    custo_variavel  = km * custo_km
    balanco  = receita_liquida - custo_variavel - pedagio - estacionamento - agua
    margem   = receita_liquida * (balanco / receita) if receita > 0 else 0.0
    pct_i10  = balanco / receita if receita > 0 else 0.0   # métrica I10 da planilha
    return {
        "receita_bruta": receita, "receita_liquida": receita_liquida,
        "custo_variavel": custo_variavel, "balanco": balanco,
        "margem": margem, "pct_i10": pct_i10,
        "pedagio": pedagio, "estacionamento": estacionamento, "agua": agua,
    }


def calcular_preco_sugerido(km, custo_km, pedagio, estacionamento, agua, margem_minima):
    """Maior entre: preço para 40% na métrica I10  e  preço para o piso absoluto."""
    fator  = 1 - COMISSOES_IMPOSTOS          # 0.7235
    custos = km * custo_km + pedagio + estacionamento + agua

    # 40%: (RL − Custos) / Receita ≥ 0.40  →  Receita = Custos / (fator − 0.40)
    denom_pct = fator - MARGEM_PCT_ALVO      # 0.3235
    preco_pct = math.ceil(custos / denom_pct) if denom_pct > 0 and custos > 0 else 0

    # Piso absoluto (R$ 700 semana / R$ 1.000 FDS)
    preco_abs = math.ceil((margem_minima / fator + custos) / fator)

    return max(preco_pct, preco_abs, 1)


# ── Tipo de viagem ────────────────────────────────────────────────────────────
c = get_theme()
st.markdown('<div class="g-section-label">Tipo de serviço</div>', unsafe_allow_html=True)
tipo_viagem = st.radio("Tipo", ["Ida e Volta", "Somente Ida"], horizontal=True, label_visibility="collapsed")

# ── Endereços ─────────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Rota</div>', unsafe_allow_html=True)

col_orig, col_dest = st.columns(2)

with col_orig:
    origem = campo_endereco("Origem", "origem")
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
    else:
        data_volta = data_saida

# ── Badge de dia e margem mínima ──────────────────────────────────────────────
DIAS_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
data_ref   = data_saida
is_fds     = data_ref.weekday() >= 5
if tipo_viagem == "Ida e Volta":
    is_fds = is_fds or data_volta.weekday() >= 5
margem_minima  = MARGEM_MIN_FDS if is_fds else MARGEM_MIN_SEMANA
tipo_dia_label = "Final de semana" if is_fds else "Dia de semana"
dia_nome       = DIAS_PT[data_ref.weekday()]
badge_class    = "badge-fds" if is_fds else "badge-semana"
badge_icon     = "📅" if is_fds else "📆"

st.markdown(
    f'<span class="g-badge-type {badge_class}" style="margin-top:4px;margin-bottom:4px;">'
    f'{badge_icon} {dia_nome} · {tipo_dia_label} · '
    f'Mínimo: R$ {margem_minima:,.0f} · Meta: {int(MARGEM_PCT_ALVO*100)}%'
    f'</span>',
    unsafe_allow_html=True,
)

# ── Paradas intermediárias ────────────────────────────────────────────────────
if "n_paradas" not in st.session_state:
    st.session_state.n_paradas = 0

with st.expander("➕  Adicionar paradas intermediárias", expanded=False):
    st.markdown(
        f'<div style="font-family:Abhaya Libre,serif;font-size:0.88rem;color:{c["text_muted"]};margin-bottom:12px">'
        f'Endereços adicionais incluídos automaticamente no cálculo de km.</div>',
        unsafe_allow_html=True,
    )
    for i in range(st.session_state.n_paradas):
        campo_endereco(f"Parada {i + 1}", f"parada_{i}", "Ex: Terminal Tietê, São Paulo")

    col_add, col_rem = st.columns(2)
    with col_add:
        if st.button("+ Adicionar parada", key="btn_add"):
            st.session_state.n_paradas += 1
            st.rerun()
    with col_rem:
        if st.session_state.n_paradas > 0 and st.button("− Remover última", key="btn_rem"):
            idx = st.session_state.n_paradas - 1
            st.session_state[f"addr_parada_{idx}"] = None
            st.session_state.n_paradas -= 1
            st.rerun()

# ── Calcular km ───────────────────────────────────────────────────────────────
for k, v in [("km_auto", None), ("km_legs", []), ("km_input", 0.0)]:
    if k not in st.session_state:
        st.session_state[k] = v

tem_coords = origem is not None and destino is not None

if tem_coords:
    url_rotas = f"https://rotasbrasil.com.br/?origem={quote(origem['nome'])}&destino={quote(destino['nome'])}"
    col_calc, col_link = st.columns([2, 2])

    with col_calc:
        calcular_clicked = st.button("📏 Calcular distância automaticamente", key="btn_calc_km")

    with col_link:
        st.markdown(
            f'<div style="margin-top:8px">'
            f'<a href="{url_rotas}" target="_blank" class="g-link-btn">🛣️ Consultar pedágios no RotasBrasil</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if calcular_clicked:
        coords = [(origem["lat"], origem["lon"])]
        for i in range(st.session_state.n_paradas):
            p = st.session_state.get(f"addr_parada_{i}")
            if p:
                coords.append((p["lat"], p["lon"]))
        coords.append((destino["lat"], destino["lon"]))
        if tipo_viagem == "Ida e Volta":
            coords.append((origem["lat"], origem["lon"]))

        with st.spinner("Calculando rota..."):
            km_calc, legs = calcular_km_rota(coords)

        if km_calc:
            st.session_state.km_auto  = km_calc
            st.session_state.km_legs  = legs
            st.session_state["km_input"] = km_calc   # preenche o campo diretamente
            st.rerun()
        else:
            st.error("Não foi possível calcular a rota. Insira o km manualmente.")

    if st.session_state.km_auto:
        label_tipo = "ida e volta" if tipo_viagem == "Ida e Volta" else "somente ida"
        st.markdown(
            f'<div class="g-km-badge">✅ Rota calculada: <strong>{st.session_state.km_auto} km</strong> total ({label_tipo})</div>',
            unsafe_allow_html=True,
        )

        # Breakdown por trecho
        legs = st.session_state.km_legs
        if legs:
            paradas_selecionadas = [
                st.session_state.get(f"addr_parada_{i}") for i in range(st.session_state.n_paradas)
                if st.session_state.get(f"addr_parada_{i}")
            ]
            pontos = [origem] + paradas_selecionadas + [destino]
            if tipo_viagem == "Ida e Volta":
                pontos.append(origem)

            def nome_curto(addr):
                partes = addr["nome"].split(",")
                return partes[0].strip() if partes else addr["nome"]

            trechos_html = ""
            for i, leg_km in enumerate(legs):
                if i < len(pontos) - 1:
                    de = nome_curto(pontos[i])
                    ate = nome_curto(pontos[i + 1])
                    sufixo = " (retorno)" if tipo_viagem == "Ida e Volta" and i == len(legs) - 1 else ""
                    trechos_html += (
                        f'<div style="font-family:Abhaya Libre,serif;font-size:0.82rem;'
                        f'color:{c["text_muted"]};padding:2px 0;">'
                        f'<span style="color:{c["text_secondary"]};">{de} → {ate}</span>'
                        f'<span style="float:right;color:{c["accent"]};font-weight:600;">{leg_km} km{sufixo}</span>'
                        f'</div>'
                    )
            if trechos_html:
                st.markdown(
                    f'<div style="background:{c["accent_bg"]};border:1px solid {c["border"]};'
                    f'border-radius:8px;padding:10px 14px;margin-top:6px;">'
                    f'{trechos_html}</div>',
                    unsafe_allow_html=True,
                )

elif origem is not None or destino is not None:
    st.markdown(
        f'<div style="font-size:0.78rem;color:{c["text_muted"]};margin-top:4px;">'
        f'Selecione origem e destino para calcular a distância automaticamente.</div>',
        unsafe_allow_html=True,
    )

# ── Veículo e Distância ───────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Veículo e Distância</div>', unsafe_allow_html=True)

col_v, col_km = st.columns([3, 2])
with col_v:
    veiculo = st.selectbox("Tipo de veículo", list(VEICULOS.keys()), key="veiculo")
with col_km:
    km_label = "Km total (ida e volta)" if tipo_viagem == "Ida e Volta" else "Km total (somente ida)"
    km = st.number_input(
        km_label, min_value=0.0, step=10.0, format="%.1f", key="km_input",
        help="Distância total da viagem. Para Ida e Volta, inclua os dois trechos. Use o botão acima para calcular automaticamente.",
    )

custo_km = VEICULOS[veiculo]

# ── Custos adicionais ─────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Custos Adicionais</div>', unsafe_allow_html=True)

col_ped, col_est, col_agua = st.columns(3)
with col_ped:
    pedagio = st.number_input(
        "Pedágio (R$)", min_value=0.0, step=5.0, value=0.0, format="%.2f", key="pedagio",
        help="Valor total de pedágios da viagem. Consulte o RotasBrasil para o valor exato.",
    )
with col_est:
    estacionamento = st.number_input(
        "Estacionamento (R$)", min_value=0.0, step=5.0, value=0.0, format="%.2f", key="estacionamento",
        help="Custo de estacionamento no destino, se houver.",
    )
with col_agua:
    agua = st.number_input(
        "Água / caixa (R$)", min_value=0.0, step=1.0, value=0.0, format="%.2f", key="agua",
        help="Custo de uma caixa de copos d'água para os passageiros.",
    )

# ── Precificação ──────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Precificação</div>', unsafe_allow_html=True)

preco_sugerido = calcular_preco_sugerido(km, custo_km, pedagio, estacionamento, agua, margem_minima) if km > 0 else 0.0

col_preco, col_sugestao = st.columns([2, 1])
with col_preco:
    if "_preco_override" in st.session_state:
        override = st.session_state.pop("_preco_override")
        st.session_state["preco_cobrado"] = override
    preco_cobrado = st.number_input(
        "Valor cobrado do cliente (R$)", min_value=0.0, step=50.0,
        format="%.2f", key="preco_cobrado",
        help="Valor cobrado do cliente. O preço sugerido garante 40% de margem com mínimo de R$ 1.000.",
    )

with col_sugestao:
    st.markdown(
        f'<div style="margin-top:28px;font-family:Geologica,sans-serif;font-size:0.78rem;">'
        f'<span style="color:{c["text_faint"]};">Preço sugerido (40%)</span><br>'
        f'<strong style="color:{c["accent"]};font-size:1.1rem;">R$ {preco_sugerido:,.2f}</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Resultado ─────────────────────────────────────────────────────────────────
st.divider()

if km <= 0:
    st.markdown(
        f'<div style="text-align:center;padding:32px 24px;color:{c["border"]};'
        f'font-family:Geologica,sans-serif;font-weight:600;">'
        f'Informe a distância em km para calcular a precificação.</div>',
        unsafe_allow_html=True,
    )
else:
    resultado = calcular_margem(preco_cobrado, km, custo_km, pedagio, estacionamento, agua)
    margem    = resultado["margem"]
    margem_ok = margem >= margem_minima

    price_class = "g-result-price" if margem_ok else "g-result-price red"
    st.markdown(
        f'<div class="g-result-label">Valor cobrado</div>'
        f'<div class="{price_class}">R$ {preco_cobrado:,.2f}</div>',
        unsafe_allow_html=True,
    )

    if not margem_ok:
        diferenca = margem_minima - margem
        st.markdown(
            f'<div style="font-size:0.82rem;color:{c["error"]};margin-top:6px;font-family:Geologica,sans-serif;">'
            f'⚠️ Margem abaixo do mínimo em R$ {diferenca:,.2f}</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"↑ Usar preço sugerido  ·  R$ {preco_sugerido:,.2f}", key="btn_usar_minimo"):
            st.session_state["_preco_override"] = float(preco_sugerido)
            st.rerun()

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
        ]
        if pedagio:
            linhas.append(("Pedágio", -pedagio, True))
        if estacionamento:
            linhas.append(("Estacionamento", -estacionamento, True))
        if agua:
            linhas.append(("Água / caixa", -agua, True))
        linhas.append(("= Margem de contribuição", margem, False))

        html_rows = ""
        for lbl, val, is_custo in linhas:
            vc = "g-breakdown-value negative" if is_custo and val != 0 else "g-breakdown-value"
            if lbl.startswith("="):
                html_rows += (
                    f'<div class="g-breakdown-row" style="font-weight:700;border-top:2px solid {c["border"]};'
                    f'margin-top:4px;padding-top:10px;">'
                    f'<span class="g-breakdown-label" style="color:{c["text_secondary"]};">{lbl}</span>'
                    f'<span class="{vc}">R$ {val:,.2f}</span></div>'
                )
            else:
                html_rows += (
                    f'<div class="g-breakdown-row">'
                    f'<span class="g-breakdown-label">{lbl}</span>'
                    f'<span class="{vc}">R$ {val:,.2f}</span></div>'
                )
        st.markdown(f'<div style="padding:4px 0">{html_rows}</div>', unsafe_allow_html=True)

    with st.expander("Ver resumo da viagem", expanded=False):
        saida_fmt = data_saida.strftime("%d/%m/%Y") + " às " + hora_saida.strftime("%H:%M")
        if tipo_viagem == "Ida e Volta":
            volta_fmt = data_volta.strftime("%d/%m/%Y") + " às " + hora_volta.strftime("%H:%M")
        else:
            volta_fmt = "—"
        paradas_lista = [st.session_state.get(f"addr_parada_{i}") or {} for i in range(st.session_state.n_paradas)]
        paradas_txt = ", ".join(p["nome"].split(",")[0] for p in paradas_lista if p.get("nome")) or "Nenhuma"

        info = [
            ("Tipo de serviço", tipo_viagem),
            ("Origem", (origem or {}).get("nome", "—").split(",")[0]),
            ("Saída", saida_fmt),
            ("Destino", (destino or {}).get("nome", "—").split(",")[0]),
            ("Volta", volta_fmt),
            ("Paradas", paradas_txt),
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
