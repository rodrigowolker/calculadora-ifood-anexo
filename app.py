import streamlit as st
from PIL import Image
import base64
import io

st.set_page_config(page_title="Calculadora iFood - Anexo", layout="centered")

# CSS customizado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #f9f9f9;
    }

    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
    }

    .stTextInput input {
        font-size: 18px !important;
        height: 55px !important;
        padding-left: 15px;
    }

    .stButton button {
        background-color: #1c1c1c;
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 14px;
        font-size: 18px;
        width: 100%;
        margin-top: 15px;
    }
    .stButton button:hover {
        background-color: #000;
        transition: 0.3s;
    }

    .result-card {
        background-color: #1eb540;
        padding: 45px;
        border-radius: 20px;
        text-align: center;
        margin-top: 20px;
    }

    .result-price {
        font-size: 7em;
        font-weight: 700;
        color: #fff;
        margin: 0;
    }

    .footer-text {
        text-align: center;
        margin-top: 70px;
        font-size: 18px;
        color: #000;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Exibir logo
logo_path = "Ativo 1.png"
try:
    logo = Image.open(logo_path)
    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    b64_logo = base64.b64encode(buffer.getvalue()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{b64_logo}" width="180"></div>', unsafe_allow_html=True)
except:
    st.warning("Logo não encontrada, adicione 'Ativo 1.png' na mesma pasta.")

st.title("Calculadora de Precificação iFood")
st.write("Preencha os dados abaixo para calcular o preço ideal no cardápio.")

# Inputs
preco_cardapio = st.text_input("Preço do produto no cardápio (R$)", placeholder="Ex.: 25,90")
taxa_ifood = st.text_input("Todas as Taxas do iFood (%)", placeholder="Ex.: 23")
impostos = st.text_input("Impostos (%) (opcional)", placeholder="Ex.: 5")
margem = st.text_input("Margem de Lucro (%) (opcional)", placeholder="Ex.: 20")

# Estado
if "calculado" not in st.session_state:
    st.session_state.calculado = False

if not st.session_state.calculado:
    if st.button("Calcular"):
        try:
            preco_valor = float(preco_cardapio.replace(".", "").replace(",", ".")) if preco_cardapio else 0
            taxa_valor = float(taxa_ifood.replace(".", "").replace(",", ".")) / 100 if taxa_ifood else 0
            impostos_valor = float(impostos.replace(".", "").replace(",", ".")) / 100 if impostos else 0
            margem_valor = float(margem.replace(".", "").replace(",", ".")) / 100 if margem else 0

            if preco_valor > 0:
                preco_sugerido = preco_valor / (1 - (taxa_valor + impostos_valor + margem_valor))
                st.markdown(f"""
                    <div class="result-card">
                        <p class="result-price">R$ {preco_sugerido:,.2f}</p>
                    </div>
                """, unsafe_allow_html=True)
                st.session_state.calculado = True
            else:
                st.error("Informe pelo menos o preço do produto.")
        except ValueError:
            st.error("Preencha os campos corretamente usando números.")
else:
    if st.button("Novo Cálculo"):
        st.session_state.calculado = False
        st.experimental_rerun()

st.markdown('<p class="footer-text">Com a Anexo, você precifica o seu produto no iFood da forma correta.</p>', unsafe_allow_html=True)
