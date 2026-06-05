import base64
import io
import json
from pathlib import Path

import fitz  # pymupdf
import streamlit as st
from groq import Groq
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

st.set_page_config(
    page_title="Gooden · Listas de Passageiros",
    page_icon="🚌",
    layout="centered",
)

# ── Design System Gooden ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geologica:wght@300;400;600;700;900&family=Abhaya+Libre:wght@400;600&display=swap');

/* Reset & base */
html, body, [class*="css"], .stApp {
    font-family: 'Abhaya Libre', Georgia, serif;
    background-color: #FAFBFF !important;
}

/* Esconde elementos desnecessários do Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 760px !important; }

/* ── HEADER ── */
.g-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 24px 0;
    margin-bottom: 8px;
    border-bottom: 1.5px solid #E8EAFF;
}
.g-logo {
    font-family: 'Geologica', sans-serif;
    font-weight: 900;
    font-size: 2rem;
    color: #020066;
    letter-spacing: -1.5px;
    line-height: 1;
}
.g-logo span {
    display: inline-block;
    width: 6px;
    height: 6px;
    background: #5450FF;
    border-radius: 50%;
    margin-left: 3px;
    vertical-align: super;
}
.g-header-right {
    text-align: right;
}
.g-header-title {
    font-family: 'Geologica', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    color: #020066;
    letter-spacing: 0.02em;
}
.g-header-sub {
    font-family: 'Abhaya Libre', serif;
    font-size: 0.78rem;
    color: #ACB0F8;
    margin-top: 1px;
}

/* ── SEÇÃO ── */
.g-section-label {
    font-family: 'Geologica', sans-serif;
    font-weight: 600;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ACB0F8;
    margin-bottom: 10px;
}

/* ── UPLOAD ── */
[data-testid="stFileUploaderDropzone"] {
    background: white !important;
    border: 1.5px dashed #C4C7F8 !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #5450FF !important;
}
[data-testid="stFileUploaderDropzone"] p {
    font-family: 'Abhaya Libre', serif !important;
    color: #8386C8 !important;
}

/* ── EMPTY STATE ── */
.g-empty {
    text-align: center;
    padding: 48px 24px;
    color: #C4C7F8;
}
.g-empty-icon {
    font-size: 2.8rem;
    margin-bottom: 12px;
    opacity: 0.7;
}
.g-empty-title {
    font-family: 'Geologica', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: #8386C8;
    margin-bottom: 4px;
}
.g-empty-sub {
    font-size: 0.82rem;
    color: #C4C7F8;
}

/* ── RESULTADO CARD ── */
.g-card {
    background: white;
    border: 1px solid #EAECFF;
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 20px;
    box-shadow: 0 2px 16px rgba(84,80,255,0.06);
}
.g-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}
.g-card-name {
    font-family: 'Geologica', sans-serif;
    font-weight: 700;
    font-size: 0.9rem;
    color: #020066;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 320px;
}
.g-badge {
    font-family: 'Geologica', sans-serif;
    font-weight: 700;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    background: #F0F1FF;
    color: #5450FF;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
}
.g-badge-warn {
    background: #FFF4E8;
    color: #E8901A;
}

/* ── DIVIDER ── */
hr[data-testid="stDivider"] {
    border-color: #EAECFF !important;
    margin: 24px 0 !important;
}

/* ── BOTÃO DOWNLOAD ── */
.stDownloadButton > button {
    background: #020066 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Geologica', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em !important;
    padding: 10px 24px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(2,0,102,0.18) !important;
}
.stDownloadButton > button:hover {
    background: #3500D8 !important;
    box-shadow: 0 4px 16px rgba(53,0,216,0.28) !important;
    transform: translateY(-1px) !important;
}
.stDownloadButton > button:active {
    transform: translateY(0) !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: white !important;
    border: 1px solid #EAECFF !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 16px rgba(84,80,255,0.06) !important;
    overflow: hidden !important;
    margin-top: 16px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Geologica', sans-serif !important;
    font-weight: 700 !important;
    color: #020066 !important;
    font-size: 0.88rem !important;
    padding: 14px 20px !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #EAECFF !important;
}

/* ── ALERTS ── */
.stSuccess {
    background: #F0F1FF !important;
    color: #020066 !important;
    border-left: 3px solid #5450FF !important;
    border-radius: 8px !important;
    font-family: 'Abhaya Libre', serif !important;
}
.stWarning {
    background: #FFF8F0 !important;
    border-left: 3px solid #FFC48B !important;
    border-radius: 8px !important;
}

/* ── SPINNER ── */
.stSpinner > div > div {
    border-top-color: #5450FF !important;
}

/* ── FOOTER ── */
.g-footer {
    text-align: center;
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid #EAECFF;
    font-family: 'Geologica', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #D0D2F0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="g-header">
    <div class="g-logo">Gooden<span></span></div>
    <div class="g-header-right">
        <div class="g-header-title">Listas de Passageiros</div>
        <div class="g-header-sub">Extração automática · Conferência simplificada</div>
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


def pdf_para_imagens(pdf_bytes: bytes) -> list[bytes]:
    """Converte cada página do PDF em PNG (bytes) para envio à API."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    paginas = []
    for pagina in doc:
        # Renderiza em alta resolução (2x para melhor OCR)
        mat = fitz.Matrix(2.0, 2.0)
        pix = pagina.get_pixmap(matrix=mat)
        paginas.append(pix.tobytes("png"))
    doc.close()
    return paginas


# ── Funções ──────────────────────────────────────────────────────────────────
def extrair_passageiros(client: Groq, imagem_bytes: bytes, media_type: str) -> list[dict]:
    imagem_b64 = base64.standard_b64encode(imagem_bytes).decode("utf-8")
    prompt = """Analise esta imagem de uma lista de passageiros e extraia TODOS os dados visíveis.

Para cada passageiro encontrado, retorne um objeto JSON com:
- "nome": nome completo do passageiro
- "documento": SOMENTE os dígitos e pontuação do número (ex: "12.345.678-9" ou "123.456.789-00"). NÃO inclua o tipo do documento (não escreva "RG", "CPF", "Doc", "Passaporte" etc.). Se houver mais de um número, retorne apenas o principal.
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
        if not isinstance(resultado, list):
            return []
        # Remove rótulos de tipo de documento que possam ter vindo junto
        import re
        prefixos = re.compile(
            r"^\s*(rg|cpf|doc\.?|documento|passaporte|cnh|rne|ctps|pis|nit"
            r"|id|identidade|n[°º]?\.?)\s*[:\-]?\s*",
            re.IGNORECASE,
        )
        for p in resultado:
            if p.get("documento"):
                p["documento"] = prefixos.sub("", str(p["documento"])).strip()
        return resultado
    except json.JSONDecodeError:
        return []


def gerar_xlsx(passageiros: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Passageiros"

    cor_header = "020066"
    cor_par    = "F4F5FF"
    f_header   = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    fill_header = PatternFill(fill_type="solid", fgColor=cor_header)
    fill_par    = PatternFill(fill_type="solid", fgColor=cor_par)

    cabecalhos = ["✓", "#", "Nome Completo", "Documento", "Observação"]
    larguras   = [5,   6,   42,              20,           28]

    for col, (cab, larg) in enumerate(zip(cabecalhos, larguras), start=1):
        cel = ws.cell(row=1, column=col, value=cab)
        cel.font = f_header
        cel.fill = fill_header
        cel.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[cel.column_letter].width = larg
    ws.row_dimensions[1].height = 22

    for i, p in enumerate(passageiros, start=1):
        linha = i + 1
        ws.cell(row=linha, column=1, value="☐").alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=linha, column=1).font = Font(name="Calibri", size=13)
        for col, val in enumerate([i, p.get("nome") or "", p.get("documento") or "", p.get("observacao") or ""], start=2):
            cel = ws.cell(row=linha, column=col, value=val)
            cel.alignment = Alignment(vertical="center", wrap_text=True)
        if linha % 2 == 0:
            for col in range(1, 6):
                ws.cell(row=linha, column=col).fill = fill_par
        ws.row_dimensions[linha].height = 18

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"B1:{ws.cell(row=1, column=5).coordinate}"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── API ───────────────────────────────────────────────────────────────────────
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    import os
    api_key = os.getenv("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ Chave GROQ_API_KEY não configurada nos Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown('<div class="g-section-label">Imagens das listas</div>', unsafe_allow_html=True)

arquivos = st.file_uploader(
    "Selecione ou arraste os arquivos",
    type=["jpg", "jpeg", "png", "webp", "pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not arquivos:
    st.markdown("""
    <div class="g-empty">
        <div class="g-empty-icon">📋</div>
        <div class="g-empty-title">Nenhum arquivo carregado</div>
        <div class="g-empty-sub">Suporta JPG, PNG, WEBP e PDF · Uma planilha gerada por arquivo</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Resultados ────────────────────────────────────────────────────────────────
st.markdown(f'<div class="g-section-label" style="margin-top:28px">{len(arquivos)} arquivo(s) carregado(s)</div>', unsafe_allow_html=True)

for arquivo in arquivos:
    sufixo    = Path(arquivo.name).suffix.lower()
    nome_base = Path(arquivo.name).stem
    eh_pdf    = sufixo == ".pdf"
    icone     = "📑" if eh_pdf else "📄"

    with st.expander(f"{icone}  {arquivo.name}", expanded=True):
        arquivo_bytes = arquivo.read()

        # ── PDF: converte páginas em imagens ──
        if eh_pdf:
            with st.spinner("Convertendo páginas do PDF..."):
                paginas = pdf_para_imagens(arquivo_bytes)

            n_pags = len(paginas)
            st.markdown(
                f'<div style="font-family:Geologica,sans-serif;font-size:0.78rem;'
                f'color:#ACB0F8;margin-bottom:12px">'
                f'PDF com {n_pags} página(s)</div>',
                unsafe_allow_html=True,
            )

            todos = []
            for idx, pag_bytes in enumerate(paginas, start=1):
                with st.spinner(f"Analisando página {idx}/{n_pags}..."):
                    resultado = extrair_passageiros(client, pag_bytes, "image/png")
                    todos.extend(resultado)

            passageiros = todos

        # ── Imagem normal ──
        else:
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image(arquivo_bytes, use_container_width=True)
            with col_info:
                with st.spinner("Analisando imagem..."):
                    passageiros = extrair_passageiros(client, arquivo_bytes, MEDIA_TYPES.get(sufixo, "image/jpeg"))

        # ── Resultado ──
        if not passageiros:
            st.warning("Nenhum passageiro encontrado neste arquivo.")
        else:
            n = len(passageiros)

            if eh_pdf:
                st.markdown(f"""
                <div style="margin-bottom:12px">
                    <span style="font-family:'Geologica',sans-serif;font-weight:700;
                                 font-size:1.6rem;color:#020066;">{n}</span>
                    <span style="font-family:'Abhaya Libre',serif;color:#8386C8;
                                 font-size:0.9rem;margin-left:6px;">passageiro(s) em {len(paginas)} página(s)</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="margin-bottom:12px">
                    <span style="font-family:'Geologica',sans-serif;font-weight:700;
                                 font-size:1.6rem;color:#020066;">{n}</span>
                    <span style="font-family:'Abhaya Libre',serif;color:#8386C8;
                                 font-size:0.9rem;margin-left:6px;">passageiro(s) identificado(s)</span>
                </div>
                """, unsafe_allow_html=True)

            st.dataframe(
                [{
                    "✓": "☐",
                    "#": i + 1,
                    "Nome": p.get("nome") or "—",
                    "Documento": p.get("documento") or "—",
                    "Obs.": p.get("observacao") or "",
                } for i, p in enumerate(passageiros)],
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                label=f"⬇  Baixar  {nome_base}.xlsx",
                data=gerar_xlsx(passageiros),
                file_name=f"{nome_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="g-footer">Gooden · Conduzindo tranquilidade</div>', unsafe_allow_html=True)
