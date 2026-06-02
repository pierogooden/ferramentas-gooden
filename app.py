import base64
import io
import json
from pathlib import Path

import streamlit as st
from groq import Groq
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Gooden · Listas de Passageiros",
    page_icon="🚌",
    layout="centered",
)

# ── Identidade Visual Gooden ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geologica:wght@400;700;900&family=Abhaya+Libre:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Abhaya Libre', serif;
}

/* Header com logo */
.gooden-header {
    background: #020066;
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.gooden-logo {
    font-family: 'Geologica', sans-serif;
    font-weight: 900;
    font-size: 2.2rem;
    color: white;
    letter-spacing: -1px;
    line-height: 1;
}
.gooden-tagline {
    font-family: 'Abhaya Libre', serif;
    color: #ACB0F8;
    font-size: 0.95rem;
    margin-top: 4px;
}
.gooden-divider {
    width: 3px;
    height: 48px;
    background: #5450FF;
    border-radius: 2px;
    flex-shrink: 0;
}
.gooden-title {
    font-family: 'Geologica', sans-serif;
    font-weight: 700;
    color: #020066;
    font-size: 1.1rem;
    margin: 0;
    line-height: 1.2;
}
.gooden-subtitle {
    color: #5450FF;
    font-size: 0.85rem;
    margin-top: 2px;
}

/* Cards de resultado */
.result-card {
    background: white;
    border: 1.5px solid #ACB0F8;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.result-header {
    font-family: 'Geologica', sans-serif;
    font-weight: 700;
    color: #020066;
    font-size: 0.95rem;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.badge-ok {
    background: #ACB0F8;
    color: #020066;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    font-family: 'Geologica', sans-serif;
}

/* Botão de download */
.stDownloadButton > button {
    background: #020066 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Geologica', sans-serif !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
.stDownloadButton > button:hover {
    background: #3500D8 !important;
}

/* Upload area */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #ACB0F8 !important;
    border-radius: 10px !important;
    background: #f8f8ff !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1.5px solid #ACB0F8 !important;
    border-radius: 10px !important;
    overflow: hidden;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #5450FF !important;
}

/* Sucesso */
.stSuccess {
    background: #f0f0ff !important;
    color: #020066 !important;
    border-left: 3px solid #5450FF !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #ACB0F8;
    border-radius: 8px;
    overflow: hidden;
}

/* Footer */
.gooden-footer {
    text-align: center;
    color: #ACB0F8;
    font-size: 0.8rem;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #f0f0ff;
    font-family: 'Abhaya Libre', serif;
}
</style>

<div class="gooden-header">
    <div class="gooden-logo">Gooden</div>
    <div class="gooden-divider"></div>
    <div>
        <div class="gooden-title">Listas de Passageiros</div>
        <div class="gooden-subtitle">Extração automática · Conferência simplificada</div>
    </div>
</div>
""", unsafe_allow_html=True)

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


# ── Funções ─────────────────────────────────────────────────────────────────

def extrair_passageiros(client: Groq, imagem_bytes: bytes, media_type: str) -> list[dict]:
    imagem_b64 = base64.standard_b64encode(imagem_bytes).decode("utf-8")
    prompt = """Analise esta imagem de uma lista de passageiros e extraia TODOS os dados visíveis.

Para cada passageiro encontrado, retorne um objeto JSON com:
- "nome": nome completo do passageiro
- "documento": número do documento (RG, CPF, passaporte ou qualquer número de identificação presente)
- "observacao": qualquer informação adicional relevante (opcional, deixe vazio se não houver)

Se um campo não estiver visível ou legível, use null.

Responda SOMENTE com um array JSON válido, sem texto adicional, sem markdown, sem explicações.
Exemplo: [{"nome": "João Silva", "documento": "12.345.678-9", "observacao": ""}, ...]

Se a imagem não contiver lista de passageiros ou não for legível, retorne: []"""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{imagem_b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        max_tokens=4096,
        temperature=0,
    )
    texto = response.choices[0].message.content.strip()

    if texto.startswith("```"):
        linhas = texto.split("\n")
        texto = "\n".join(linhas[1:-1] if linhas[-1].strip() == "```" else linhas[1:])

    try:
        resultado = json.loads(texto)
        return resultado if isinstance(resultado, list) else []
    except json.JSONDecodeError:
        return []


def gerar_xlsx(passageiros: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Passageiros"

    # Cabeçalho com cores Gooden
    cor_cabecalho = "020066"
    fonte_cabecalho = Font(name="Calibri", bold=True, color="FFFFFF", size=12)
    preenchimento_cabecalho = PatternFill(fill_type="solid", fgColor=cor_cabecalho)
    cor_linha_par = "F0F0FF"
    preenchimento_par = PatternFill(fill_type="solid", fgColor=cor_linha_par)

    cabecalhos = ["✓", "#", "Nome Completo", "Documento", "Observação"]
    larguras   = [5,   6,   40,              20,           30]

    for col, (cab, larg) in enumerate(zip(cabecalhos, larguras), start=1):
        cel = ws.cell(row=1, column=col, value=cab)
        cel.font = fonte_cabecalho
        cel.fill = preenchimento_cabecalho
        cel.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[cel.column_letter].width = larg

    ws.row_dimensions[1].height = 22

    for i, p in enumerate(passageiros, start=1):
        linha = i + 1
        preen = preenchimento_par if linha % 2 == 0 else None

        cel_check = ws.cell(row=linha, column=1, value="☐")
        cel_check.alignment = Alignment(horizontal="center", vertical="center")
        cel_check.font = Font(name="Calibri", size=14)

        for col, valor in enumerate(
            [i, p.get("nome") or "", p.get("documento") or "", p.get("observacao") or ""],
            start=2,
        ):
            cel = ws.cell(row=linha, column=col, value=valor)
            cel.alignment = Alignment(vertical="center", wrap_text=True)

        if preen:
            for col in range(1, 6):
                ws.cell(row=linha, column=col).fill = preen

        ws.row_dimensions[linha].height = 18

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"B1:{ws.cell(row=1, column=len(cabecalhos)).coordinate}"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Interface ────────────────────────────────────────────────────────────────

# Chave da API
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    import os
    api_key = os.getenv("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ Chave GROQ_API_KEY não configurada.")
    st.stop()

client = Groq(api_key=api_key)

# Upload
arquivos = st.file_uploader(
    "Selecione as imagens das listas de passageiros",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Cada imagem gera uma planilha separada para download.",
)

if not arquivos:
    st.markdown("""
    <div style='text-align:center; padding: 40px 20px; color: #ACB0F8;'>
        <div style='font-size: 2.5rem; margin-bottom: 12px;'>📋</div>
        <div style='font-family: Geologica, sans-serif; font-weight: 700; color: #020066; font-size: 1rem;'>
            Carregue as imagens para começar
        </div>
        <div style='font-size: 0.85rem; margin-top: 6px;'>
            Suporta JPG, PNG e WEBP · Uma planilha por imagem
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.divider()

for arquivo in arquivos:
    sufixo = Path(arquivo.name).suffix.lower()
    media_type = MEDIA_TYPES.get(sufixo, "image/jpeg")
    nome_base = Path(arquivo.name).stem

    with st.expander(f"📄  {arquivo.name}", expanded=True):
        col_img, col_info = st.columns([1, 2])

        with col_img:
            st.image(arquivo, use_container_width=True)

        with col_info:
            with st.spinner("Extraindo passageiros..."):
                imagem_bytes = arquivo.read()
                passageiros = extrair_passageiros(client, imagem_bytes, media_type)

            if not passageiros:
                st.warning("Nenhum passageiro encontrado nesta imagem.")
            else:
                st.success(f"**{len(passageiros)} passageiro(s)** identificado(s)")

                st.dataframe(
                    data=[{
                        "✓": "☐",
                        "#": i + 1,
                        "Nome": p.get("nome") or "—",
                        "Documento": p.get("documento") or "—",
                        "Obs.": p.get("observacao") or "",
                    } for i, p in enumerate(passageiros)],
                    use_container_width=True,
                    hide_index=True,
                )

                xlsx_bytes = gerar_xlsx(passageiros)
                st.download_button(
                    label=f"⬇  Baixar  {nome_base}.xlsx",
                    data=xlsx_bytes,
                    file_name=f"{nome_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

st.markdown("""
<div class="gooden-footer">
    Gooden · Conduzindo tranquilidade
</div>
""", unsafe_allow_html=True)
