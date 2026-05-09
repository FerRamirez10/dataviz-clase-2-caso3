import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title='MetalParts Dashboard',
    page_icon='🏭',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Estilos personalizados
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1b2631 0%, #2e4057 100%);
        padding: 1rem; border-radius: 12px; color: white; text-align: center;
    }
    .block-container { padding-top: 1rem; }
    h1 { color: #1b2631; }
    .stAlert { border-radius: 8px; }
    /* Estilo para la tabla de alertas */
    .alerta-header {
        background: #c0392b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px 8px 0 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CARGA DE DATOS (con caché para mejor rendimiento)
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso3_produccion_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_produccion'] = pd.to_datetime(df['fecha_produccion'])
    return df

df = cargar_datos()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1b2631/ffffff?text=MetalParts", width=200)
    st.markdown("---")
    st.header("🔧 Filtros")

    # ── Selector de rango de fechas ──────────────────────────
    fecha_min = df['fecha_produccion'].min().date()
    fecha_max = df['fecha_produccion'].max().date()

    rango_fechas = st.date_input(
        "📅 Rango de Fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
        help="Selecciona la fecha de inicio y fin del período a analizar"
    )

    # Validar que se hayan elegido dos fechas
    if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio, fecha_fin = fecha_min, fecha_max

    st.markdown("---")

    lineas_sel = st.multiselect(
        "Línea de Producción",
        options=sorted(df['linea_produccion'].unique()),
        default=list(df['linea_produccion'].unique())
    )

    turnos_sel = st.multiselect(
        "Turno",
        options=sorted(df['turno'].unique()),
        default=list(df['turno'].unique())
    )

    producto_sel = st.selectbox(
        "Producto",
        options=['Todos'] + sorted(df['producto'].unique())
    )

    maquinas_sel = st.multiselect(
        "Máquina",
        options=sorted(df['maquina'].unique()),
        default=list(df['maquina'].unique())
    )

    alertas_toggle = st.checkbox("⚠️ Solo órdenes con defectos > 10%", value=False)

    st.markdown("---")
    st.caption("📅 Datos: MetalParts Colombia | Zona Industrial Itagüí")

# ═══════════════════════════════════════════════════════════════
# APLICAR FILTROS (incluyendo rango de fechas)
# ═══════════════════════════════════════════════════════════════
df_f = df.copy()

# Filtro de fechas
df_f = df_f[
    (df_f['fecha_produccion'].dt.date >= fecha_inicio) &
    (df_f['fecha_produccion'].dt.date <= fecha_fin)
]

if lineas_sel:
    df_f = df_f[df_f['linea_produccion'].isin(lineas_sel)]
if turnos_sel:
    df_f = df_f[df_f['turno'].isin(turnos_sel)]
if producto_sel != 'Todos':
    df_f = df_f[df_f['producto'] == producto_sel]
if maquinas_sel:
    df_f = df_f[df_f['maquina'].isin(maquinas_sel)]
if alertas_toggle:
    df_f = df_f[df_f['tasa_defectos_pct'] > 10]

# ═══════════════════════════════════════════════════════════════
# TÍTULO PRINCIPAL
# ═══════════════════════════════════════════════════════════════
st.title("🏭 MetalParts — Dashboard de Control de Producción")
st.markdown(
    f"**Panel de operaciones industriales · Eficiencia, calidad y tiempos de paro** "
    f"| 📅 Período: `{fecha_inicio}` → `{fecha_fin}`"
)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# KPIs (siempre visibles, fuera de los tabs)
# ═══════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)

total_ordenes     = len(df_f)
eficiencia_prom   = df_f['eficiencia_pct'].mean() if total_ordenes > 0 else 0
tasa_defectos     = df_f['tasa_defectos_pct'].mean() if total_ordenes > 0 else 0
total_unidades    = df_f['unidades_producidas'].sum() if total_ordenes > 0 else 0
tiempo_paro_total = df_f['tiempo_paro_min'].sum() if total_ordenes > 0 else 0
ordenes_alerta    = (df_f['tasa_defectos_pct'] > 10).sum() if total_ordenes > 0 else 0

k1.metric("📋 Órdenes", f"{total_ordenes:,}", delta=f"{total_ordenes - len(df)} vs total")
k2.metric("⚙️ Eficiencia Prom.", f"{eficiencia_prom:.1f}%", delta=f"{eficiencia_prom - 80:.1f}% vs meta 80%")
k3.metric("❌ Tasa Defectos", f"{tasa_defectos:.2f}%")
k4.metric("🏭 Unidades Producidas", f"{total_unidades:,}")
k5.metric("⏱️ Tiempo de Paro", f"{tiempo_paro_total:,.0f} min")

# Banner de alerta si hay órdenes críticas
if ordenes_alerta > 0:
    st.warning(
        f"⚠️ **{ordenes_alerta} órdenes** presentan una tasa de defectos superior al 10%. "
        f"Revisa la pestaña **Alertas de Calidad** para el detalle.",
        icon="🚨"
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# TABS — ORGANIZACIÓN DEL DASHBOARD
# ═══════════════════════════════════════════════════════════════
tab_produccion, tab_calidad, tab_alertas, tab_datos = st.tabs([
    "📅 Producción",
    "🌡️ Calidad & Eficiencia",
    "🚨 Alertas de Calidad",
    "📋 Datos & Exportar"
])

# ───────────────────────────────────────────────────────────────
# TAB 1 — PRODUCCIÓN
# ───────────────────────────────────────────────────────────────
with tab_produccion:
    st.subheader("Evolución temporal y distribución de paros")

    col_izq, col_der = st.columns([1.5, 1])

    with col_izq:
        produccion_semanal = (
            df_f.groupby('semana')
                .agg(unidades_producidas=('unidades_producidas', 'sum'))
                .reset_index()
        )
        fig_linea = px.line(
            produccion_semanal, x='semana', y='unidades_producidas',
            markers=True,
            title='📅 Evolución Semanal de Producción',
            labels={'semana': 'Semana', 'unidades_producidas': 'Unidades Producidas'},
            color_discrete_sequence=['#35b779']
        )
        fig_linea.update_traces(line_width=3, marker_size=8)
        fig_linea.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig_linea, use_container_width=True)

    with col_der:
        causas = df_f['causa_paro'].value_counts().reset_index()
        causas.columns = ['causa_paro', 'cantidad']
        fig_pie = px.pie(
            causas, names='causa_paro', values='cantidad',
            title='🛑 Causas de Paro',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Producción por línea en el período
    st.markdown("#### Producción Total por Línea en el Período")
    prod_linea = (
        df_f.groupby('linea_produccion')
            .agg(
                unidades=('unidades_producidas', 'sum'),
                ordenes=('id_orden', 'count'),
                paro_total=('tiempo_paro_min', 'sum')
            )
            .reset_index()
            .sort_values('unidades', ascending=False)
    )
    st.dataframe(
        prod_linea.rename(columns={
            'linea_produccion': 'Línea',
            'unidades': 'Unidades Producidas',
            'ordenes': 'N° Órdenes',
            'paro_total': 'Paro Total (min)'
        }),
        use_container_width=True,
        hide_index=True
    )

# ───────────────────────────────────────────────────────────────
# TAB 2 — CALIDAD & EFICIENCIA
# ───────────────────────────────────────────────────────────────
with tab_calidad:
    st.subheader("Análisis de eficiencia y correlación de defectos")

    col_izq2, col_der2 = st.columns([1, 1.5])

    with col_izq2:
        efic_linea = (
            df_f.groupby('linea_produccion')['eficiencia_pct']
                .mean()
                .reset_index()
                .sort_values('eficiencia_pct', ascending=True)
        )
        fig_bar = px.bar(
            efic_linea, y='linea_produccion', x='eficiencia_pct',
            orientation='h',
            title='⚙️ Eficiencia por Línea',
            labels={'eficiencia_pct': 'Eficiencia (%)', 'linea_produccion': ''},
            color='eficiencia_pct',
            color_continuous_scale='Viridis',
            text_auto='.1f'
        )
        fig_bar.add_vline(x=80, line_dash='dash', line_color='red',
                          annotation_text='Meta 80%', annotation_position='top right')
        fig_bar.update_layout(height=320, margin=dict(t=40, b=20), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_der2:
        fig_scatter = px.scatter(
            df_f, x='temperatura_c', y='tasa_defectos_pct',
            color='linea_produccion', size='unidades_producidas',
            hover_data=['maquina', 'turno', 'producto'],
            trendline='ols',
            title='🌡️ Temperatura vs Tasa de Defectos',
            labels={
                'temperatura_c': 'Temperatura (°C)',
                'tasa_defectos_pct': 'Tasa de Defectos (%)',
                'linea_produccion': 'Línea'
            },
            color_discrete_sequence=['#440154', '#31688e', '#35b779', '#fde725']
        )
        fig_scatter.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Heatmap completo
    st.markdown("#### 🌡️ Mapa de Calor — Tasa de Defectos por Turno y Línea")
    pivot = df_f.pivot_table(
        values='tasa_defectos_pct',
        index='turno',
        columns='linea_produccion',
        aggfunc='mean'
    ).round(2)

    fig_heat = px.imshow(
        pivot,
        color_continuous_scale='RdYlGn_r',
        text_auto=True,
        title='Tasa de Defectos Promedio (%) — Rojo = Mayor defecto'
    )
    fig_heat.update_layout(height=300, margin=dict(t=40, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

# ───────────────────────────────────────────────────────────────
# TAB 3 — ALERTAS DE CALIDAD (órdenes con defectos > 10%)
# ───────────────────────────────────────────────────────────────
with tab_alertas:
    df_alertas = df_f[df_f['tasa_defectos_pct'] > 10].copy()
    n_alertas = len(df_alertas)

    if n_alertas == 0:
        st.success("✅ No hay órdenes con tasa de defectos superior al 10% en el período y filtros seleccionados.")
    else:
        st.error(f"🚨 Se encontraron **{n_alertas} órdenes** con tasa de defectos > 10%")

        # Métricas de resumen de alertas
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Órdenes en alerta", n_alertas)
        a2.metric("Defecto prom. (alertas)", f"{df_alertas['tasa_defectos_pct'].mean():.2f}%")
        a3.metric("Unidades defectuosas", f"{df_alertas['unidades_defectuosas'].sum():,}")
        a4.metric("Costo asociado (COP)", f"${df_alertas['costo_produccion_cop'].sum():,.0f}")

        st.markdown("---")

        # Alertas por línea de producción
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            alertas_linea = df_alertas.groupby('linea_produccion').size().reset_index(name='alertas')
            fig_al = px.bar(
                alertas_linea.sort_values('alertas', ascending=False),
                x='linea_produccion', y='alertas',
                title='Alertas por Línea de Producción',
                color='alertas', color_continuous_scale='Reds',
                text_auto=True
            )
            fig_al.update_layout(height=280, showlegend=False, margin=dict(t=40, b=20))
            st.plotly_chart(fig_al, use_container_width=True)

        with col_a2:
            alertas_turno = df_alertas.groupby('turno').size().reset_index(name='alertas')
            fig_at = px.pie(
                alertas_turno, names='turno', values='alertas',
                title='Alertas por Turno',
                color_discrete_sequence=['#e74c3c', '#e67e22', '#f1c40f']
            )
            fig_at.update_layout(height=280, margin=dict(t=40, b=20))
            st.plotly_chart(fig_at, use_container_width=True)

        # Tabla de detalle de alertas
        st.markdown("#### 📋 Detalle de Órdenes en Alerta")
        cols_alerta = [
            'id_orden', 'fecha_produccion', 'linea_produccion', 'producto',
            'turno', 'maquina', 'unidades_producidas', 'unidades_defectuosas',
            'tasa_defectos_pct', 'eficiencia_pct', 'tiempo_paro_min',
            'causa_paro', 'costo_produccion_cop'
        ]
        df_alertas_show = (
            df_alertas[cols_alerta]
            .sort_values('tasa_defectos_pct', ascending=False)
            .reset_index(drop=True)
        )

        # Resaltar columna crítica con formato condicional
        st.dataframe(
            df_alertas_show.style.background_gradient(
                subset=['tasa_defectos_pct'], cmap='Reds'
            ).format({
                'tasa_defectos_pct': '{:.2f}%',
                'eficiencia_pct': '{:.1f}%',
                'costo_produccion_cop': '${:,.0f}'
            }),
            use_container_width=True,
            height=400
        )

        # Descarga específica de alertas
        st.download_button(
            label="⬇️ Descargar reporte de alertas (CSV)",
            data=df_alertas_show.to_csv(index=False).encode('utf-8'),
            file_name=f"alertas_defectos_{fecha_inicio}_{fecha_fin}.csv",
            mime='text/csv',
            type='primary'
        )

# ───────────────────────────────────────────────────────────────
# TAB 4 — DATOS & EXPORTAR
# ───────────────────────────────────────────────────────────────
with tab_datos:
    st.subheader("Explorador de datos filtrados")

    st.markdown(
        f"Mostrando **{len(df_f):,}** registros del período "
        f"`{fecha_inicio}` → `{fecha_fin}` con los filtros aplicados."
    )

    # Opciones de columnas a mostrar
    cols_disponibles = list(df_f.columns)
    cols_default = [
        'id_orden', 'fecha_produccion', 'linea_produccion', 'producto',
        'turno', 'maquina', 'unidades_producidas', 'unidades_defectuosas',
        'eficiencia_pct', 'tasa_defectos_pct', 'tiempo_paro_min',
        'causa_paro', 'costo_produccion_cop'
    ]
    cols_sel = st.multiselect(
        "Columnas a mostrar",
        options=cols_disponibles,
        default=[c for c in cols_default if c in cols_disponibles]
    )

    if cols_sel:
        df_mostrar = df_f[cols_sel].sort_values('fecha_produccion', ascending=False)
    else:
        df_mostrar = df_f.sort_values('fecha_produccion', ascending=False)

    st.dataframe(df_mostrar, use_container_width=True, height=450)

    st.markdown("---")
    st.markdown("#### ⬇️ Exportar datos")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        # Descarga del dataset filtrado completo
        csv_filtrado = df_f.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar dataset filtrado (CSV)",
            data=csv_filtrado,
            file_name=f"produccion_filtrado_{fecha_inicio}_{fecha_fin}.csv",
            mime='text/csv',
            help="Descarga todos los registros según los filtros y rango de fechas seleccionados"
        )

    with col_d2:
        # Resumen estadístico exportable
        resumen = df_f.describe().round(2)
        csv_resumen = resumen.to_csv().encode('utf-8')
        st.download_button(
            label="📊 Descargar resumen estadístico (CSV)",
            data=csv_resumen,
            file_name=f"resumen_estadistico_{fecha_inicio}_{fecha_fin}.csv",
            mime='text/csv',
            help="Descarga el resumen estadístico (media, std, min, max) del período filtrado"
        )

    # Vista previa del resumen estadístico
    with st.expander("📊 Ver resumen estadístico"):
        st.dataframe(df_f.describe().round(2), use_container_width=True)

st.markdown("---")
st.caption("🔧 Desarrollado con Streamlit + Plotly | MetalParts Colombia S.A.S.")