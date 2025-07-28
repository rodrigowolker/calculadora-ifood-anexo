import streamlit as st
import base64
import os
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Calculadora iFood - Anexo", layout="centered")

# ===== Função para carregar logo =====
def load_logo(logo_path="Ativo 1.png"):
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return None

logo_base64 = load_logo()

# ===== CSS Apple-like =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
    background-color: #fff;
}

.logo-container {
    text-align: center;
    margin-bottom: 15px;
}

h1 {
    text-align: center;
    margin-bottom: 10px;
}

p {
    text-align: center;
    color: #333;
}

input {
    padding: 12px;
    font-size: 18px;
    width: 100%;
    border: 1px solid #ccc;
    border-radius: 10px;
    margin-bottom: 15px;
}

button {
    width: 100%;
    background-color: #1c1c1c;
    color: #fff;
    padding: 14px;
    font-size: 18px;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    cursor: pointer;
}

button:hover {
    background-color: #000;
}

.result-box {
    background-color: #1eb540;
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    margin-top: 25px;
}

.result-text {
    font-size: 5em;
    font-weight: 700;
    color: #fff;
}

.history-table {
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ===== Exibir Logo =====
if logo_base64:
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
else:
    st.warning("Logo não encontrada! Certifique-se de que 'Ativo 1.png' está na mesma pasta que app.py.")

st.markdown("<h1>Calculadora de Precificação iFood</h1>", unsafe_allow_html=True)
st.markdown("<p>Preencha os dados abaixo para calcular o preço ideal no cardápio.</p>", unsafe_allow_html=True)

# ===== Inicializar histórico =====
if "historico" not in st.session_state:
    st.session_state.historico = []

# ===== Formulário =====
with st.form("form_calculo"):
    nome_produto = st.text_input("Nome do Produto", placeholder="Ex.: X-Burger")
    preco = st.text_input("Preço do produto no cardápio (R$)", placeholder="Ex.: 10,00")
    taxa = st.text_input("Todas as Taxas do iFood (%)", placeholder="Ex.: 27")
    impostos = st.text_input("Impostos (%) (opcional)", placeholder="Ex.: 5")
    margem = st.text_input("Margem de Lucro (%) (opcional)", placeholder="Ex.: 20")

    calcular = st.form_submit_button("Calcular")

# ===== Cálculo =====
if calcular:
    try:
        preco_valor = float(preco.replace(".", "").replace(",", ".")) if preco else 0
        taxa_valor = float(taxa.replace(",", ".")) / 100 if taxa else 0
        impostos_valor = float(impostos.replace(",", ".")) / 100 if impostos else 0
        margem_valor = float(margem.replace(",", ".")) / 100 if margem else 0

        if preco_valor > 0 and nome_produto:
            preco_sugerido = preco_valor / (1 - (taxa_valor + impostos_valor + margem_valor))
            preco_formatado = f"R$ {preco_sugerido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Mostrar resultado
            st.markdown(f"""
                <div class="result-box">
                    <p class="result-text">{preco_formatado}</p>
                </div>
            """, unsafe_allow_html=True)

            # Salvar no histórico
            st.session_state.historico.append({
                "Nome do Produto": nome_produto,
                "Preço do Cardápio": f"R$ {preco_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Preço Sugerido iFood": preco_formatado
            })
        else:
            st.error("Preencha o nome do produto e o preço.")
    except ValueError:
        st.error("Por favor, insira apenas números válidos.")

# ===== Exibir histórico =====
if st.session_state.historico:
    st.subheader("Histórico de Cálculos")
    df = pd.DataFrame(st.session_state.historico)
    st.table(df)

    # Botão Download CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, sep=";")
    st.download_button("📥 Baixar CSV", data=csv_buffer.getvalue(), file_name="historico_precificacao.csv", mime="text/csv")

    # Botão Download PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 14)
    c.drawString(200, 750, "Histórico de Precificação")
    c.setFont("Helvetica", 12)
    y = 720
    for item in st.session_state.historico:
        c.drawString(50, y, f"{item['Nome do Produto']} | {item['Preço do Cardápio']} | {item['Preço Sugerido iFood']}")
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 750
    c.save()
    st.download_button("📄 Baixar PDF", data=pdf_buffer.getvalue(), file_name="historico_precificacao.pdf", mime="application/pdf")
