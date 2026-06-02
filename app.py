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
    page_title="Extrator de Listas de Passageiros",
    page_icon="📋",
    layout="centered",
)

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


# ── Funções de extração ─────────────────────────────────────────────────────

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
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{imagem_b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
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

    cor_cabecalho = "2B5EA7"
    fonte_cabecalho = Font(name="Calibri", bold=True, color="FFFFFF", size=12)
    preenchimento_cabecalho = PatternFill(fill_type="solid", fgColor=cor_cabecalho)
    cor_linha_par = "DCE6F1"
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


# ── Interface ───────────────────────────────────────────────────────────────

st.title("📋 Extrator de Listas de Passageiros")
st.caption("Envie fotos de listas e baixe as planilhas prontas para conferência.")

# Chave da API — lida dos secrets do Streamlit Cloud (ou variável de ambiente local)
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    import os
    api_key = os.getenv("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ Chave GROQ_API_KEY não configurada. Adicione nos Secrets do Streamlit Cloud.")
    st.stop()

client = Groq(api_key=api_key)

# Upload
arquivos = st.file_uploader(
    "Selecione as imagens das listas",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Cada imagem gera uma planilha separada.",
)

if not arquivos:
    st.info("👆 Carregue uma ou mais imagens para começar.")
    st.stop()

st.divider()

for arquivo in arquivos:
    sufixo = Path(arquivo.name).suffix.lower()
    media_type = MEDIA_TYPES.get(sufixo, "image/jpeg")
    nome_base = Path(arquivo.name).stem

    with st.expander(f"📄 {arquivo.name}", expanded=True):
        col_img, col_info = st.columns([1, 2])

        with col_img:
            st.image(arquivo, use_container_width=True)

        with col_info:
            with st.spinner("Extraindo dados..."):
                imagem_bytes = arquivo.read()
                passageiros = extrair_passageiros(client, imagem_bytes, media_type)

            if not passageiros:
                st.warning("Nenhum passageiro encontrado nesta imagem.")
            else:
                st.success(f"✅ {len(passageiros)} passageiro(s) encontrado(s)")

                # Tabela de preview
                st.dataframe(
                    data=[
                        {
                            "✓": "☐",
                            "#": i + 1,
                            "Nome": p.get("nome") or "—",
                            "Documento": p.get("documento") or "—",
                            "Observação": p.get("observacao") or "",
                        }
                        for i, p in enumerate(passageiros)
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                # Botão de download
                xlsx_bytes = gerar_xlsx(passageiros)
                st.download_button(
                    label=f"⬇️ Baixar {nome_base}.xlsx",
                    data=xlsx_bytes,
                    file_name=f"{nome_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
