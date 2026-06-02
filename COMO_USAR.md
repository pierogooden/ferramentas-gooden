# Como Usar — Extrator de Listas de Passageiros

## 1. Pré-requisitos

### Instalar Python
1. Acesse https://www.python.org/downloads/
2. Baixe o instalador do Python 3.11 ou superior
3. **IMPORTANTE:** Na instalação, marque a caixa "Add Python to PATH"
4. Clique em "Install Now"

### Instalar as dependências
Após instalar o Python, abra o Prompt de Comando (CMD) nesta pasta e execute:
```
pip install anthropic openpyxl
```

### Configurar a chave da API Anthropic
Defina sua chave como variável de ambiente (no CMD):
```
set ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```
Ou de forma permanente no Windows:
- Pesquise "variáveis de ambiente" no menu Iniciar
- Em "Variáveis do usuário", clique em "Novo"
- Nome: `ANTHROPIC_API_KEY`
- Valor: sua chave de API

---

## 2. Como usar

### Processar TODAS as imagens da pasta
```
python extrair_lista.py
```
Gera o arquivo `passageiros.xlsx` com todos os dados.

### Processar imagens específicas
```
python extrair_lista.py "WhatsApp Image 2026-06-01 at 13.29.01.jpeg"
```

### Processar múltiplas imagens com nome personalizado
```
python extrair_lista.py imagem1.jpg imagem2.jpg --saida resultado_junho.xlsx
```

---

## 3. O que o sistema extrai

Para cada passageiro na lista, o sistema tenta extrair:
- **Nome Completo**
- **Número de Documento** (RG, CPF, passaporte ou outro)
- **Observações** (qualquer informação adicional visível)
- **Fonte** (qual imagem originou o dado)

---

## 4. Formatos de imagem suportados
- `.jpg` / `.jpeg`
- `.png`
- `.gif`
- `.webp`

---

## 5. Dicas para melhores resultados
- Use imagens com boa iluminação
- A imagem deve estar em foco (sem borrão)
- Evite reflexos e sombras sobre o texto
- Quanto maior a resolução, mais precisa a extração
