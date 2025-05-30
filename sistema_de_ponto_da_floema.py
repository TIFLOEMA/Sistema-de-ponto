import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

escopo = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credenciais_dict = st.secrets["gcp_credentials"]
# Corrige a chave privada para quebras de linha reais
credenciais_dict["private_key"] = credenciais_dict["private_key"].replace("\\n", "\n")

credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
cliente = gspread.authorize(credenciais)

# Abrir planilha e aba
planilha = cliente.open("Registro_Ponto")
aba = planilha.worksheet("Dados")

# Dados dos colaboradores fixos (pode ser extraído da planilha se preferir)
colaboradores = {
    "Fernando": 33,
    "Gustavo": 44,
    "Clara": 45,
    "Eveline": 56,
    "Valmir": 37
}

# Criar DataFrame dos colaboradores
Dados = pd.DataFrame(list(colaboradores.items()), columns=["Nome", "Codigo"])

# Colunas que armazenam os horários
colunas_ponto = [
    "Entrada", "Horário de saída", "Horário de volta do almoço",
    "Horário de saída não programada", "Horário de volta da saída não programada", "Saída"
]

# Configurar página
st.set_page_config(page_title="Registro de Ponto", page_icon="🕒")
st.title("🕒 Sistema de Registro de Ponto")

# Estado da sessão para controlar registro
if "registrado" not in st.session_state:
    st.session_state.registrado = False

if not st.session_state.registrado:
    codigo = st.number_input("Insira seu código de colaborador:", step=1, format="%d")
    lista_codigos = Dados["Codigo"].values

    if codigo in lista_codigos:
        nome = Dados.loc[Dados["Codigo"] == codigo, "Nome"].values[0]
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
                agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
                data = agora.date().strftime("%d/%m/%Y")
                hora = agora.time().strftime("%H:%M:%S")

                campos = {
                    "1": "Entrada",
                    "2": "Horário de saída",
                    "3": "Horário de volta do almoço",
                    "4": "Horário de saída não programada",
                    "5": "Horário de volta da saída não programada",
                    "6": "Saída"
                }

                campo_selecionado = campos[opcao.split(" ")[0]]

                # Buscar registros atuais na planilha
                registros = aba.get_all_records()

                # Procurar linha do colaborador na data atual
                linha_para_atualizar = None
                for i, registro in enumerate(registros, start=2):  # considerando que cabeçalho está na linha 1
                    if registro["Nome"] == nome and registro["Data"] == data:
                        linha_para_atualizar = i
                        break

                if linha_para_atualizar:
                    # Atualizar célula específica
                    # Colunas na planilha: A=Nome(1), B=Codigo(2), C=Data(3), colunas_ponto começam na D(4)
                    indice_coluna = colunas_ponto.index(campo_selecionado) + 4
                    aba.update_cell(linha_para_atualizar, indice_coluna, hora)
                else:
                    # Criar nova linha com nome, codigo, data e horários em branco
                    nova_linha = [nome, codigo, data] + [""] * len(colunas_ponto)
                    # Colocar a hora na coluna selecionada
                    nova_linha[3 + colunas_ponto.index(campo_selecionado)] = hora
                    aba.append_row(nova_linha, value_input_option="USER_ENTERED")

                st.success(f"{campo_selecionado} registrada com sucesso às {hora}!")
                st.session_state.registrado = True
        else:
            st.warning("Por favor, contate o PCP para corrigir o código.")
    else:
        if codigo != 0:
            st.error("Código não encontrado. Tente novamente.")
else:
    if st.button("Registrar outro colaborador"):
        st.session_state.registrado = False

