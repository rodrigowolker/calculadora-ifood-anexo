"""
Aplicativo Streamlit aprimorado para precificação de itens no iFood.

Este app é uma evolução da calculadora original criada com ChatGPT.  Ele foi
projetado para atender às necessidades de gestores de restaurantes que
precisam calcular o preço ideal de venda no iFood considerando diversas
variáveis, como as taxas do plano do iFood, impostos, margem de lucro,
custo de embalagem, custos logísticos e descontos/promos.  Além do cálculo
individual, o aplicativo mantém um histórico das precificações realizadas,
permite importar um cardápio em formato CSV para precificação em lote e
exportar os resultados em CSV ou PDF.

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

    O PDF contém um título e uma tabela com as colunas do DataFrame.  Este
    método utiliza a biblioteca FPDF para criar o PDF em memória.  A saída
    é retornada em formato ``bytes`` para ser usada diretamente em
    `st.download_button`.

    Args:
        df: DataFrame a ser exportado.
        titulo: título exibido no cabeçalho do PDF.

    Returns:
        Conteúdo do PDF em bytes.  O método detecta se o retorno de
        ``pdf.output(dest='S')`` é uma string (nas versões antigas da
        biblioteca) ou bytes (em fpdf2) e converte adequadamente.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    # Largura das colunas baseada no número de colunas
    col_width = pdf.w / (len(df.columns) + 1)
    # Cabeçalho
    for col in df.columns:
        pdf.cell(col_width, 8, txt=str(col), border=1, align="C")
    pdf.ln()
    # Linhas
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 8, txt=str(item), border=1, align="C")
        pdf.ln()
    # Nas versões antigas de fpdf, output(dest='S') retorna string; em fpdf2 retorna bytes
    raw = pdf.output(dest="S")
    if isinstance(raw, str):
        return raw.encode("latin-1")
    return raw


def carregar_csv_em_lote(csv_bytes: bytes) -> pd.DataFrame:
    """Lê um CSV enviado pelo usuário e retorna um DataFrame.

    Espera‑se que o CSV contenha ao menos as colunas ``nome_produto`` e
    ``preco_cardapio``.  Outras colunas opcionais são ``taxa_ifood``,
    ``impostos``, ``margem``, ``custo_embalagem``, ``custo_logistica`` e
    ``desconto``.  Valores ausentes serão preenchidos com padrões.

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
        page_title="Calculadora iFood Aprimorada",
        layout="centered",
        page_icon="🍔",
    )

    st.title("Calculadora de Precificação iFood - Versão Aprimorada")
    st.markdown(
        "Esta ferramenta ajuda a calcular o preço ideal de venda no iFood, "
        "considerando plano do iFood, impostos, margem de lucro, custo de "
        "embalagem, logística e descontos. Você também pode carregar um "
        "arquivo CSV para precificar vários itens de uma vez."
    )

    # Inicializa histórico na sessão
    if "historico" not in st.session_state:
        st.session_state.historico = pd.DataFrame(
            columns=[
                "Nome do Produto",
                "Preço Cardápio (R$)",
                "Taxa iFood (%)",
                "Impostos (%)",
                "Margem (%)",
                "Custo Embalagem (R$)",
                "Custo Logística (R$)",
                "Desconto (%)",
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
            impostos = st.number_input(
                "Impostos (%) (ICMS/ISS)", min_value=0.0, max_value=100.0, value=5.0, step=0.1
            )
            margem = st.number_input(
                "Margem de Lucro (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1
            )
            custo_embalagem = st.number_input(
                "Custo de Embalagem (R$)", min_value=0.0, value=0.0, step=0.01, format="%.2f"
            )
            custo_logistica = st.number_input(
                "Custo de Logística/Entrega (R$)", min_value=0.0, value=0.0, step=0.01, format="%.2f"
            )
            desconto = st.number_input(
                "Desconto/Acréscimo (%) (use negativo para acréscimo)",
                min_value=-100.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
            )
            calcular_btn = st.form_submit_button("Calcular")

        if calcular_btn:
            # Validação básica
            if not nome_produto.strip():
                st.warning("Por favor, informe o nome do produto.")
            else:
                preco_sugerido = calcular_preco_ifood(
                    preco_cardapio=preco_cardapio,
                    taxa_ifood=taxa_ifood,
                    impostos=impostos,
                    margem=margem,
                    custo_embalagem=custo_embalagem,
                    custo_logistica=custo_logistica,
                    desconto=desconto,
                )
                if preco_sugerido is None:
                    st.error(
                        "A soma das porcentagens de taxa do iFood, impostos, margem e desconto é maior ou igual a 100 %. "
                        "Ajuste os valores para obter um preço válido."
                    )
                else:
                    st.success(f"Preço sugerido no iFood: R$ {preco_sugerido:.2f}")
                    # Tabela de detalhamento
                    detalhamento = pd.DataFrame(
                        {
                            "Item": [
                                "Preço no cardápio",
                                "Custo embalagem",
                                "Custo logística",
                                "Taxa iFood",
                                "Impostos",
                                "Margem de lucro",
                                "Desconto/Acréscimo",
                                "Preço sugerido",
                            ],
                            "Valor": [
                                f"R$ {preco_cardapio:.2f}",
                                f"R$ {custo_embalagem:.2f}",
                                f"R$ {custo_logistica:.2f}",
                                f"{taxa_ifood:.1f} %",
                                f"{impostos:.1f} %",
                                f"{margem:.1f} %",
                                f"{desconto:.1f} %",
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
                            "Impostos (%)": [round(impostos, 2)],
                            "Margem (%)": [round(margem, 2)],
                            "Custo Embalagem (R$)": [round(custo_embalagem, 2)],
                            "Custo Logística (R$)": [round(custo_logistica, 2)],
                            "Desconto (%)": [round(desconto, 2)],
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
            )
        with col3:
            # Botão para limpar histórico
            if st.button("Limpar Histórico"):
                st.session_state.historico = st.session_state.historico.iloc[0:0]
                st.experimental_rerun()

    st.markdown("---")

    with st.expander("Precificação em lote (importação de CSV)"):
        st.markdown(
            "Você pode carregar um arquivo CSV com as colunas: ``nome_produto``, ``preco_cardapio``, "
            "``taxa_ifood`` (opcional), ``impostos`` (opcional), ``margem`` (opcional), "
            "``custo_embalagem`` (opcional), ``custo_logistica`` (opcional) e ``desconto`` (opcional).\n"
            "Se uma coluna não existir, o valor padrão será 0 ou o definido no formulário."
        )
        arquivo = st.file_uploader(
            "Selecione o arquivo CSV", type=["csv"], accept_multiple_files=False
        )
        if arquivo is not None:
            try:
                df = carregar_csv_em_lote(arquivo.getvalue())
                # Aplica valores padrão se estiverem vazios
                # Usa valores atuais do formulário individual como padrão
                # Nota: estas variáveis são capturadas no escopo externo
                df["taxa_ifood"] = df["taxa_ifood"].replace(0, taxa_ifood)
                df["impostos"] = df["impostos"].replace(0, impostos)
                df["margem"] = df["margem"].replace(0, margem)
                df["custo_embalagem"] = df["custo_embalagem"].replace(0, custo_embalagem)
                df["custo_logistica"] = df["custo_logistica"].replace(0, custo_logistica)
                df["desconto"] = df["desconto"].replace(0, desconto)
                # Calcula para cada linha
                precos = []
                for _, linha in df.iterrows():
                    preco = calcular_preco_ifood(
                        preco_cardapio=float(linha["preco_cardapio"]),
                        taxa_ifood=float(linha["taxa_ifood"]),
                        impostos=float(linha["impostos"]),
                        margem=float(linha["margem"]),
                        custo_embalagem=float(linha["custo_embalagem"]),
                        custo_logistica=float(linha["custo_logistica"]),
                        desconto=float(linha["desconto"]),
                    )
                    precos.append(preco if preco is not None else 0.0)
                df_result = df.copy()
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


if __name__ == "__main__":
    main()