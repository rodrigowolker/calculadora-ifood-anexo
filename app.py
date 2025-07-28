"""
Aplicativo Streamlit aprimorado para precificação de itens no iFood.

Este app é uma evolução da calculadora original criada com ChatGPT.  Ele foi
projetado para atender às necessidades de gestores de restaurantes que
precisam calcular o preço ideal de venda no iFood considerando diversas
variáveis, como as taxas do plano do iFood e custos logísticos.  Esta
versão removeu campos menos utilizados (impostos, margem de lucro,
custo de embalagem e desconto), simplificando o preenchimento.  Além do
cálculo individual, o aplicativo mantém um histórico das precificações
realizadas, permite importar um cardápio em formato CSV para
precificação em lote e exportar os resultados em CSV ou PDF.

Para executar este aplicativo, é necessário ter o Streamlit instalado no
ambiente.  Execute-o com o comando:

    streamlit run app.py

O código utiliza apenas bibliotecas amplamente disponíveis (pandas e
fpdf).  Caso a biblioteca fpdf não esteja instalada, ela pode ser
adicionada via pip (pip install fpdf).
"""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from fpdf import FPDF  # type: ignore
import streamlit as st


def calcular_preco_ifood(
    preco_cardapio: float,
    taxa_ifood: float,
    impostos: float,
    margem: float,
    custo_embalagem: float,
    custo_logistica: float,
    desconto: float,
) -> Optional[float]:
    """Calcula o preço sugerido no iFood considerando diversas variáveis.

    O cálculo baseia‑se na seguinte fórmula:

        preco_sugerido = custo_total / (1 - taxa_total)

    onde custo_total = preco_cardapio + custo_embalagem + custo_logistica
          taxa_total  = (taxa_ifood + impostos + margem - desconto) / 100

    Args:
        preco_cardapio: preço do produto no cardápio físico.
        taxa_ifood: soma das taxas do iFood em porcentagem.
        impostos: porcentagem de impostos (ICMS, ISS etc.).
        margem: margem de lucro desejada em porcentagem.
        custo_embalagem: custo unitário de embalagem.
        custo_logistica: custo unitário de entrega ou logística.
        desconto: percentual de desconto (usar valor negativo para acréscimo).

    Returns:
        O preço sugerido.  Retorna ``None`` se a soma das porcentagens
        resultar em 100 % ou mais.
    """
    custo_total = preco_cardapio + custo_embalagem + custo_logistica
    taxa_total = (taxa_ifood + impostos + margem - desconto) / 100.0
    # Evitar divisão por zero ou porcentagens absurdas
    if taxa_total >= 1.0:
        return None
    preco_sugerido = custo_total / (1.0 - taxa_total)
    return round(preco_sugerido, 2)


def gerar_pdf_tabela(df: pd.DataFrame, titulo: str) -> bytes:
    """Gera um PDF simples a partir de um DataFrame.

    O PDF contém um título e uma tabela com as colunas do DataFrame.  Para
    maximizar a compatibilidade com diferentes versões da biblioteca
    ``fpdf``/``fpdf2``, esta função tenta primeiro produzir o PDF via
    ``dest='S'`` (que normalmente retorna uma string ou bytes).  Caso
    ocorra algum erro (ou o retorno não seja um tipo esperado), ele
    recorre a gravar o conteúdo em um ``BytesIO``.  No final, sempre
    retorna um objeto ``bytes``, conforme exigido pela API do
    ``streamlit.download_button``.

    Args:
        df: DataFrame a ser exportado.
        titulo: título exibido no cabeçalho do PDF.

    Returns:
        Conteúdo do PDF em bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    # Calcula largura das colunas proporcionalmente ao número de colunas
    col_width = pdf.w / (len(df.columns) + 1)
    # Cabeçalho da tabela
    for col in df.columns:
        pdf.cell(col_width, 8, txt=str(col), border=1, align="C")
    pdf.ln()
    # Linhas da tabela
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 8, txt=str(item), border=1, align="C")
        pdf.ln()
    # Tenta gerar o conteúdo via dest='S' (string) para maior compatibilidade
    try:
        pdf_content = pdf.output(dest="S")  # type: ignore[no-untyped-call]
        # O método pode retornar ``str`` (em python 2/algumas versões) ou ``bytes``.
        if isinstance(pdf_content, bytes):
            return pdf_content
        elif isinstance(pdf_content, str):
            # Converte string para bytes usando latin-1
            return pdf_content.encode("latin-1")
        else:
            # Qualquer outro tipo não é esperado; convertemos via buffer
            raise TypeError
    except Exception:
        # Fallback: grava em buffer e lê bytes
        buffer = io.BytesIO()
        pdf.output(buffer)  # type: ignore[no-untyped-call]
        return buffer.getvalue()


def carregar_csv_em_lote(csv_bytes: bytes) -> pd.DataFrame:
    """Lê um CSV enviado pelo usuário e retorna um DataFrame.

    Espera‑se que o CSV contenha ao menos as colunas ``nome_produto`` e
    ``preco_cardapio``.  Os campos opcionais mais relevantes são
    ``taxa_ifood`` e ``custo_logistica``.  As colunas relacionadas a
    impostos, margens, embalagens ou descontos são preservadas apenas
    por compatibilidade, mas seus valores serão ignorados.  Valores
    ausentes serão preenchidos com padrões.

    Args:
        csv_bytes: arquivo CSV em bytes.

    Returns:
        DataFrame com as colunas necessárias preenchidas.
    """
    df = pd.read_csv(io.BytesIO(csv_bytes))
    # Renomear colunas para padrão interno
    df.columns = [c.strip().lower() for c in df.columns]
    # Garante a presença das colunas esperadas
    expected_cols = {
        "nome_produto": "nome_produto",
        "preco_cardapio": "preco_cardapio",
        "taxa_ifood": "taxa_ifood",
        "impostos": "impostos",
        "margem": "margem",
        "custo_embalagem": "custo_embalagem",
        "custo_logistica": "custo_logistica",
        "desconto": "desconto",
    }
    for col in expected_cols.values():
        if col not in df.columns:
            df[col] = 0.0 if col != "nome_produto" else ""
    return df[list(expected_cols.values())].copy()


def main() -> None:
    st.set_page_config(
        page_title="Calculadora de Precificação iFood",
        layout="centered",
        page_icon="favanexo.png",
    )

    # Exibe o logo da Agência no topo, se o arquivo existir
    # Para evitar erros caso a imagem não esteja presente, usamos um bloco try/except.
    try:
        st.image("Ativo 1.png", width=180)
    except Exception:
        pass

    st.title("Calculadora de Precificação iFood")
    st.markdown(
        "Esta ferramenta ajuda a calcular o preço ideal de venda no iFood, "
        "considerando o plano escolhido e custos logísticos. Você também pode "
        "carregar um arquivo CSV para precificar vários itens de uma vez."
    )

    # Estilos CSS personalizados para botões e componentes
    st.markdown(
        """
        <style>
        /* Botão Calcular dentro do formulário */
        form button[type="submit"] {
            background-color: #333333 !important;
            color: #FFFFFF !important;
            width: 100% !important;
        }
        /* Primeiro botão de download (Baixar CSV) */
        div[data-testid="stDownloadButton"]:first-of-type button {
            background-color: #007BFF !important;
            color: #FFFFFF !important;
            width: 100% !important;
        }
        /* Segundo botão de download (Baixar PDF) */
        div[data-testid="stDownloadButton"]:nth-of-type(2) button {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            width: 100% !important;
        }
        /* Botão para limpar histórico */
        div[data-testid="stButton"] button {
            background-color: #DC3545 !important;
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inicializa histórico na sessão
    if "historico" not in st.session_state:
        # O histórico agora contém apenas as colunas essenciais: nome, preço de cardápio,
        # taxa do iFood, custo de logística e preço sugerido.  Campos de impostos,
        # margem, embalagem e desconto foram removidos conforme solicitado.
        st.session_state.historico = pd.DataFrame(
            columns=[
                "Nome do Produto",
                "Preço Cardápio (R$)",
                "Taxa iFood (%)",
                "Custo Logística (R$)",
                "Preço Sugerido iFood (R$)",
            ]
        )

    with st.expander("Precificação individual", expanded=True):
        with st.form("form_precificacao"):
            nome_produto = st.text_input("Nome do Produto", max_chars=100)
            preco_cardapio = st.number_input(
                "Preço do produto no cardápio (R$)", min_value=0.0, format="%.2f"
            )
            # Seleção de plano do iFood
            planos_ifood = {
                "Básico (27%)": 27.0,
                "Intermediário (21%)": 21.0,
                "Parceiro de Entrega (16.5%)": 16.5,
                "Próprio (12%)": 12.0,
                "Personalizado": None,
            }
            plano_escolhido = st.selectbox(
                "Plano do iFood",
                options=list(planos_ifood.keys()),
                index=0,
            )
            if planos_ifood[plano_escolhido] is None:
                taxa_ifood = st.number_input(
                    "Taxa do iFood (%)", min_value=0.0, max_value=100.0, value=27.0, step=0.1
                )
            else:
                taxa_ifood = planos_ifood[plano_escolhido]
            # Os campos de impostos, margem, custo de embalagem e desconto foram removidos.
            # Permanece apenas o custo de logística/entrega para permitir ajuste do valor total.
            custo_logistica = st.number_input(
                "Custo de Logística/Entrega (R$)", min_value=0.0, value=0.0, step=0.01, format="%.2f"
            )
            calcular_btn = st.form_submit_button("Calcular", use_container_width=True)

        if calcular_btn:
            # Validação básica
            if not nome_produto.strip():
                st.warning("Por favor, informe o nome do produto.")
            else:
                # Com os campos de impostos, margem, embalagem e desconto removidos,
                # passamos zeros para essas variáveis.  O custo de logística é o
                # único acréscimo ao preço de cardápio considerado no cálculo.
                preco_sugerido = calcular_preco_ifood(
                    preco_cardapio=preco_cardapio,
                    taxa_ifood=taxa_ifood,
                    impostos=0.0,
                    margem=0.0,
                    custo_embalagem=0.0,
                    custo_logistica=custo_logistica,
                    desconto=0.0,
                )
                if preco_sugerido is None:
                    st.error(
                        "A taxa do iFood deve ser menor que 100 %. Ajuste o valor para obter um preço válido."
                    )
                else:
                    st.success(f"Preço sugerido no iFood: R$ {preco_sugerido:.2f}")
                    # Tabela de detalhamento com apenas os itens relevantes
                    detalhamento = pd.DataFrame(
                        {
                            "Item": [
                                "Preço no cardápio",
                                "Custo logística",
                                "Taxa iFood",
                                "Preço sugerido",
                            ],
                            "Valor": [
                                f"R$ {preco_cardapio:.2f}",
                                f"R$ {custo_logistica:.2f}",
                                f"{taxa_ifood:.1f} %",
                                f"R$ {preco_sugerido:.2f}",
                            ],
                        }
                    )
                    with st.expander("Ver detalhamento do cálculo"):
                        st.table(detalhamento)
                    # Atualiza histórico
                    nova_linha = pd.DataFrame(
                        {
                            "Nome do Produto": [nome_produto],
                            "Preço Cardápio (R$)": [round(preco_cardapio, 2)],
                            "Taxa iFood (%)": [round(taxa_ifood, 2)],
                            "Custo Logística (R$)": [round(custo_logistica, 2)],
                            "Preço Sugerido iFood (R$)": [preco_sugerido],
                        }
                    )
                    st.session_state.historico = pd.concat(
                        [st.session_state.historico, nova_linha], ignore_index=True
                    )

    # Exibe histórico caso exista
    if not st.session_state.historico.empty:
        st.subheader("Histórico de precificações")
        st.dataframe(st.session_state.historico, use_container_width=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            # Botão de download de CSV
            csv_bytes = st.session_state.historico.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Baixar CSV",
                data=csv_bytes,
                file_name="historico_precificacao.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col2:
            # Botão de download de PDF
            pdf_bytes = gerar_pdf_tabela(
                st.session_state.historico,
                titulo="Histórico de precificação iFood",
            )
            st.download_button(
                label="Baixar PDF",
                data=pdf_bytes,
                file_name="historico_precificacao.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col3:
            # Botão para limpar histórico
            if st.button("Limpar Histórico"):
                # Limpa o histórico
                st.session_state.historico = st.session_state.historico.iloc[0:0]
                # Recarrega a interface para refletir a mudança.  Utiliza st.rerun(),
                # que é a API oficial a partir das versões recentes.  Se não
                # estiver disponível, ignora a chamada silenciosamente.
                try:
                    # type: ignore[attr-defined]
                    st.rerun()  # Streamlit 1.27+
                except Exception:
                    # Fallback: não força recarregar para versões antigas
                    pass

    st.markdown("---")

    with st.expander("Precificação em lote (importação de CSV)"):
        st.markdown(
            "Você pode carregar um arquivo CSV com as colunas: ``nome_produto``, ``preco_cardapio`` e "
            "``taxa_ifood`` (opcional) e ``custo_logistica`` (opcional).\n"
            "Se uma coluna não existir ou estiver vazia, será utilizado o valor definido no formulário."
        )
        arquivo = st.file_uploader(
            "Selecione o arquivo CSV", type=["csv"], accept_multiple_files=False
        )
        if arquivo is not None:
            try:
                df = carregar_csv_em_lote(arquivo.getvalue())
                # Aplica valores padrão se estiverem vazios (0) usando os valores definidos no formulário
                df["taxa_ifood"] = df["taxa_ifood"].replace(0, taxa_ifood)
                df["custo_logistica"] = df["custo_logistica"].replace(0, custo_logistica)
                # Para colunas que não são utilizadas (impostos, margem, embalagem, desconto),
                # substituímos por zero para não interferir no cálculo.
                if "impostos" in df.columns:
                    df["impostos"] = 0.0
                if "margem" in df.columns:
                    df["margem"] = 0.0
                if "custo_embalagem" in df.columns:
                    df["custo_embalagem"] = 0.0
                if "desconto" in df.columns:
                    df["desconto"] = 0.0
                # Calcula para cada linha
                precos = []
                for _, linha in df.iterrows():
                    preco = calcular_preco_ifood(
                        preco_cardapio=float(linha.get("preco_cardapio", 0)),
                        taxa_ifood=float(linha.get("taxa_ifood", taxa_ifood)),
                        impostos=0.0,
                        margem=0.0,
                        custo_embalagem=0.0,
                        custo_logistica=float(linha.get("custo_logistica", custo_logistica)),
                        desconto=0.0,
                    )
                    precos.append(preco if preco is not None else 0.0)
                df_result = df[["nome_produto", "preco_cardapio", "taxa_ifood", "custo_logistica"]].copy()
                df_result["preco_sugerido_ifood"] = precos
                st.success("Arquivo processado com sucesso!")
                st.dataframe(df_result, use_container_width=True)
                # Download resultante
                csv_lote = df_result.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Baixar resultados (CSV)",
                    data=csv_lote,
                    file_name="precificacao_lote.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

    # Rodapé
    st.markdown("---")
    st.markdown("Desenvolvido por **Agência Anexo**.")


if __name__ == "__main__":
    main()