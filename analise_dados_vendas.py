import streamlit as st
import plotly.express as px
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Análise de Pedidos",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Dashboard de Análise de Pedidos")

# Upload do arquivo
st.sidebar.header("Configurações")
uploaded_file = st.sidebar.file_uploader("Faça upload do seu arquivo Excel", type=['xlsx', 'xls'])

# Definição das colunas esperadas
COLUNAS_ESPERADAS = [
    "id_pedido", "data", "loja", "cidade", "estado", 
    "regiao", "tamanho", "local_consumo", "preco",
    "forma_pagamento", "ano_mes"
]

if uploaded_file is not None:
    try:
        # Leitura dos dados do Excel
        dados = pd.read_excel(uploaded_file)
        
        # Verifica se todas as colunas necessárias estão presentes
        colunas_faltantes = [col for col in COLUNAS_ESPERADAS if col not in dados.columns]
        
        if colunas_faltantes:
            st.error(f"As seguintes colunas estão faltando no arquivo: {', '.join(colunas_faltantes)}")
        else:
            # Preparação dos dados - Criando uma cópia explícita do DataFrame
            dados = dados.copy()
            dados['data'] = pd.to_datetime(dados['data'])
            
            # Sidebar - Filtros
            st.sidebar.header("Filtros")
            
            # Filtro de período
            min_date = dados['data'].min()
            max_date = dados['data'].max()
            start_date, end_date = st.sidebar.date_input(
                "Selecione o período",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Filtro de região
            regioes = ['Todas'] + sorted(dados['regiao'].unique().tolist())
            regiao_selecionada = st.sidebar.selectbox('Selecione a Região', regioes)
            
            # Aplicar filtros - Criando uma nova cópia do DataFrame
            mask = (dados['data'].dt.date >= start_date) & (dados['data'].dt.date <= end_date)
            if regiao_selecionada != 'Todas':
                mask = mask & (dados['regiao'] == regiao_selecionada)
            
            dados_filtrados = dados.loc[mask].copy()
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Pedidos", f"{len(dados_filtrados):,}")
            with col2:
                st.metric("Faturamento Total", f"R$ {dados_filtrados['preco'].sum():,.2f}")
            with col3:
                st.metric("Ticket Médio", f"R$ {dados_filtrados['preco'].mean():,.2f}")
            with col4:
                st.metric("Nº de Lojas", f"{dados_filtrados['loja'].nunique():,}")
            
            # Gráficos
            st.header("Análise de Vendas")
            
            # Lista de análises disponíveis
            colunas_analise = ["loja", "cidade", "estado", "regiao", "tamanho", 
                             "local_consumo", "forma_pagamento"]
            
            # Tabs para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["Análise por Categoria", "Análise Temporal", "Análise Detalhada"])
            
            with tab1:
                # Seletor de categoria para análise
                categoria = st.selectbox(
                    "Selecione a categoria para análise",
                    colunas_analise
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de barras - Faturamento
                    dados_fat = dados_filtrados.groupby(categoria)['preco'].sum().reset_index()
                    fig_fat = px.bar(
                        dados_fat,
                        x=categoria,
                        y='preco',
                        title=f'Faturamento por {categoria}',
                        labels={'preco': 'Faturamento (R$)'}
                    )
                    st.plotly_chart(fig_fat, use_container_width=True)
                
                with col2:
                    # Gráfico de pizza - Quantidade de pedidos
                    fig_qtd = px.pie(
                        dados_filtrados,
                        names=categoria,
                        title=f'Distribuição de Pedidos por {categoria}'
                    )
                    st.plotly_chart(fig_qtd, use_container_width=True)
            
            with tab2:
                # Análise temporal
                dados_temporais = dados_filtrados.groupby('ano_mes')['preco'].sum().reset_index()
                fig_temporal = px.line(
                    dados_temporais,
                    x='ano_mes',
                    y='preco',
                    title='Evolução do Faturamento por Mês',
                    labels={'preco': 'Faturamento (R$)', 'ano_mes': 'Período'}
                )
                st.plotly_chart(fig_temporal, use_container_width=True)
                
                # Preparando dados para o heatmap
                dados_filtrados.loc[:, 'dia_semana'] = dados_filtrados['data'].dt.day_name()
                dados_filtrados.loc[:, 'hora'] = dados_filtrados['data'].dt.hour
                
                vendas_hora_dia = dados_filtrados.pivot_table(
                    values='preco',
                    index='dia_semana',
                    columns='hora',
                    aggfunc='sum'
                )
                
                fig_heatmap = px.imshow(
                    vendas_hora_dia,
                    title='Mapa de Calor: Vendas por Dia e Hora',
                    labels=dict(x='Hora do Dia', y='Dia da Semana', color='Faturamento')
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            with tab3:
                # Análise detalhada
                st.subheader("Dados Detalhados")
                
                # Agrupamento por múltiplas dimensões
                grouped_data = dados_filtrados.groupby(
                    ['regiao', 'estado', 'cidade', 'loja']
                ).agg({
                    'id_pedido': 'count',
                    'preco': ['sum', 'mean']
                }).round(2)
                
                grouped_data.columns = ['Quantidade de Pedidos', 'Faturamento Total', 'Ticket Médio']
                grouped_data = grouped_data.reset_index()
                
                st.dataframe(
                    grouped_data,
                    hide_index=True,
                    column_config={
                        'Faturamento Total': st.column_config.NumberColumn(
                            'Faturamento Total',
                            format="R$ %.2f"
                        ),
                        'Ticket Médio': st.column_config.NumberColumn(
                            'Ticket Médio',
                            format="R$ %.2f"
                        )
                    }
                )
                
                # Opção para download dos dados
                st.download_button(
                    label="Download dos dados analisados",
                    data=grouped_data.to_csv(index=False),
                    file_name="analise_detalhada.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
else:
    # Mensagem inicial
    st.info("👈 Por favor, faça o upload de um arquivo Excel na barra lateral para começar a análise.")
    
    # Exemplo do formato esperado
    st.header("Formato esperado do arquivo Excel:")
    exemplo_df = pd.DataFrame({
        'id_pedido': [1, 2],
        'data': ['2024-01-01', '2024-01-02'],
        'loja': ['Loja A', 'Loja B'],
        'cidade': ['São Paulo', 'Rio de Janeiro'],
        'estado': ['SP', 'RJ'],
        'regiao': ['Sudeste', 'Sudeste'],
        'tamanho': ['Grande', 'Médio'],
        'local_consumo': ['Local', 'Delivery'],
        'preco': [100.0, 150.0],
        'forma_pagamento': ['Cartão', 'Dinheiro'],
        'ano_mes': ['2024-01', '2024-01']
    })
    st.dataframe(exemplo_df)