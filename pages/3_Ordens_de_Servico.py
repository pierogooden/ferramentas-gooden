"""
Página: Ordens de Serviço
Extrai dados das fotos das OS e gera um arquivo Excel com 3 abas para download.
"""
import base64
import json
import sys
from pathlib import Path
from datetime import date, datetime

import streamlit as st
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.design import inject_css, render_header
from utils.planilhas_os import (
    get_data, get_valor_viagem, parse_prefixo,
    gerar_download,
)

st.set_page_config(
    page_title="Canivete Gooden · OS",
    page_icon="🚌",
    layout="wide",
)
inject_css()
render_header("Ordens de Serviço", "Extração automática → Planilhas Excel", page_key="os")

# ── Configuração da API ───────────────────────────────────────────────────────
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    import os
    api_key = os.getenv("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ GROQ_API_KEY não configurada em .streamlit/secrets.toml")
    st.stop()

client = Groq(api_key=api_key)

# ── Inicializa session_state ───────────────────────────────────────────────────
if "dados_os" not in st.session_state:
    st.session_state.dados_os = []

# ── Extração via Groq Vision ──────────────────────────────────────────────────

_PROMPT = """Analise esta imagem de uma ORDEM DE SERVIÇO (OS) de empresa de ônibus e extraia TODOS os campos abaixo.
Retorne SOMENTE um objeto JSON válido, sem texto adicional, sem markdown.

Campos a extrair:
- num_os: número da OS (campo "N°" no canto superior direito)
- contratante: nome do contratante (campo CONTRATANTE)
- motorista_matricula: número antes do hífen no campo MOTORISTA (ex: "002404" → "002404")
- motorista_nome: nome após o hífen no campo MOTORISTA (ex: "CARLOS LUIZ DA SILVA")
- carro: número do carro (campo CARRO, incluindo zeros à esquerda)
- destino: cidade/local de destino
- data_saida: data de saída no formato DD/MM/AAAA (campo SAÍDA → DIA)
- hora_saida: hora de saída no formato HH:MM (campo SAÍDA → HORA)
- data_retorno: data de retorno no formato DD/MM/AAAA (campo RETORNO → DIA)
- hora_retorno: hora de retorno no formato HH:MM (campo RETORNO → HORA)
- saida_garagem_km: odômetro "Saída da Garagem" (número inteiro)
- saida_garagem_hora: horário "Saída da Garagem" no formato HH:MM
- chegada_cliente_km: odômetro "Chegada ao Cliente" (número inteiro)
- chegada_cliente_hora: horário "Chegada ao Cliente" no formato HH:MM
- saida_cliente_km: odômetro "Saída do Cliente" (número inteiro)
- saida_cliente_hora: horário "Saída do Cliente" no formato HH:MM
- chegada_destino_km: odômetro "Chegada ao Destino" (número inteiro)
- chegada_destino_hora: horário "Chegada ao Destino" no formato HH:MM
- saida_destino_km: odômetro "Saída do Destino" (número inteiro)
- saida_destino_hora: horário "Saída do Destino" no formato HH:MM
- chegada_origem_km: odômetro "Chegada à Origem" (número inteiro)
- chegada_origem_hora: horário "Chegada à Origem" no formato HH:MM
- chegada_garagem_km: odômetro "Chegada à Garagem" (número inteiro)
- chegada_garagem_hora: horário "Chegada à Garagem" no formato HH:MM
- comissao: valor numérico da COMISSÃO no rodapé da OS (apenas o número, ex: 286.19). Se não houver, use null.

Atenção:
- Horários acima de 24h (ex: "26:50") converta para formato normal (02:50)
- Odômetros são números inteiros sem pontos
- Se um campo não estiver visível, use null

Exemplo de resposta: {"num_os":"8086","contratante":"FEI","motorista_matricula":"002404",...}"""


def extrair_os(imagem_bytes: bytes, media_type: str) -> dict:
    b64 = base64.standard_b64encode(imagem_bytes).decode()
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                {"type": "text", "text": _PROMPT},
            ],
        }],
        max_tokens=1500,
        temperature=0,
    )
    texto = resp.choices[0].message.content.strip()
    if texto.startswith("```"):
        linhas = texto.split("\n")
        texto = "\n".join(linhas[1:-1] if linhas[-1].strip() == "```" else linhas[1:])
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return {}


def enriquecer(d: dict) -> dict:
    carro = d.get("carro") or d.get("prefixo", "0")
    d["prefixo"] = parse_prefixo(carro)
    d["valor_viagem"] = get_valor_viagem(d.get("comissao"))
    return d


MEDIA_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".png": "image/png", ".webp": "image/webp"}

# ════════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════════════════════════════════════════

aba_upload, aba_revisao, aba_download = st.tabs([
    "📤 Upload e Extração",
    "🔍 Revisão dos Dados",
    "📥 Gerar Arquivo",
])

# ════════════════════════════════════════════════════════════════════════════════
# ABA 1: UPLOAD E EXTRAÇÃO
# ════════════════════════════════════════════════════════════════════════════════
with aba_upload:
    st.markdown("### 📤 Envio das Ordens de Serviço")
    st.caption(
        "Envie as fotos das OS em lote. "
        "O sistema extrai automaticamente todos os campos e adiciona à fila de revisão."
    )

    arquivos = st.file_uploader(
        "Selecione as imagens das OS",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if arquivos:
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            extrair = st.button(
                f"⚡ Extrair {len(arquivos)} OS",
                type="primary",
                use_container_width=True,
            )

        if extrair:
            novos = 0
            erros = []
            barra = st.progress(0, text="Processando imagens…")

            for i, arq in enumerate(arquivos):
                sufixo = Path(arq.name).suffix.lower()
                mt = MEDIA_TYPES.get(sufixo, "image/jpeg")

                with st.spinner(f"Analisando {arq.name}…"):
                    raw = extrair_os(arq.read(), mt)

                if not raw.get("num_os"):
                    erros.append(arq.name)
                else:
                    d = enriquecer(raw)
                    d["_arquivo"] = arq.name
                    chave = (str(d.get("num_os")), d.get("prefixo"))
                    if chave not in [(str(x.get("num_os")), x.get("prefixo"))
                                     for x in st.session_state.dados_os]:
                        st.session_state.dados_os.append(d)
                        novos += 1

                barra.progress((i + 1) / len(arquivos), text=f"{arq.name} ✓")

            barra.empty()
            if novos:
                st.success(f"✅ {novos} OS extraída(s). Vá para a aba **Revisão**.")
            if erros:
                st.warning(f"⚠️ Não foi possível extrair: {', '.join(erros)}")

    else:
        st.info("Carregue as fotos das Ordens de Serviço acima para começar.")

    if st.session_state.dados_os:
        st.markdown(f"**{len(st.session_state.dados_os)} OS na fila** · "
                    "Acesse a aba **Revisão** para conferir.")
        if st.button("🗑️ Limpar fila", type="secondary"):
            st.session_state.dados_os = []
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# ABA 2: REVISÃO
# ════════════════════════════════════════════════════════════════════════════════
with aba_revisao:
    st.markdown("### 🔍 Revisão dos dados extraídos")

    if not st.session_state.dados_os:
        st.info("Nenhuma OS extraída ainda. Use a aba **Upload e Extração** primeiro.")
    else:
        st.caption("Confira os campos abaixo. Clique em qualquer célula para editar.")

        campos_exibir = [
            "num_os", "contratante", "motorista_matricula", "motorista_nome",
            "prefixo", "destino", "data_saida", "hora_saida",
            "data_retorno", "hora_retorno", "comissao", "valor_viagem",
            "saida_garagem_km", "saida_garagem_hora",
            "chegada_cliente_km", "chegada_cliente_hora",
            "saida_cliente_km", "saida_cliente_hora",
            "chegada_destino_km", "chegada_destino_hora",
            "saida_destino_km", "saida_destino_hora",
            "chegada_origem_km", "chegada_origem_hora",
            "chegada_garagem_km", "chegada_garagem_hora",
        ]

        import pandas as pd
        df = pd.DataFrame([
            {c: d.get(c, "") for c in campos_exibir}
            for d in st.session_state.dados_os
        ])

        df_editado = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_os",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar edições", type="primary"):
                novos = []
                for i, row in df_editado.iterrows():
                    d = row.to_dict()
                    if i < len(st.session_state.dados_os):
                        extra = {k: v for k, v in st.session_state.dados_os[i].items()
                                 if k not in campos_exibir}
                        d.update(extra)
                    d = enriquecer(d)
                    novos.append(d)
                st.session_state.dados_os = novos
                st.success("Edições salvas. Vá para **Gerar Arquivo**.")
        with col2:
            if st.button("🗑️ Remover todos", type="secondary"):
                st.session_state.dados_os = []
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# ABA 3: GERAR ARQUIVO PARA DOWNLOAD
# ════════════════════════════════════════════════════════════════════════════════
with aba_download:
    st.markdown("### 📥 Gerar arquivo Excel")

    if not st.session_state.dados_os:
        st.info("Fila vazia. Extraia as OS primeiro na aba **Upload e Extração**.")
    else:
        dados = st.session_state.dados_os
        n = len(dados)

        st.markdown(
            f"**{n} OS pronta(s) para exportar.** "
            "O arquivo gerado terá 3 abas: **Km Turismo**, **Análise de Resultados** e **Comissão dos Motoristas**."
        )

        for d in dados:
            st.markdown(
                f"- OS **{d.get('num_os')}** · {d.get('motorista_nome', '?')} · "
                f"{d.get('data_saida', '?')} · R$ {d.get('valor_viagem', '—')}"
            )

        st.divider()

        datas_validas = [get_data(d.get("data_saida")) for d in dados if d.get("data_saida")]
        if datas_validas:
            meses_pt = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                        "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            dt = datas_validas[0]
            nome_arquivo = f"OS_{meses_pt[dt.month]}_{dt.year}.xlsx"
        else:
            nome_arquivo = "OS_export.xlsx"

        if st.button("⚡ Gerar arquivo", type="primary"):
            with st.spinner("Gerando planilha…"):
                xlsx_bytes = gerar_download(dados)

            st.success("✅ Arquivo pronto!")
            st.download_button(
                label=f"⬇  Baixar {nome_arquivo}",
                data=xlsx_bytes,
                file_name=nome_arquivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="g-footer">Gooden · Conduzindo tranquilidade</div>',
            unsafe_allow_html=True)
