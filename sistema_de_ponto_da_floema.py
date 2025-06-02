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

# --- Função para garantir cabeçalho ---

colunas_ponto = [
    "Entrada",
    "Horário de saída",
    "Horário de volta do almoço",
    "Horário de saída não programada",
    "Horário de volta da saída não programada",
    "Saída"
]

def garantir_cabecalho(worksheet):
    cabecalho_esperado = ["Nome", "Codigo", "Data"] + colunas_ponto
    primeira_linha = worksheet.row_values(1)
    if primeira_linha != cabecalho_esperado:
        worksheet.update('A1', [cabecalho_esperado])
        st.info("Cabeçalho criado na planilha!")

garantir_cabecalho(aba)

# --- Dados fixos dos colaboradores ---

colaboradores = {
    "Fernando": 33,
    "Gustavo": 44,
    "Clara": 45,
    "Eveline": 56,
    "Valmir": 37
}
df_colaboradores = pd.DataFrame(list(colaboradores.items()), columns=["Nome", "Codigo"])

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
            campos = {
                "1": "Entrada",
                "2": "Horário de saída",
                "3": "Horário de volta do almoço",
                "4": "Horário de saída não programada",
                "5": "Horário de volta da saída não programada",
                "6": "Saída"
            }

            agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
            data = agora.strftime("%d/%m/%Y")
            hora = agora.strftime("%H:%M:%S")
            registros = aba.get_all_records()

            registro_hoje = next((r for r in registros if r["Nome"] == nome and r["Data"] == data), None)

            opcoes_disponiveis = []
            for chave, campo in campos.items():
                if not registro_hoje or not registro_hoje.get(campo):
                    opcoes_disponiveis.append(f"{chave} - {campo}")

            if opcoes_disponiveis:
                opcao = st.selectbox("Escolha uma opção:", opcoes_disponiveis)

                if st.button("Registrar"):
                    try:
                        chave = opcao.split(" ")[0]
                        campo_selecionado = campos[chave]

                        linha_para_atualizar = None
                        for i, registro in enumerate(registros, start=2):  # começa na linha 2
                            if registro["Nome"] == nome and registro["Data"] == data:
                                linha_para_atualizar = i
                                break

                        if linha_para_atualizar:
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
                st.info("✅ Todos os pontos já foram registrados para hoje.")
        else:
            st.warning("Por favor, contate o PCP para corrigir o código.")
    else:
        if codigo != 0:
            st.error("Código não encontrado. Tente novamente.")
else:
    if st.button("Novo registro"):
        st.session_state.registrado = False
