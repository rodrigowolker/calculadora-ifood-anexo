import streamlit as st
from streamlit_javascript import st_javascript
from PIL import Image
import base64
import io

st.set_page_config(page_title="Calculadora iFood - Anexo", layout="centered")

# CSS Apple-like
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #fff;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 20px;
    }
    .btn-primary {
        background-color: #1c1c1c;
        color: white;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
        padding: 14px;
        width: 100%;
        border: none;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #000;
    }
    .result-card {
        background-color: #1eb540;
        padding: 45px;
        border-radius: 20px;
        text-align: center;
        margin-top: 20px;
    }
    .result-price {
        font-size: 6em;
        font-weight: 700;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# Logo e título
st.markdown('<div class="logo-container"><h1>Calculadora de Precificação iFood</h1></div>', unsafe_allow_html=True)
st.write("Preencha os dados abaixo para calcular o preço ideal no cardápio:")

# Estado inicial
if "calculado" not in st.session_state:
    st.session_state.calculado = False
    st.session_state.resultado = None

if not st.session_state.calculado:
    # HTML + JS para inputs
    js_code = """
        const formatNumber = (el) => {
            el.addEventListener('input', function() {
                let value = this.value.replace(/\\D/g, '');
                if (value) {
                    this.value = (parseInt(value) / 100).toLocaleString('pt-BR', {minimumFractionDigits: 2});
                }
            });
        };

        const fields = {
            preco: document.getElementById('preco'),
            taxa: document.getElementById('taxa'),
            impostos: document.getElementById('impostos'),
            margem: document.getElementById('margem')
        };

        Object.values(fields).forEach(el => {
            el.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9,]/g, '');
            });
        });

        formatNumber(fields.preco);

        const dados = {
            preco: fields.preco.value,
            taxa: fields.taxa.value,
            impostos: fields.impostos.value,
            margem: fields.margem.value
        };

        return dados;
    """

    # Renderizar formulário HTML
    st.markdown("""
    <div style="max-width:400px;margin:auto;">
        <div style="margin-bottom:15px;">
            <label>Preço do produto no cardápio (R$)</label>
            <input id="preco" type="text" placeholder="Ex.: 25,90" style="padding:12px;font-size:18px;border-radius:10px;border:1px solid #ccc;width:100%;">
        </div>
        <div style="margin-bottom:15px;">
            <label>Todas as Taxas do iFood (%)</label>
            <input id="taxa" type="text" placeholder="Ex.: 23" style="padding:12px;font-size:18px;border-radius:10px;border:1px solid #ccc;width:100%;">
        </div>
        <div style="margin-bottom:15px;">
            <label>Impostos (%) (opcional)</label>
            <input id="impostos" type="text" placeholder="Ex.: 5" style="padding:12px;font-size:18px;border-radius:10px;border:1px solid #ccc;width:100%;">
        </div>
        <div style="margin-bottom:20px;">
            <label>Margem de Lucro (%) (opcional)</label>
            <input id="margem" type="text" placeholder="Ex.: 20" style="padding:12px;font-size:18px;border-radius:10px;border:1px solid #ccc;width:100%;">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Botão calcular
    if st.button("Calcular"):
        dados = st_javascript(js_code)
        preco = float(dados["preco"].replace(".", "").replace(",", ".")) if dados["preco"] else 0
        taxa = float(dados["taxa"].replace(",", ".")) / 100 if dados["taxa"] else 0
        impostos = float(dados["impostos"].replace(",", ".")) / 100 if dados["impostos"] else 0
        margem = float(dados["margem"].replace(",", ".")) / 100 if dados["margem"] else 0

        if preco > 0:
            resultado = preco / (1 - (taxa + impostos + margem))
            st.session_state.resultado = f"{resultado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.session_state.calculado = True
            st.experimental_rerun()
        else:
            st.error("Informe o preço do produto.")
else:
    # Exibir resultado
    st.markdown(f"""
        <div class="result-card">
            <p class="result-price">R$ {st.session_state.resultado}</p>
        </div>
    """, unsafe_allow_html=True)

    # Botão Novo Cálculo
    if st.button("Novo Cálculo"):
        st.session_state.calculado = False
        st.session_state.resultado = None
        st.experimental_rerun()
