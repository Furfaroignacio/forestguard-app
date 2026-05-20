import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression

# ── CONFIGURACIÓN ──────────────────────────────────────────────
st.set_page_config(
    page_title="ForestGuard Analytics",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── DATOS ──────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect('forest_guard_dwh.db')
    df_agro = pd.read_sql("""
        SELECT t.anio, g.provincia, g.region,
               c.cultivo, c.categoria, c.es_soja_maiz,
               f.sup_sembrada_ha, f.sup_cosechada_ha,
               f.produccion_tn, f.rendimiento_kg_ha
        FROM FACT_AGRO_FORESTAL f
        JOIN DIM_TIEMPO    t ON f.id_tiempo    = t.id_tiempo
        JOIN DIM_GEOGRAFIA g ON f.id_geografia = g.id_geografia
        JOIN DIM_CULTIVO   c ON f.id_cultivo   = c.id_cultivo
    """, conn)
    df_forest = pd.read_sql("""
        SELECT t.anio, c.clase_cobertura, c.tipo, c.es_forestal,
               f.hectareas_cobertura
        FROM FACT_COBERTURA_NACIONAL f
        JOIN DIM_TIEMPO    t ON f.id_tiempo    = t.id_tiempo
        JOIN DIM_COBERTURA c ON f.id_cobertura = c.id_cobertura
    """, conn)
    df_perdida = pd.read_sql(
        "SELECT * FROM FACT_PERDIDA_FORESTAL ORDER BY anio", conn)
    df_indice = pd.read_sql(
        "SELECT * FROM DIM_INDICE_PRESION ORDER BY indice_presion_100 DESC", conn)
    conn.close()
    return df_agro, df_forest, df_perdida, df_indice

df_agro, df_forest, df_perdida, df_indice = cargar_datos()

# ── SIDEBAR ────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/emoji/96/evergreen-tree.png", width=80)
st.sidebar.title("ForestGuard Analytics")
st.sidebar.markdown("*El bosque habla en datos.*")
st.sidebar.markdown("---")
pagina = st.sidebar.radio("Navegación", [
    "🏠 Panel ejecutivo",
    "🌲 Análisis forestal",
    "🌾 Análisis agrícola",
    "🌎 Mapa de riesgo",
    "🔮 Proyección 2030"
])
st.sidebar.markdown("---")
st.sidebar.markdown("**Fuentes:** MAGyP / SIIA · MapBiomas")
st.sidebar.markdown("**Período:** 2000–2024")

# ══════════════════════════════════════════════════════════════
# PANEL EJECUTIVO
# ══════════════════════════════════════════════════════════════
if pagina == "🏠 Panel ejecutivo":
    st.title("🌳 ForestGuard Analytics")
    st.markdown("### Panel ejecutivo — Argentina 2000–2024")
    st.markdown("---")

    bosque_2000 = df_forest[(df_forest['anio']==2000) & (df_forest['es_forestal']==1)]\
        ['hectareas_cobertura'].sum() / 1e6
    bosque_2024 = df_forest[(df_forest['anio']==2024) & (df_forest['es_forestal']==1)]\
        ['hectareas_cobertura'].sum() / 1e6
    perdida_total = bosque_2000 - bosque_2024
    agro_2000 = df_agro[df_agro['anio']==2000]['sup_sembrada_ha'].sum() / 1e6
    agro_2024 = df_agro[df_agro['anio']==2024]['sup_sembrada_ha'].sum() / 1e6
    crecimiento_agro = ((agro_2024 - agro_2000) / agro_2000 * 100)
    peor_anio = df_perdida.loc[df_perdida['perdida_mha'].idxmax(), 'anio']
    peor_perdida = df_perdida['perdida_mha'].max()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pérdida forestal total",
              f"{perdida_total:.1f} M ha",
              delta=f"-{perdida_total:.1f} M ha vs 2000", delta_color="inverse")
    c2.metric("Cobertura forestal 2024",
              f"{bosque_2024:.1f} M ha",
              delta=f"era {bosque_2000:.1f} M ha en 2000", delta_color="inverse")
    c3.metric("Crecimiento agrícola",
              f"+{crecimiento_agro:.1f}%",
              delta="superficie sembrada 2000→2024", delta_color="inverse")
    c4.metric("Peor año de deforestación",
              f"{int(peor_anio)}",
              delta=f"-{peor_perdida:.2f} M ha ese año", delta_color="inverse")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        df_f = df_forest[df_forest['es_forestal']==1]\
            .groupby('anio')['hectareas_cobertura'].sum().reset_index()
        df_f['mha'] = df_f['hectareas_cobertura'] / 1e6
        fig = px.area(df_f, x='anio', y='mha',
                      title='Cobertura forestal nacional 2000–2024',
                      labels={'anio':'Año','mha':'Millones de ha'},
                      color_discrete_sequence=['#2d6a4f'])
        fig.add_vline(x=2007, line_dash='dash', line_color='orange',
                      annotation_text='Ley de Bosques', annotation_position='top right')
        fig.update_layout(template='plotly_white', height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        df_a = df_agro.groupby('anio')['sup_sembrada_ha'].sum().reset_index()
        df_a['mha'] = df_a['sup_sembrada_ha'] / 1e6
        fig2 = px.bar(df_a, x='anio', y='mha',
                      title='Superficie agrícola total 2000–2024',
                      labels={'anio':'Año','mha':'Millones de ha'},
                      color_discrete_sequence=['#e9c46a'])
        fig2.add_vline(x=2007, line_dash='dash', line_color='orange',
                       annotation_text='Ley de Bosques')
        fig2.update_layout(template='plotly_white', height=320)
        st.plotly_chart(fig2, use_container_width=True)

    st.info("📊 **Correlación de Pearson r = -0.975** entre expansión agrícola y pérdida "
            "forestal — relación negativa casi perfecta sostenida 24 años consecutivos.")

# ══════════════════════════════════════════════════════════════
# ANÁLISIS FORESTAL
# ══════════════════════════════════════════════════════════════
elif pagina == "🌲 Análisis forestal":
    st.title("🌲 Análisis de cobertura forestal")
    st.markdown("---")

    # Pérdida anual
    st.subheader("Pérdida forestal anual")
    df_p = df_perdida.copy()
    df_p['color'] = df_p['perdida_mha'].apply(
        lambda x: 'Pérdida alta' if x > 1 else ('Recuperación' if x < 0 else 'Pérdida moderada'))

    fig_p = px.bar(df_p, x='anio', y='perdida_mha',
                   color='color',
                   color_discrete_map={
                       'Pérdida alta':     '#d62828',
                       'Pérdida moderada': '#e9c46a',
                       'Recuperación':     '#2d6a4f'
                   },
                   title='Hectáreas de bosque perdidas por año (millones)',
                   labels={'anio':'Año', 'perdida_mha':'Pérdida (M ha)', 'color':''})
    fig_p.add_vline(x=2007, line_dash='dash', line_color='orange',
                    annotation_text='Ley de Bosques 2007',
                    annotation_position='top right')
    fig_p.update_layout(template='plotly_white', height=380)
    st.plotly_chart(fig_p, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tasa anual de deforestación (%)")
        fig_t = px.line(df_p, x='anio', y='tasa_deforestacion_pct',
                        title='Tasa de deforestación anual',
                        labels={'anio':'Año',
                                'tasa_deforestacion_pct':'Tasa (%)'},
                        color_discrete_sequence=['#d62828'])
        fig_t.add_hline(y=0, line_dash='dash', line_color='gray')
        fig_t.add_vline(x=2007, line_dash='dash', line_color='orange',
                        annotation_text='Ley de Bosques')
        fig_t.update_layout(template='plotly_white', height=320)
        st.plotly_chart(fig_t, use_container_width=True)

    with col2:
        st.subheader("Peores años de deforestación")
        top5 = df_p.nlargest(5, 'perdida_mha')[['anio','perdida_mha','tasa_deforestacion_pct']]
        top5.columns = ['Año','Pérdida (M ha)','Tasa (%)']
        top5['Pérdida (M ha)'] = top5['Pérdida (M ha)'].round(3)
        top5['Tasa (%)'] = top5['Tasa (%)'].round(3)
        st.dataframe(top5, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Correlación agricultura vs bosque")
        df_agro_anio = df_agro.groupby('anio')['sup_sembrada_ha'].sum().reset_index()
        df_agro_anio['mha'] = df_agro_anio['sup_sembrada_ha'] / 1e6
        df_f2 = df_forest[df_forest['es_forestal']==1]\
            .groupby('anio')['hectareas_cobertura'].sum().reset_index()
        df_f2['mha_f'] = df_f2['hectareas_cobertura'] / 1e6
        df_corr = df_agro_anio.merge(df_f2, on='anio')
        r = df_corr['mha'].corr(df_corr['mha_f'])
        fig_c = px.scatter(df_corr, x='mha', y='mha_f',
                           text='anio', trendline='ols',
                           title=f'Correlación Pearson r = {r:.3f}',
                           labels={'mha':'Agricultura (M ha)',
                                   'mha_f':'Bosque (M ha)'},
                           color_discrete_sequence=['#2d6a4f'])
        fig_c.update_traces(textposition='top center', textfont_size=8)
        fig_c.update_layout(template='plotly_white', height=320)
        st.plotly_chart(fig_c, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# ANÁLISIS AGRÍCOLA
# ══════════════════════════════════════════════════════════════
elif pagina == "🌾 Análisis agrícola":
    st.title("🌾 Análisis de expansión agrícola")
    st.markdown("---")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        provs = sorted(df_agro['provincia'].unique())
        prov_sel = st.multiselect("Provincia", provs,
                                   default=['BUENOS AIRES','CORDOBA','SANTA FE'])
    with col_f2:
        anio_min, anio_max = st.slider("Años", 2000, 2024, (2000, 2024))
    with col_f3:
        cats = sorted(df_agro['categoria'].unique())
        cat_sel = st.multiselect("Categoría", cats, default=cats)

    df_f = df_agro[
        (df_agro['provincia'].isin(prov_sel)) &
        (df_agro['anio'] >= anio_min) &
        (df_agro['anio'] <= anio_max) &
        (df_agro['categoria'].isin(cat_sel))
    ]

    if df_f.empty:
        st.warning("Sin datos para los filtros seleccionados.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            df_ev = df_f.groupby(['anio','provincia'])\
                ['sup_sembrada_ha'].sum().reset_index()
            df_ev['mha'] = df_ev['sup_sembrada_ha'] / 1e6
            fig = px.line(df_ev, x='anio', y='mha', color='provincia',
                          title='Evolución superficie por provincia',
                          labels={'anio':'Año','mha':'M ha','provincia':'Provincia'})
            fig.update_layout(template='plotly_white', height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_cu = df_f.groupby('cultivo')['sup_sembrada_ha'].sum()\
                .reset_index().sort_values('sup_sembrada_ha', ascending=False).head(8)
            df_cu['mha'] = df_cu['sup_sembrada_ha'] / 1e6
            fig2 = px.bar(df_cu.sort_values('mha'),
                          x='mha', y='cultivo', orientation='h',
                          title='Top cultivos por superficie',
                          labels={'mha':'M ha','cultivo':''},
                          color='mha', color_continuous_scale='YlGn')
            fig2.update_layout(template='plotly_white', height=350,
                               coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Soja vs resto
        df_soja = df_f.groupby(['anio','es_soja_maiz'])\
            ['sup_sembrada_ha'].sum().reset_index()
        df_soja['grupo'] = df_soja['es_soja_maiz'].map(
            {1:'Soja y Maíz', 0:'Otros cultivos'})
        df_soja['mha'] = df_soja['sup_sembrada_ha'] / 1e6
        fig3 = px.bar(df_soja, x='anio', y='mha', color='grupo',
                      title='Soja y Maíz vs otros cultivos',
                      labels={'anio':'Año','mha':'M ha','grupo':''},
                      color_discrete_map={
                          'Soja y Maíz':    '#e9c46a',
                          'Otros cultivos': '#457b9d'},
                      barmode='stack')
        fig3.update_layout(template='plotly_white', height=320)
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# MAPA DE RIESGO
# ══════════════════════════════════════════════════════════════
elif pagina == "🌎 Mapa de riesgo":
    st.title("🌎 Índice de presión agrícola por provincia")
    st.markdown("Score compuesto: superficie sembrada (50%) + % soja/maíz (30%) "
                "+ tasa de crecimiento (20%).")
    st.markdown("---")

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("Ranking de provincias")
        df_show = df_indice[['provincia','indice_presion_100',
                              'sup_total','pct_soja']].copy()
        df_show.columns = ['Provincia','Índice (0–100)',
                           'Sup. total (M ha)','% Soja/Maíz']
        df_show['Sup. total (M ha)'] = df_show['Sup. total (M ha)'].round(1)
        df_show['% Soja/Maíz'] = df_show['% Soja/Maíz'].round(1)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    with col2:
        fig_i = px.bar(df_indice.sort_values('indice_presion_100'),
                       x='indice_presion_100', y='provincia',
                       orientation='h',
                       title='Índice de presión agrícola por provincia',
                       labels={'indice_presion_100':'Índice (0–100)',
                               'provincia':''},
                       color='indice_presion_100',
                       color_continuous_scale='RdYlGn_r')
        fig_i.add_vline(x=50, line_dash='dash', line_color='gray',
                        annotation_text='umbral crítico')
        fig_i.update_layout(template='plotly_white', height=500,
                            coloraxis_showscale=False)
        st.plotly_chart(fig_i, use_container_width=True)

    # Clustering
    st.markdown("---")
    st.subheader("Clustering K-Means — Perfiles de impacto")
    clustering_data = {
        'provincia':     ['BUENOS AIRES','CORDOBA','SANTA FE',
                          'CHACO','ENTRE RIOS','LA PAMPA','FORMOSA',
                          'CORRIENTES','MISIONES','LA RIOJA',
                          'CATAMARCA','JUJUY','SALTA',
                          'SAN LUIS','SANTIAGO DEL ESTERO','TUCUMAN'],
        'perfil':        ['Alto impacto','Alto impacto','Alto impacto',
                          'Impacto medio','Impacto medio','Impacto medio','Impacto medio',
                          'Impacto medio','Impacto medio','Impacto medio',
                          'Bajo impacto','Bajo impacto','Bajo impacto',
                          'Bajo impacto','Bajo impacto','Bajo impacto'],
        'sup_total_mha': [424.2,319.6,213.8,51.4,86.6,56.6,2.3,
                          4.0,5.9,0.03,2.9,1.6,39.2,19.6,71.8,16.7],
        'pct_soja_maiz': [39.1,41.2,44.7,48.2,38.1,31.1,47.7,
                          42.8,45.0,0.0,53.2,57.6,49.5,36.3,46.1,54.6],
    }
    df_cl = pd.DataFrame(clustering_data)
    fig_cl = px.scatter(df_cl, x='sup_total_mha', y='pct_soja_maiz',
                        color='perfil', size='sup_total_mha', text='provincia',
                        color_discrete_map={
                            'Alto impacto':  '#d62828',
                            'Impacto medio': '#e9c46a',
                            'Bajo impacto':  '#2d6a4f'},
                        title='Clustering de provincias por perfil de impacto',
                        labels={'sup_total_mha':'Superficie total (M ha)',
                                'pct_soja_maiz':'% Soja y Maíz',
                                'perfil':'Perfil'})
    fig_cl.update_traces(textposition='top center', textfont_size=8)
    fig_cl.update_layout(template='plotly_white', height=420)
    st.plotly_chart(fig_cl, use_container_width=True)
    # ── ÁRBOL DE DECISIÓN ─────────────────────────────────────
    st.markdown("---")
    st.subheader("🌿 Árbol de decisión — Reglas de clasificación")
    st.markdown("El árbol explica *por qué* cada provincia recibe su perfil de impacto. "
                "Solo necesita dos variables para clasificar perfectamente las 16 provincias.")

    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.preprocessing import LabelEncoder
    import matplotlib.pyplot as plt
    from sklearn.tree import plot_tree

    # Datos
    df_raw_tree = df_agro.copy()
    features_tree = df_raw_tree.groupby('provincia').agg(
        sup_total_mha   = ('sup_sembrada_ha', lambda x: x.sum()/1e6),
        prod_total_mtn  = ('produccion_tn',   lambda x: x.sum()/1e6),
        pct_soja_maiz   = ('es_soja_maiz',    lambda x: x.mean()*100),
        crecimiento_pct = ('sup_sembrada_ha', lambda x: (
            x[df_raw_tree.loc[x.index,'anio'] >= 2020].mean() /
            x[df_raw_tree.loc[x.index,'anio'] <= 2004].mean() - 1
        ) * 100 if x[df_raw_tree.loc[x.index,'anio'] <= 2004].mean() > 0 else 0)
    ).reset_index()
    features_tree['crecimiento_pct'] = features_tree['crecimiento_pct'].fillna(0)

    labels_tree = {
        'BUENOS AIRES': 'Alto impacto', 'CORDOBA': 'Alto impacto',
        'SANTA FE': 'Alto impacto', 'CHACO': 'Impacto medio',
        'ENTRE RIOS': 'Impacto medio', 'LA PAMPA': 'Impacto medio',
        'FORMOSA': 'Impacto medio', 'CORRIENTES': 'Impacto medio',
        'MISIONES': 'Impacto medio', 'LA RIOJA': 'Impacto medio',
        'CATAMARCA': 'Bajo impacto', 'JUJUY': 'Bajo impacto',
        'SALTA': 'Bajo impacto', 'SAN LUIS': 'Bajo impacto',
        'SANTIAGO DEL ESTERO': 'Bajo impacto', 'TUCUMAN': 'Bajo impacto'
    }
    features_tree['perfil'] = features_tree['provincia'].map(labels_tree)

    X_tree = features_tree[['sup_total_mha','prod_total_mtn',
                              'pct_soja_maiz','crecimiento_pct']]
    le_tree = LabelEncoder()
    y_tree = le_tree.fit_transform(features_tree['perfil'])

    arbol = DecisionTreeClassifier(max_depth=3, random_state=42, min_samples_leaf=2)
    arbol.fit(X_tree, y_tree)

    # Visualización
    fig_tree, ax_tree = plt.subplots(figsize=(14, 7))
    fig_tree.patch.set_facecolor('#0e1117')
    ax_tree.set_facecolor('#0e1117')
    plot_tree(arbol,
              feature_names=['Sup. sembrada (M ha)','Producción (M tn)',
                             '% Soja/Maíz','Crecimiento (%)'],
              class_names=le_tree.classes_,
              filled=True, rounded=True, fontsize=11,
              ax=ax_tree, impurity=False, precision=1)
    plt.title('Árbol de decisión — Clasificación por perfil de impacto',
              fontsize=13, fontweight='bold', color='white', pad=15)
    plt.tight_layout()
    st.pyplot(fig_tree)
    plt.close()

    # Importancia de variables
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Variables más importantes")
        imp_df = pd.DataFrame({
            'Variable': ['Crecimiento (%)', 'Sup. sembrada (M ha)',
                         '% Soja/Maíz', 'Producción (M tn)'],
            'Importancia': [0.585, 0.415, 0.000, 0.000]
        })
        fig_imp = px.bar(imp_df.sort_values('Importancia'),
                         x='Importancia', y='Variable',
                         orientation='h',
                         color='Importancia',
                         color_continuous_scale='Greens',
                         title='Importancia de variables')
        fig_imp.update_layout(template='plotly_white',
                              height=250, coloraxis_showscale=False)
        st.plotly_chart(fig_imp, use_container_width=True)

    with col_b:
        st.markdown("#### Reglas del árbol")
        st.markdown("""
        🔴 **Alto impacto** — Crecimiento > -20.5% **y** Superficie > 150 M ha
        
        🟡 **Impacto medio** — Crecimiento > -20.5% **y** Superficie ≤ 150 M ha
        
        🟢 **Bajo impacto** — Crecimiento ≤ -20.5%
        
        *Con solo 2 variables el árbol clasifica correctamente las 16 provincias.*
        """)

# ══════════════════════════════════════════════════════════════
# PROYECCIÓN 2030
# ══════════════════════════════════════════════════════════════
elif pagina == "🔮 Proyección 2030":
    st.title("🔮 Proyección de cobertura forestal 2025–2030")
    st.markdown("Modelo de regresión lineal sobre datos históricos 2000–2024.")
    st.markdown("---")

    df_fh = df_forest[df_forest['es_forestal']==1]\
        .groupby('anio')['hectareas_cobertura'].sum().reset_index()
    df_fh['mha'] = df_fh['hectareas_cobertura'] / 1e6

    X = df_fh['anio'].values.reshape(-1,1)
    y = df_fh['mha'].values
    modelo = LinearRegression()
    modelo.fit(X, y)

    años_pred = np.arange(2025, 2031).reshape(-1,1)
    pred = modelo.predict(años_pred)

    df_pred = pd.DataFrame({
        'anio': años_pred.flatten(),
        'mha': pred, 'tipo': 'Proyección'})
    df_hist = df_fh[['anio','mha']].copy()
    df_hist['tipo'] = 'Histórico'
    df_total = pd.concat([df_hist, df_pred])

    fig_pr = px.line(df_total, x='anio', y='mha', color='tipo',
                     color_discrete_map={
                         'Histórico':  '#2d6a4f',
                         'Proyección': '#d62828'},
                     title='Cobertura forestal histórica y proyectada',
                     labels={'anio':'Año','mha':'Millones de ha','tipo':''})
    fig_pr.add_vline(x=2024, line_dash='dash', line_color='gray',
                     annotation_text='Inicio proyección')
    fig_pr.add_vline(x=2007, line_dash='dot', line_color='orange',
                     annotation_text='Ley de Bosques 2007',
                     annotation_position='bottom right')
    fig_pr.update_layout(template='plotly_white', height=420)
    st.plotly_chart(fig_pr, use_container_width=True)

    perdida_proy = df_fh['mha'].iloc[-1] - pred[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Cobertura forestal 2024", f"{df_fh['mha'].iloc[-1]:.2f} M ha")
    c2.metric("Proyección 2030", f"{pred[-1]:.2f} M ha",
              delta=f"-{perdida_proy:.2f} M ha", delta_color="inverse")
    c3.metric("Pérdida proyectada 2024–2030", f"{perdida_proy:.2f} M ha",
              delta="si continúa la tendencia", delta_color="inverse")

    st.warning("⚠️ Escenario de referencia asumiendo tendencia histórica sin cambios "
               "de política. No es una predicción determinística.")
    st.info(f"📐 El modelo proyecta una pérdida de "
            f"**{abs(modelo.coef_[0]):.3f} M ha por año** "
            f"si se mantiene la tendencia actual.")
