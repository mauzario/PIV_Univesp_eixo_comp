import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Fechamento de Empresas em SP",
    page_icon="📊",
    layout="wide"
)

# -------------------------------------------------------------
# 1. CARREGAMENTO / SIMULAÇÃO DE DADOS
# -------------------------------------------------------------
@st.cache_data
def load_data():
    # Dados de exemplo com bairros centrais e periféricos de SP
    data = [
        {"bairro": "Sé / República (Centro)", "zona": "Centro", "empresas_fechadas": 1240, "setor_predominante": "Comércio", "lat": -23.5489, "lon": -46.6388},
        {"bairro": "Pinheiros", "zona": "Oeste", "empresas_fechadas": 890, "setor_predominante": "Serviços", "lat": -23.5617, "lon": -46.6997},
        {"bairro": "Bela Vista", "zona": "Centro", "empresas_fechadas": 810, "setor_predominante": "Serviços", "lat": -23.5606, "lon": -46.6478},
        {"bairro": "Santo Amaro", "zona": "Sul", "empresas_fechadas": 760, "setor_predominante": "Comércio", "lat": -23.6528, "lon": -46.7092},
        {"bairro": "Itaquera", "zona": "Leste", "empresas_fechadas": 690, "setor_predominante": "Comércio", "lat": -23.5417, "lon": -46.4567},
        {"bairro": "Mooca", "zona": "Leste", "empresas_fechadas": 620, "setor_predominante": "Indústria", "lat": -23.5684, "lon": -46.5989},
        {"bairro": "Vila Mariana", "zona": "Sul", "empresas_fechadas": 590, "setor_predominante": "Serviços", "lat": -23.5895, "lon": -46.6346},
        {"bairro": "Santana", "zona": "Norte", "empresas_fechadas": 550, "setor_predominante": "Comércio", "lat": -23.5042, "lon": -46.6264},
        {"bairro": "Lapa", "zona": "Oeste", "empresas_fechadas": 510, "setor_predominante": "Serviços", "lat": -23.5218, "lon": -46.7022},
        {"bairro": "Freguesia do Ó", "zona": "Norte", "empresas_fechadas": 380, "setor_predominante": "Comércio", "lat": -23.5015, "lon": -46.6991},
        {"bairro": "São Mateus", "zona": "Leste", "empresas_fechadas": 440, "setor_predominante": "Comércio", "lat": -23.6062, "lon": -46.4789},
        {"bairro": "Tatuapé", "zona": "Leste", "empresas_fechadas": 490, "setor_predominante": "Serviços", "lat": -23.5404, "lon": -46.5765},
    ]
    return pd.DataFrame(data)

df = load_data()

# -------------------------------------------------------------
# 2. BARRA LATERAL (FILTROS)
# -------------------------------------------------------------
st.sidebar.header("🔍 Filtros")

# Filtro por Zona
zonas_disponiveis = sorted(df["zona"].unique())
zonas_selecionadas = st.sidebar.multiselect(
    "Região / Zona:",
    options=zonas_disponiveis,
    default=zonas_disponiveis
)

# Filtro por Setor Predominante
setores_disponiveis = sorted(df["setor_predominante"].unique())
setores_selecionados = st.sidebar.multiselect(
    "Setor Predominante:",
    options=setores_disponiveis,
    default=setores_disponiveis
)

# Filtro por Volume Mínimo de Fechamentos
min_fechamentos = st.sidebar.slider(
    "Mínimo de empresas fechadas:",
    min_value=int(df["empresas_fechadas"].min()),
    max_value=int(df["empresas_fechadas"].max()),
    value=int(df["empresas_fechadas"].min()),
    step=50
)

# Aplicando os filtros ao DataFrame
df_filtrado = df[
    (df["zona"].isin(zonas_selecionadas)) &
    (df["setor_predominante"].isin(setores_selecionados)) &
    (df["empresas_fechadas"] >= min_fechamentos)
].sort_values(by="empresas_fechadas", ascending=False)

# -------------------------------------------------------------
# 3. INTERFACE PRINCIPAL
# -------------------------------------------------------------
st.title("🏢 Painel de Encerramento de Empresas - São Paulo")
st.markdown("Análise espacial e setorial das baixas de empresas por bairro na capital paulista.")

# Cards de Métricas Rápidas
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Bairros Listados", len(df_filtrado))
col_m2.metric("Total de Empresas Fechadas", f"{df_filtrado['empresas_fechadas'].sum():,}".replace(",", "."))
bairro_top = df_filtrado.iloc[0]["bairro"] if not df_filtrado.empty else "Nenhum"
col_m3.metric("Maior Concentração", bairro_top)

st.divider()

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para a combinação de filtros selecionada.")
else:
    # Layout em duas colunas: Mapa interativo à esquerda, Gráfico/Resumo à direita
    col_mapa, col_grafico = st.columns([3, 2])

    with col_mapa:
        st.subheader("📍 Mapa Interativo de Fechamentos")
        st.caption("Círculos proporcionais ao número de empresas fechadas. Clique para ver detalhes.")

        # Centro do mapa em São Paulo
        mapa_sp = folium.Map(
            location=[-23.5505, -46.6333],
            zoom_start=11,
            tiles="CartoDB positron"  # Visual clean e moderno open-source
        )

        # Adicionando círculos proporcionais para cada bairro
        for _, row in df_filtrado.iterrows():
            raio = (row["empresas_fechadas"] / df["empresas_fechadas"].max()) * 25 + 5
            popup_html = f"""
            <div style='font-family: sans-serif; min-width: 150px;'>
                <b>{row['bairro']}</b><br>
                <b>Zona:</b> {row['zona']}<br>
                <b>Setor:</b> {row['setor_predominante']}<br>
                <b>Fechamentos:</b> {row['empresas_fechadas']}
            </div>
            """
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=raio,
                color="#e63946",
                fill=True,
                fill_color="#e63946",
                fill_opacity=0.65,
                weight=1.5,
                tooltip=f"{row['bairro']}: {row['empresas_fechadas']} baixas",
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(mapa_sp)

        # Renderiza o mapa Folium no Streamlit
        st_folium(mapa_sp, width="100%", height=450)

    with col_grafico:
        st.subheader("📊 Ranking dos Bairros")
        fig = px.bar(
            df_filtrado.head(10),
            x="empresas_fechadas",
            y="bairro",
            orientation="h",
            color="zona",
            title="Top Bairros com Mais Baixas",
            labels={"empresas_fechadas": "Total de Baixas", "bairro": "Bairro"},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0, r=10, t=40, b=0), height=450)
        st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    st.divider()
    st.subheader("📋 Tabela Analítica de Bairros")
    st.dataframe(
        df_filtrado[["bairro", "zona", "setor_predominante", "empresas_fechadas"]].rename(
            columns={
                "bairro": "Bairro",
                "zona": "Zona / Região",
                "setor_predominante": "Setor Predominante",
                "empresas_fechadas": "Empresas Fechadas"
            }
        ),
        use_container_width=True,
        hide_index=True
    )