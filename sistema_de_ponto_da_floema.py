import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials

# --- Configuração das credenciais e autorização ---

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # Carrega as credenciais do secrets do Streamlit
    credenciais_dict = dict(st.secrets["gcp_credentials"])
    # Corrige as quebras de linha do private_key
    credenciais_dict["private_key"] = credenciais_dict["private_key"].replace("\\n", "\n")
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=SCOPES)
    cliente = gspread.authorize(credenciais)
except Exception as e:
    st.error(f"Erro na autenticação das credenciais: {e}")
    st.stop()

# --- Abrir a planilha e a aba ---

PLANILHA_KEY = "1tae8vNgryWDpTSINk6RYJq9uAzc6M3s6oNQMtlImnXk"

try:
    planilha = cliente.open_by_key(PLANILHA_KEY)
    aba = planilha.worksheet("Dados")
except Exception as e:
    st.error(f"Erro ao abrir a planilha ou aba: {e}")
    st.stop()

# --- Dados fixos dos colaboradores ---

colaboradores = {
    "Fernando": 33,
    "Gustavo": 44,
    "Clara": 45,
    "Eveline": 56,
    "Valmir": 37
}
df_colaboradores = pd.DataFrame(list(colaboradores.items()), columns=["Nome", "Codigo"])

# Colunas de horários na planilha, iniciando na coluna D (4)
colunas_ponto = [
    "Entrada",
    "Horário de saída",
    "Horário de volta do almoço",
    "Horário de saída não programada",
    "Horário de volta da saída não programada",
    "Saída"
]

# --- Configuração da página Streamlit ---

st.set_page_config(page_title="Registro de Ponto", page_icon="🕒")
st.title("🕒 Sistema de Registro de Ponto")

if "registrado" not in st.session_state:
    st.session_state.registrado = False

if not st.session_state.registrado:
    codigo = st.number_input("Insira seu código de colaborador:", step=1, format="%d")
    lista_codigos = df_colaboradores["Codigo"].values

    if codigo in lista_codigos:
        nome = df_colaboradores.loc[df_colaboradores["Codigo"] == codigo, "Nome"].values[0]
        st.success(f"Bem-vindo, {nome}!")

        confirma = st.radio("Confirma seu nome?", ["Sim", "Não"])

        if confirma == "Sim":
            opcao = st.selectbox("Escolha uma opção:", [
                "1 - Entrada",
                "2 - Saída para o almoço",
                "3 - Volta para o almoço",
                "4 - Saída não programada",
                "5 - Volta da saída não programada",
                "6 - Saída"
            ])

            if st.button("Registrar"):
                try:
                    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
                    data = agora.strftime("%d/%m/%Y")
                    hora = agora.strftime("%H:%M:%S")

                    campos = {
                        "1": "Entrada",
                        "2": "Horário de saída",
                        "3": "Horário de volta do almoço",
                        "4": "Horário de saída não programada",
                        "5": "Horário de volta da saída não programada",
                        "6": "Saída"
                    }
                    chave = opcao.split(" ")[0]
                    campo_selecionado = campos[chave]

                    registros = aba.get_all_records()

                    linha_para_atualizar = None
                    for i, registro in enumerate(registros, start=2):  # linha 2 é a primeira após cabeçalho
                        if registro["Nome"] == nome and registro["Data"] == data:
                            linha_para_atualizar = i
                            break

                    if linha_para_atualizar:
                        # Coluna da planilha onde atualizar o horário (D=4, E=5, ...)
                        indice_coluna = colunas_ponto.index(campo_selecionado) + 4
                        aba.update_cell(linha_para_atualizar, indice_coluna, hora)
                    else:
                        nova_linha = [nome, codigo, data] + [""] * len(colunas_ponto)
                        nova_linha[3 + colunas_ponto.index(campo_selecionado)] = hora
                        aba.append_row(nova_linha, value_input_option="USER_ENTERED")

                    st.success(f"{campo_selecionado} registrada com sucesso às {hora}!")
                    st.session_state.registrado = True

                except Exception as e:
                    st.error(f"Erro ao registrar ponto: {e}")

        else:
            st.warning("Por favor, contate o PCP para corrigir o código.")
    else:
        if codigo != 0:
            st.error("Código não encontrado. Tente novamente.")
else:
    if st.button("Registrar outro colaborador"):
        st.session_state.registrado = False
