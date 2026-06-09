import math
import sys
from datetime import date, datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
COMISSOES_IMPOSTOS   = 0.2765
MARGEM_MIN_SEMANA    = 700.0
MARGEM_MIN_FDS       = 1000.0
MARGEM_PCT_ALVO      = 0.40
DESPESAS_MOTORISTA   = 200.0   # adicionado quando serviço > 13 h
HORAS_NOVO_DIA       = 18      # a partir de 18 h conta como +1 dia
HORAS_DESPESAS_MOT   = 13      # acima de 13 h → despesas do motorista

VEICULOS = {
    "Ônibus Executivo - Motor Traseiro":    3.12,
    "Ônibus Convencional - Motor Traseiro": 2.78,
    "Ônibus Executivo - Motor Dianteiro":   2.65,
    "Ônibus Convencional - Motor Dianteiro":2.48,
    "Microônibus Executivo":                1.82,
    "Microônibus Convencional":             1.73,
    "Van Executiva 18 Lugares":             round(1.73 * 0.90, 4),  # microônibus conv. − 10 %
}

DETALHAMENTO_COMISSOES = {
    "Comissão de Vendas (2%)":     0.02,
    "Comissão do Motorista (10%)": 0.10,
    "PIS (0,65%)":                 0.0065,
    "COFINS (3%)":                 0.03,
    "ICMS (12%)":                  0.12,
}


# ── Cálculo de duração e dias ─────────────────────────────────────────────────
def calcular_servico(tipo_viagem, data_saida, hora_saida, data_volta, hora_volta):
    """
    Retorna (duracao_horas, num_dias, despesas_motorista).

    Regras:
      - Somente Ida: 1 dia, sem despesas extras (duração desconhecida)
      - Ida e Volta:
        • >= 18 h → conta no mínimo 2 dias (ou mais, se cruzar mais datas)
        • > 13 h  → adiciona R$ 200 de despesas do motorista
    """
    if tipo_viagem != "Ida e Volta":
        return 0.0, 1, 0.0

    dt_saida = datetime.combine(data_saida, hora_saida)
    dt_volta = datetime.combine(data_volta, hora_volta)
    duracao_horas = max(0.0, (dt_volta - dt_saida).total_seconds() / 3600)

    calendar_days = (data_volta - data_saida).days + 1
    if duracao_horas >= HORAS_NOVO_DIA:
        num_dias = max(2, calendar_days)
    else:
        num_dias = max(1, calendar_days)

    desp = DESPESAS_MOTORISTA if duracao_horas > HORAS_DESPESAS_MOT else 0.0
    return duracao_horas, num_dias, desp


# ── Cálculo de margem ─────────────────────────────────────────────────────────
def calcular_margem(receita, km, custo_km, pedagio, estacionamento, agua, desp_motorista=0.0):
    receita_liquida = receita * (1 - COMISSOES_IMPOSTOS)
    custo_variavel  = km * custo_km
    balanco = receita_liquida - custo_variavel - pedagio - estacionamento - agua - desp_motorista
    margem  = receita_liquida * (balanco / receita) if receita > 0 else 0.0
    pct_i10 = balanco / receita if receita > 0 else 0.0
    return {
        "receita_bruta": receita, "receita_liquida": receita_liquida,
        "custo_variavel": custo_variavel, "balanco": balanco,
        "margem": margem, "pct_i10": pct_i10,
        "pedagio": pedagio, "estacionamento": estacionamento,
        "agua": agua, "desp_motorista": desp_motorista,
    }


def calcular_preco_sugerido(km, custo_km, pedagio, estacionamento, agua, margem_minima, desp_motorista=0.0):
    fator  = 1 - COMISSOES_IMPOSTOS           # 0.7235
    custos = km * custo_km + pedagio + estacionamento + agua + desp_motorista
    denom_pct = fator - MARGEM_PCT_ALVO        # 0.3235
    preco_pct = math.ceil(custos / denom_pct) if denom_pct > 0 and custos > 0 else 0
    preco_abs = math.ceil((margem_minima / fator + custos) / fator)
    return max(preco_pct, preco_abs, 1)


# ── Tipo de viagem ────────────────────────────────────────────────────────────
c = get_theme()
st.markdown('<div class="g-section-label">Tipo de serviço</div>', unsafe_allow_html=True)
tipo_viagem = st.radio("Tipo", ["Ida e Volta", "Somente Ida"], horizontal=True, label_visibility="collapsed")

# ── Datas e horários ──────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Data e horário</div>', unsafe_allow_html=True)

if tipo_viagem == "Ida e Volta":
    col_d1, col_h1, col_d2, col_h2 = st.columns(4)
    with col_d1:
        data_saida = st.date_input("Data de saída",  value=date.today(),  format="DD/MM/YYYY", key="data_saida")
    with col_h1:
        hora_saida = st.time_input("Hora de saída",  value=datetime.strptime("08:00", "%H:%M").time(), key="hora_saida", step=300)
    with col_d2:
        data_volta = st.date_input("Data de volta",  value=date.today(),  format="DD/MM/YYYY", key="data_volta")
    with col_h2:
        hora_volta = st.time_input("Hora de volta",  value=datetime.strptime("18:00", "%H:%M").time(), key="hora_volta", step=300)
else:
    col_d1, col_h1 = st.columns(2)
    with col_d1:
        data_saida = st.date_input("Data de saída",  value=date.today(),  format="DD/MM/YYYY", key="data_saida")
    with col_h1:
        hora_saida = st.time_input("Hora de saída",  value=datetime.strptime("08:00", "%H:%M").time(), key="hora_saida", step=300)
    data_volta = data_saida
    hora_volta = hora_saida

# ── Duração e dias de serviço ─────────────────────────────────────────────────
duracao_horas, num_dias, desp_motorista = calcular_servico(
    tipo_viagem, data_saida, hora_saida, data_volta, hora_volta
)

# ── FDS / semana e margem mínima (por dia) ────────────────────────────────────
DIAS_PT  = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
is_fds   = data_saida.weekday() >= 5
if tipo_viagem == "Ida e Volta":
    is_fds = is_fds or data_volta.weekday() >= 5

daily_min     = MARGEM_MIN_FDS if is_fds else MARGEM_MIN_SEMANA
margem_minima = daily_min * num_dias          # mínimo total = por dia × nº de dias

tipo_dia_label = "Final de semana" if is_fds else "Dia de semana"
dia_nome       = DIAS_PT[data_saida.weekday()]
badge_class    = "badge-fds" if is_fds else "badge-semana"
badge_icon     = "📅" if is_fds else "📆"

# Monta texto informativo do badge
badge_parts = [
    f"{badge_icon} {dia_nome} · {tipo_dia_label}",
    f"Mínimo: R$ {margem_minima:,.0f}" + (f" ({num_dias} dias × R$ {daily_min:,.0f})" if num_dias > 1 else ""),
    f"Meta: {int(MARGEM_PCT_ALVO*100)}%",
]
if desp_motorista:
    badge_parts.append("+ R$ 200 despesas motorista")

st.markdown(
    f'<span class="g-badge-type {badge_class}" style="margin-top:4px;margin-bottom:4px;">'
    f'{" · ".join(badge_parts)}'
    f'</span>',
    unsafe_allow_html=True,
)

# Info de duração (apenas para Ida e Volta)
if tipo_viagem == "Ida e Volta" and duracao_horas > 0:
    h = int(duracao_horas)
    m = int((duracao_horas - h) * 60)
    duracao_txt = f"{h}h{m:02d}" if m else f"{h}h"
    st.markdown(
        f'<div style="font-family:Geologica,sans-serif;font-size:0.75rem;'
        f'color:{c["text_faint"]};margin-bottom:4px;">'
        f'⏱ Duração total do serviço: {duracao_txt}</div>',
        unsafe_allow_html=True,
    )

# ── Veículo e Distância ───────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Veículo e Distância</div>', unsafe_allow_html=True)

col_v, col_km = st.columns([3, 2])
with col_v:
    veiculo = st.selectbox("Tipo de veículo", list(VEICULOS.keys()), key="veiculo")
with col_km:
    km_label = "Km total (ida e volta)" if tipo_viagem == "Ida e Volta" else "Km total (somente ida)"
    km = st.number_input(km_label, min_value=0.0, step=10.0, format="%.1f", key="km_input",
                         help="Distância total da viagem. Para Ida e Volta, inclua os dois trechos.")

custo_km = VEICULOS[veiculo]

# ── Custos adicionais ─────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Custos Adicionais</div>', unsafe_allow_html=True)

col_ped, col_est, col_agua = st.columns(3)
with col_ped:
    pedagio = st.number_input("Pedágio (R$)",        min_value=0.0, step=5.0,  value=0.0, format="%.2f", key="pedagio")
with col_est:
    estacionamento = st.number_input("Estacionamento (R$)", min_value=0.0, step=5.0,  value=0.0, format="%.2f", key="estacionamento")
with col_agua:
    agua = st.number_input("Água / caixa (R$)",  min_value=0.0, step=1.0,  value=0.0, format="%.2f", key="agua")

# Despesas do motorista aparecem automaticamente (apenas informativo)
if desp_motorista:
    st.markdown(
        f'<div style="font-family:Geologica,sans-serif;font-size:0.78rem;'
        f'color:{c["warning"]};background:{c["warning_bg"]};border-radius:8px;'
        f'padding:8px 14px;margin-top:4px;">'
        f'🧑‍✈️ Despesas do motorista adicionadas automaticamente: <strong>R$ {desp_motorista:,.2f}</strong>'
        f' (serviço com {int(duracao_horas)}h+)</div>',
        unsafe_allow_html=True,
    )

# ── Precificação ──────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Precificação</div>', unsafe_allow_html=True)

preco_sugerido = (
    calcular_preco_sugerido(km, custo_km, pedagio, estacionamento, agua, margem_minima, desp_motorista)
    if km > 0 else 0.0
)

col_preco, col_sugestao = st.columns([2, 1])
with col_preco:
    if "_preco_override" in st.session_state:
        st.session_state["preco_cobrado"] = st.session_state.pop("_preco_override")
    preco_cobrado = st.number_input(
        "Valor cobrado do cliente (R$)", min_value=0.0, step=50.0,
        format="%.2f", key="preco_cobrado",
        help="Valor cobrado do cliente. O preço sugerido garante 40% de margem.",
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
efeito_js = "none"
st.divider()

if km <= 0:
    st.markdown(
        f'<div style="text-align:center;padding:32px 24px;color:{c["border"]};'
        f'font-family:Geologica,sans-serif;font-weight:600;">'
        f'Informe a distância em km para calcular a precificação.</div>',
        unsafe_allow_html=True,
    )
else:
    resultado  = calcular_margem(preco_cobrado, km, custo_km, pedagio, estacionamento, agua, desp_motorista)
    margem     = resultado["margem"]
    pct        = resultado["pct_i10"]
    margem_ok  = margem >= margem_minima

    # Para dias de semana: também verifica se margem absoluta está abaixo do mínimo
    # (O que for menor — pct ou absoluto — aciona o vermelho)
    abaixo_abs = (not is_fds) and (margem < margem_minima)

    # Prioridade: danger > red > neutro > green > celebrate
    if pct < 0.30:
        price_class = "g-result-price danger"
        efeito_js   = "danger"
    elif pct < 0.35 or abaixo_abs:
        price_class = "g-result-price red"
        efeito_js   = "none"
    elif pct > 0.50:
        price_class = "g-result-price celebrate"
        efeito_js   = "confetti"
    elif pct > 0.40:
        price_class = "g-result-price green"
        efeito_js   = "none"
    else:
        price_class = "g-result-price"   # 35–40 %: neutro
        efeito_js   = "none"

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
        for nome, pct_val in DETALHAMENTO_COMISSOES.items():
            linhas.append((f"  └ {nome}", -resultado["receita_bruta"] * pct_val, True))
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
        if desp_motorista:
            linhas.append(("Despesas do motorista", -desp_motorista, True))
        linhas.append(("= Margem de contribuição", resultado["margem"], False))

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
        volta_fmt = (data_volta.strftime("%d/%m/%Y") + " às " + hora_volta.strftime("%H:%M")
                     if tipo_viagem == "Ida e Volta" else "—")
        dur_fmt = ""
        if tipo_viagem == "Ida e Volta" and duracao_horas > 0:
            h = int(duracao_horas); m = int((duracao_horas - h) * 60)
            dur_fmt = f"{h}h{m:02d}" if m else f"{h}h"

        info = [
            ("Tipo de serviço", tipo_viagem),
            ("Saída",           saida_fmt),
            ("Volta",           volta_fmt),
            ("Duração",         dur_fmt or "—"),
            ("Dias de serviço", str(num_dias)),
            ("Veículo",         veiculo),
            ("Distância",       f"{km:.1f} km"),
        ]
        if desp_motorista:
            info.append(("Despesas motorista", f"R$ {desp_motorista:,.2f}"))
        html_info = "".join(
            f'<div class="g-breakdown-row"><span class="g-breakdown-label">{k}</span>'
            f'<span class="g-breakdown-value">{v}</span></div>'
            for k, v in info
        )
        st.markdown(f'<div style="padding:4px 0">{html_info}</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="g-footer">Gooden · Conduzindo tranquilidade</div>', unsafe_allow_html=True)

# ── Efeitos JS (Enter → próximo campo + confetti/danger) ─────────────────────
_efeito = efeito_js if km > 0 else "none"
components.html(f"""
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
<script>
(function() {{
    var EFEITO = "{_efeito}";

    /* ── Navegação Enter ── */
    function instalarNavegacao() {{
        var doc = window.parent.document;
        var seletores = ['input[type="number"]','input[type="text"]',
                         'input[type="date"]','input[type="time"]'].join(',');
        function aoApertar(e) {{
            if (e.key !== 'Enter') return;
            var todos = Array.from(doc.querySelectorAll(seletores))
                            .filter(function(el) {{ return !el.disabled && el.offsetParent !== null; }});
            var idx = todos.indexOf(e.target);
            if (idx >= 0 && idx < todos.length - 1) {{
                e.preventDefault();
                todos[idx + 1].focus();
                todos[idx + 1].select();
            }}
        }}
        doc.querySelectorAll(seletores).forEach(function(el) {{
            el.removeEventListener('keydown', aoApertar);
            el.addEventListener('keydown', aoApertar);
        }});
    }}

    /* ── Confetti ── */
    function dispararConfetti() {{
        if (typeof confetti === 'undefined') return;
        var end = Date.now() + 2200;
        var colors = ['#5450FF','#4ADE80','#FACC15','#F472B6','#38BDF8'];
        (function frame() {{
            confetti({{ particleCount: 5, angle: 60,  spread: 55, origin: {{ x: 0 }}, colors: colors }});
            confetti({{ particleCount: 5, angle: 120, spread: 55, origin: {{ x: 1 }}, colors: colors }});
            if (Date.now() < end) requestAnimationFrame(frame);
        }})();
    }}

    /* ── Danger overlay ── */
    function mostrarPerigo() {{
        var doc = window.parent.document;
        if (doc.getElementById('_gooden_danger_overlay')) return;
        var el = doc.createElement('div');
        el.id = '_gooden_danger_overlay';
        el.style.cssText = 'position:fixed;top:16px;right:16px;z-index:9999;' +
            'font-size:2rem;animation:_dng 0.8s ease-in-out infinite;pointer-events:none;';
        el.textContent = '🚫';
        var style = doc.createElement('style');
        style.textContent = '@keyframes _dng{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.3;transform:scale(1.3)}}}}';
        doc.head.appendChild(style);
        doc.body.appendChild(el);
        setTimeout(function() {{ if (el.parentNode) el.parentNode.removeChild(el); }}, 3000);
    }}

    function removerPerigo() {{
        var doc = window.parent.document;
        var el = doc.getElementById('_gooden_danger_overlay');
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }}

    /* ── Init ── */
    setTimeout(function() {{
        instalarNavegacao();
        if      (EFEITO === 'confetti') dispararConfetti();
        else if (EFEITO === 'danger')   mostrarPerigo();
        else                            removerPerigo();
    }}, 400);

    var obs = new MutationObserver(function() {{ setTimeout(instalarNavegacao, 200); }});
    obs.observe(window.parent.document.body, {{ childList: true, subtree: true }});
}})();
</script>
""", height=0)
