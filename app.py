import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------------------------------------
st.set_page_config(
    page_title="Simulador de Risco Empresarial - Vancouver",
    page_icon="📊",
    layout="wide"
)

CAMINHO_PREVISOES = "./dados/previsoes_vancouver.csv"
CAMINHO_GEOJSON = "./dados/vancouver_bairros.geojson"

COORDENADAS_VANCOUVER = {
    "Arbutus-Ridge": (49.2476, -123.1627),
    "Downtown": (49.2827, -123.1207),
    "Dunbar-Southlands": (49.2435, -123.1862),
    "Fairview": (49.2636, -123.1304),
    "Grandview-Woodland": (49.2750, -123.0694),
    "Hastings-Sunrise": (49.2811, -123.0405),
    "Kensington-Cedar Cottage": (49.2478, -123.0771),
    "Kerrisdale": (49.2341, -123.1554),
    "Killarney": (49.2185, -123.0401),
    "Kitsilano": (49.2684, -123.1683),
    "Marpole": (49.2108, -123.1302),
    "Mount Pleasant": (49.2634, -123.0987),
    "Oakridge": (49.2261, -123.1162),
    "Renfrew-Collingwood": (49.2485, -123.0400),
    "Riley Park": (49.2443, -123.1014),
    "Shaughnessy": (49.2464, -123.1411),
    "South Cambie": (49.2458, -123.1213),
    "Strathcona": (49.2734, -123.0886),
    "Sunset": (49.2237, -123.0902),
    "Victoria-Fraserview": (49.2196, -123.0642),
    "West End": (49.2876, -123.1381),
    "West Point Grey": (49.2638, -123.1995),
}

# -------------------------------------------------------------
# 1. CARREGAMENTO DOS DADOS PRÉ-CALCULADOS
# -------------------------------------------------------------
@st.cache_data
def carregar_previsoes():
    if not os.path.exists(CAMINHO_PREVISOES):
        st.error(
            f"Arquivo '{CAMINHO_PREVISOES}' não encontrado. "
            "Execute primeiro o script gerador de previsões."
        )
        st.stop()
    return pd.read_csv(CAMINHO_PREVISOES)


df_previsoes = carregar_previsoes()
ramos_disponiveis = sorted(df_previsoes["Ramo"].unique())
bairros_disponiveis = sorted(df_previsoes["Areaespecifica"].unique())

# -------------------------------------------------------------
# 2. BARRA LATERAL (SIMULAÇÃO E FILTROS)
# -------------------------------------------------------------
st.sidebar.header("🎯 Simulação e Filtros")

idx_padrao = ramos_disponiveis.index("Beauty Services") if "Beauty Services" in ramos_disponiveis else 0
ramo_selecionado = st.sidebar.selectbox(
    "Ramo de Atividade para Simular:",
    options=ramos_disponiveis,
    index=idx_padrao
)

df_sim = df_previsoes[df_previsoes["Ramo"] == ramo_selecionado].copy()
df_sim["icone_diagnostico"] = df_sim["diagnostico"].map({
    "ALTO RISCO": "⚠️ ALTO RISCO",
    "BAIXO RISCO": "✅ BAIXO RISCO"
})
df_sim["lat"] = df_sim["Areaespecifica"].map(
    lambda b: COORDENADAS_VANCOUVER.get(b, (49.25, -123.12))[0]
)
df_sim["lon"] = df_sim["Areaespecifica"].map(
    lambda b: COORDENADAS_VANCOUVER.get(b, (49.25, -123.12))[1]
)

diagnosticos_selecionados = st.sidebar.multiselect(
    "Filtrar por Diagnóstico:",
    options=["ALTO RISCO", "BAIXO RISCO"],
    default=["ALTO RISCO", "BAIXO RISCO"]
)

bairros_selecionados = st.sidebar.multiselect(
    "Bairros de Vancouver:",
    options=bairros_disponiveis,
    default=bairros_disponiveis
)

df_filtrado = df_sim[
    (df_sim["diagnostico"].isin(diagnosticos_selecionados)) &
    (df_sim["Areaespecifica"].isin(bairros_selecionados))
].sort_values(by="risco_fechamento", ascending=False)

# -------------------------------------------------------------
# 3. INTERFACE PRINCIPAL
# -------------------------------------------------------------
st.title("🏢 Simulador de Risco de Fechamento - Vancouver")
st.markdown(f"Análise preditiva por bairro para o setor: **{ramo_selecionado}**")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Bairros Analisados", len(df_filtrado))
col_m2.metric("Bairros em Alto Risco", int((df_filtrado["diagnostico"] == "ALTO RISCO").sum()))
risco_medio = f"{df_filtrado['risco_fechamento'].mean():.1f}%" if not df_filtrado.empty else "0%"
col_m3.metric("Risco Médio na Cidade", risco_medio)
bairro_maior_risco = df_filtrado.iloc[0]["Areaespecifica"] if not df_filtrado.empty else "Nenhum"
col_m4.metric("Maior Risco", bairro_maior_risco)

st.divider()

if df_filtrado.empty:
    st.warning("Nenhum bairro encontrado para a combinação de filtros selecionada.")
else:
    col_mapa, col_grafico = st.columns([3, 2])

    with col_mapa:
        st.subheader("📍 Mapa de Risco por Bairro (Vancouver)")
        st.caption("Passe o mouse sobre cada bairro para ver a probabilidade estimada e o diagnóstico.")

        if os.path.exists(CAMINHO_GEOJSON):
            with open(CAMINHO_GEOJSON, "r", encoding="utf-8") as f:
                geojson_vancouver = json.load(f)

            fig_mapa = px.choropleth_map(
                df_filtrado,
                geojson=geojson_vancouver,
                locations="Areaespecifica",
                featureidkey="properties.name",
                color="diagnostico",
                color_discrete_map={"ALTO RISCO": "#e63946", "BAIXO RISCO": "#2a9d8f"},
                hover_name="Areaespecifica",
                hover_data={
                    "risco_fechamento": True,
                    "icone_diagnostico": True,
                    "empresas_fechadas": True,
                    "Areaespecifica": False,
                    "diagnostico": False
                },
                map_style="carto-positron",
                zoom=10.8,
                center={"lat": 49.252, "lon": -123.120},
                opacity=0.55,
                labels={
                    "risco_fechamento": "Risco (%)",
                    "icone_diagnostico": "Diagnóstico",
                    "empresas_fechadas": "Baixas Históricas"
                }
            )
            fig_mapa.add_trace(
                go.Scattermap(
                    lat=df_filtrado["lat"],
                    lon=df_filtrado["lon"],
                    mode="text",
                    text=df_filtrado["diagnostico"].map({"ALTO RISCO": "⚠️", "BAIXO RISCO": "✅"}),
                    textfont=dict(size=18),
                    hoverinfo="skip",
                    showlegend=False
                )
            )
        else:
            fig_mapa = px.scatter_map(
                df_filtrado,
                lat="lat",
                lon="lon",
                size="risco_fechamento",
                color="diagnostico",
                color_discrete_map={"ALTO RISCO": "#e63946", "BAIXO RISCO": "#2a9d8f"},
                hover_name="Areaespecifica",
                hover_data={
                    "risco_fechamento": True,
                    "icone_diagnostico": True,
                    "empresas_fechadas": True,
                    "lat": False,
                    "lon": False,
                    "diagnostico": False
                },
                text=df_filtrado["diagnostico"].map({"ALTO RISCO": "⚠️", "BAIXO RISCO": "✅"}),
                size_max=26,
                zoom=10.8,
                center={"lat": 49.252, "lon": -123.120},
                map_style="carto-positron",
                labels={
                    "risco_fechamento": "Risco (%)",
                    "icone_diagnostico": "Diagnóstico",
                    "empresas_fechadas": "Baixas Históricas"
                }
            )
            fig_mapa.update_traces(textposition="top center", textfont=dict(size=15))

        fig_mapa.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=480,
            legend_title_text="Status"
        )
        st.plotly_chart(fig_mapa, use_container_width=True)

    with col_grafico:
        st.subheader("📊 Ranking de Risco por Bairro")
        fig_bar = px.bar(
            df_filtrado,
            x="risco_fechamento",
            y="Areaespecifica",
            orientation="h",
            color="diagnostico",
            color_discrete_map={"ALTO RISCO": "#e63946", "BAIXO RISCO": "#2a9d8f"},
            title=f"Probabilidade de Fechamento ({ramo_selecionado})",
            labels={"risco_fechamento": "Risco Estimado (%)", "Areaespecifica": "Bairro"},
        )
        fig_bar.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=10, t=40, b=0),
            height=480,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------
    # 4. TABELA DETALHADA
    # -------------------------------------------------------------
    st.divider()
    st.subheader("📋 Tabela Analítica de Bairros")
    st.dataframe(
        df_filtrado[[
            "Areaespecifica",
            "risco_fechamento",
            "icone_diagnostico",
            "empresas_fechadas",
            "total_empresas"
        ]].rename(
            columns={
                "Areaespecifica": "Bairro",
                "risco_fechamento": "Risco Estimado (%)",
                "icone_diagnostico": "Diagnóstico",
                "empresas_fechadas": "Cancelamentos Históricos",
                "total_empresas": "Total de Licenças"
            }
        ),
        use_container_width=True,
        hide_index=True
    )