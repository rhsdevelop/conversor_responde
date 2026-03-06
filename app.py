import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==========================================
# FUNÇÕES DE TRATAMENTO DE DADOS
# ==========================================

def format_phone(phone_str):
    """Limpa e formata o telefone para o padrão internacional (+55)."""
    if pd.isna(phone_str) or str(phone_str).strip() == "":
        return ""
    
    phone_str = str(phone_str)
    # Pega apenas o primeiro número caso haja mais de um
    first_phone = phone_str.split('/')[0]
    # Remove tudo que não for número
    numeric_phone = "".join(filter(str.isdigit, first_phone))
    
    if not numeric_phone:
        return ""
    
    return f"+55{numeric_phone}"

def convert_to_respondeio(df):
    """Recebe o DataFrame original e retorna o DataFrame no formato Responde.io"""
    columns = [
        'First Name', 'Last Name', 'Phone Number', 'Email', 'Tags', 
        'Assignee', 'lote', 'mes_do_reajuste', 'cpf', 'dia_de_vencimento', 
        'ajuizado', 'negativado', 'construcao', 'qtd_de_parcelas_em_atraso'
    ]
    df_out = pd.DataFrame(columns=columns)
    
    # 1. Nomes
    df_out['First Name'] = df.get('Compromissário Comprador', pd.Series(dtype=str))
    df_out['Last Name'] = df_out['First Name'].apply(
        lambda x: str(x).strip().split()[-1] if pd.notna(x) and len(str(x).strip().split()) > 1 else ""
    )
    
    # 2. Telefones
    df_out['Phone Number'] = df.get('Telefone/Celular', pd.Series(dtype=str)).apply(format_phone)
    
    # 3. Email
    df_out['Email'] = df.get('E-mail', pd.Series(dtype=str)).fillna("")
    
    # 4. Tags
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    df_out['Tags'] = f"imported_{current_date}"
    
    # 5. Assignee
    df_out['Assignee'] = "analaura.barros@mvbadvogados.adv.br"
    
    # 6. Demais campos
    df_out['lote'] = df.get('Empreendimento', pd.Series(dtype=str)).fillna("")
    df_out['mes_do_reajuste'] = df.get('Mês de Atualização', pd.Series(dtype=str)).fillna("")
    df_out['cpf'] = df.get('CPF/CNPJ', pd.Series(dtype=str)).fillna("")
    
    if 'Dia do Vencimento' in df.columns:
        df_out['dia_de_vencimento'] = pd.to_numeric(df['Dia do Vencimento'], errors='coerce') \
            .fillna(0).astype(int).astype(str).replace('0', '')
    
    df_out['ajuizado'] = df.get('Ajuízado', pd.Series(dtype=str)).fillna("")
    df_out['negativado'] = df.get('Negativado', pd.Series(dtype=str)).fillna("")
    df_out['construcao'] = df.get('Construção', pd.Series(dtype=str)).fillna("")
    
    if 'Qtde de parcelas em atraso' in df.columns:
        df_out['qtd_de_parcelas_em_atraso'] = pd.to_numeric(df['Qtde de parcelas em atraso'], errors='coerce') \
            .fillna(0).astype(int)
    
    return df_out

# ==========================================
# INTERFACE VISUAL (STREAMLIT)
# ==========================================

# Configuração da página
st.set_page_config(page_title="Conversor Responde.io", page_icon="🔄", layout="centered")

st.title("🔄 Conversor de Dados - Responde.io")
st.markdown("""
Esta ferramenta converte as planilhas extraídas do **Gerente Remoto** para o formato exato exigido pela plataforma **Responde.io**.
""")

# Área de Upload
uploaded_file = st.file_uploader("📂 Arraste sua planilha (.xlsx ou .csv) gerada no Gerente Remoto", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Carregando os dados
        # O Gerente remoto costuma ter uma linha extra de título, por isso tentamos skiprows=1
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, skiprows=1)
                # Fallback caso a planilha já venha sem o título extra
                if 'Compromissário Comprador' not in df.columns:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file)
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
        else:
            try:
                df = pd.read_excel(uploaded_file, skiprows=1)
                if 'Compromissário Comprador' not in df.columns:
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file)
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file)

        # Checagem de segurança se a coluna principal existe
        if 'Compromissário Comprador' not in df.columns:
            st.error("❌ Não foi possível encontrar as colunas esperadas. Verifique se o arquivo é o relatório correto do Gerente Remoto.")
        else:
            with st.spinner('Convertendo os dados...'):
                df_convertido = convert_to_respondeio(df)
            
            st.success(f"✅ Sucesso! {len(df_convertido)} contatos foram processados e formatados.")
            
            # Mostra uma prévia dos dados para a equipe validar
            st.subheader("👀 Prévia dos Dados Convertidos")
            st.dataframe(df_convertido.head(10))
            
            # Prepara o arquivo CSV para download (garantindo o UTF-8 e separador de vírgula)
            csv_buffer = io.BytesIO()
            df_convertido.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_data = csv_buffer.getvalue()
            
            st.markdown("---")
            st.markdown("### 📥 Baixe seu arquivo")
            
            nome_arquivo_saida = f"importacao_respondeio_{datetime.now().strftime('%d%m%Y')}.csv"
            
            # Botão nativo de download do Streamlit
            st.download_button(
                label="⬇️ Clique aqui para baixar o CSV Formatado",
                data=csv_data,
                file_name=nome_arquivo_saida,
                mime="text/csv",
                type="primary" # Deixa o botão em destaque (azul/vermelho dependendo do tema)
            )

    except Exception as e:
        st.error(f"⚠️ Ocorreu um erro ao processar o arquivo: {e}")