# streamlit run app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Monitor Avance Estudio | Mujeres en el Cómic",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILOS CSS "PREMIUM" ---
st.markdown("""
    <style>
    /* 1. Fondo general */
    .stApp {
        background-color: #F0F2F6;
    }
    
    /* 2. Títulos */
    h1 {
        color: #1F2937;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    h3 {
        color: #4B5563;
        font-weight: 600;
        padding-top: 10px;
        border-bottom: 2px solid #E74C3C;
        display: inline-block;
        margin-bottom: 20px;
    }
    
    /* 3. Estilo para las MÉTRICAS (Las 3 primeras) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        height: 140px; /* Altura fija */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6B7280;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetricValue"] {
        color: #E74C3C;
        font-size: 2.2rem;
        font-weight: 700;
    }
    
    /* 4. SOLUCIÓN ROBUSTA PARA LA TARJETA DEL GRÁFICO (Columna 4) */
    /* Apuntamos directamente al bloque vertical de la 4ta columna */
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 10px;
        height: 140px; /* Forzamos la misma altura que las métricas */
        display: flex;
        align-items: center;     /* Centrar verticalmente */
        justify-content: center; /* Centrar horizontalmente */
    }

    /* 5. Ajustes de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    </style>
""", unsafe_allow_html=True)

# Paleta de Colores Corporativa
C_RED = '#E74C3C'
C_BLACK = '#2C3E50'
C_BLUE = '#3498DB'
C_YELLOW = '#F1C40F'
PALETTE = [C_RED, C_BLACK, C_BLUE, C_YELLOW]

# --- 3. CARGA DE DATOS ---
@st.cache_data
def load_data():
    file_name = 'results-survey1.csv'
    try:
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_name, sep=';', encoding='latin-1')
        except:
             return None 

    df.columns = df.columns.str.strip()
    
    # Procesar fechas y horas (Soporta ambos formatos de tus archivos)
    if 'Fecha' in df.columns and 'Hora' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df['Hora_dt'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
        df['Fecha_Completa'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora'], dayfirst=True, errors='coerce')
    elif 'Fecha de envío' in df.columns:
         df['Fecha_Completa'] = pd.to_datetime(df['Fecha de envío'], dayfirst=True, errors='coerce')
         df['Fecha_dt'] = df['Fecha_Completa'].dt.normalize()
         df['Hora_dt'] = df['Fecha_Completa'].dt.hour
    
    # Procesar ubicación
    if 'A5. Provincia de residencia' in df.columns:
        df['Ubicación Final'] = df.apply(
            lambda x: x['A5. Provincia de residencia'] if pd.notna(x['A5. Provincia de residencia']) 
            else x.get('A5a. País Extranjero', 'Desconocido'), axis=1
        )
    return df

try:
    df = load_data()
    
    if df is not None:
        # --- 4. BARRA LATERAL ---
        with st.sidebar:
            st.header("🎛️ Panel de Control")
            st.write("Filtra los datos para personalizar el reporte.")
            st.markdown("---")
            
            # Filtro de Roles (Si existe la columna)
            if "A7. Rol Principal" in df.columns:
                roles_unicos = sorted(df["A7. Rol Principal"].dropna().unique())
                seleccion_roles = st.multiselect(
                    "Rol Profesional:",
                    options=["(Seleccionar Todos)"] + list(roles_unicos),
                    default=["(Seleccionar Todos)"]
                )
                roles_activos = roles_unicos if "(Seleccionar Todos)" in seleccion_roles else seleccion_roles
            else:
                roles_activos = []

            # Filtro de Fechas
            if 'Fecha_dt' in df.columns and not df['Fecha_dt'].isnull().all():
                min_date, max_date = df['Fecha_dt'].min().date(), df['Fecha_dt'].max().date()
                fechas = st.date_input("Rango de Fechas:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                start_date, end_date = fechas if len(fechas) == 2 else (min_date, max_date)
            else:
                start_date, end_date = None, None

            st.markdown("---")
            st.caption("v3.0 - Monitor Final")

        # Aplicar Filtro
        mask = pd.Series([True] * len(df))
        if "A7. Rol Principal" in df.columns:
             mask = mask & (df["A7. Rol Principal"].isin(roles_activos))
        if start_date and end_date:
             mask = mask & (df['Fecha_dt'].dt.date >= start_date) & (df['Fecha_dt'].dt.date <= end_date)
        
        df_filtered = df[mask]

        # --- 5. LAYOUT PRINCIPAL ---
        
        st.markdown("<h1>Monitor Avance Estudio | Mujeres en el Cómic <span style='color:#E74C3C'>2026</span></h1>", unsafe_allow_html=True)
        st.markdown("Reporte diario de avance y calidad de la muestra.")
        st.markdown("<br>", unsafe_allow_html=True) 

       # BLOQUE 1: KPIs
        META = 150
        pct_avance = (len(df)/META)*100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Encuestas", len(df_filtered))
        with col2:
            st.metric("Meta Objetivo", META)
        with col3:
            st.metric("Faltantes", META - len(df))
        with col4:
            # Mini Gauge (Medidor) 
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = pct_avance,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "AVANCE %", 'font': {'size': 14, 'color': "#6B7280"}},
                number = {'suffix': "%", 'font': {'size': 36, 'color': C_RED, 'family': "Arial", 'weight': 'bold'}},
                gauge = {
                    'axis': {'range': [None, 100], 'visible': False},
                    'bar': {'color': C_RED},
                    'bgcolor': "#ecf0f1",
                    'borderwidth': 0,
                    'steps': [{'range': [0, 100], 'color': "white"}]
                }
            ))
            # Ajuste de márgenes para que encaje y no corte el texto
            fig_gauge.update_layout(
                height=130, 
                margin=dict(t=40, b=0, l=15, r=15),
                paper_bgcolor='rgba(0,0,0,0)', 
                font={'family': "Arial"}
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")

        # BLOQUE 2: TIEMPO 
        st.markdown("### 1. Dinámica de Respuesta")
        
        c1, c2 = st.columns((2, 1))
        
        with c1:
            st.markdown("**📅 Evolución Diaria**")
            if not df_filtered.empty and 'Fecha_dt' in df_filtered.columns:
                diario = df_filtered.groupby('Fecha_dt').size().reset_index(name='Encuestas')
                fig_line = px.line(diario, x='Fecha_dt', y='Encuestas', markers=True)
                fig_line.update_traces(line_color=C_BLACK, line_width=3, marker_color=C_RED, marker_size=8)
                fig_line.update_layout(
                    plot_bgcolor='white', 
                    yaxis_gridcolor='#F0F0F0', 
                    margin=dict(t=10),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            
        with c2:
            st.markdown("**⏰ Horas Punta**")
            if not df_filtered.empty and 'Hora_dt' in df_filtered.columns:
                # Preparación de datos (0-23)
                horas = df_filtered['Hora_dt'].value_counts().sort_index().reset_index()
                horas.columns = ['Hora', 'Cantidad']
                all_hours = pd.DataFrame({'Hora': range(24)})
                horas = all_hours.merge(horas, on='Hora', how='left').fillna(0)
                
                fig_bar_h = px.bar(
                    horas, 
                    x='Hora', 
                    y='Cantidad', 
                    text='Cantidad', 
                    color_discrete_sequence=[C_BLUE]
                )
                
                fig_bar_h.update_traces(
                    textposition='outside',
                    marker_line_color=C_BLACK, 
                    marker_line_width=1
                )
                
                fig_bar_h.update_layout(
                    xaxis=dict(tickmode='linear', tick0=0, dtick=1), # TODAS LAS HORAS
                    plot_bgcolor='white', 
                    yaxis_gridcolor='#EEE', 
                    height=300, 
                    margin=dict(l=10, r=10, t=20, b=10),
                    yaxis=dict(showticklabels=False)
                )
                st.plotly_chart(fig_bar_h, use_container_width=True)

        # BLOQUE 3: CALIDAD MUESTRA
        st.markdown("### 2. Perfil del Encuestado")
        
        c3, c4 = st.columns((1, 1))
        
        with c3:
            st.markdown("**Género**")
            if not df_filtered.empty and 'A2. Identidad de género' in df_filtered.columns:
                genero = df_filtered['A2. Identidad de género'].value_counts().reset_index()
                genero.columns = ['Género', 'Cantidad']
                fig_pie = px.pie(genero, values='Cantidad', names='Género', hole=0.5, color_discrete_sequence=PALETTE)
                fig_pie.update_traces(textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_pie, use_container_width=True)
            
        with c4:
            st.markdown("**Roles Principales**")
            if not df_filtered.empty and "A7. Rol Principal" in df_filtered.columns:
                roles = df_filtered['A7. Rol Principal'].value_counts().head(7).reset_index()
                roles.columns = ['Rol', 'Cantidad']
                fig_rol = px.bar(roles, y='Rol', x='Cantidad', orientation='h', text='Cantidad', color_discrete_sequence=[C_YELLOW])
                fig_rol.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color='black'))
                fig_rol.update_layout(
                    plot_bgcolor='white', 
                    xaxis_visible=False, 
                    yaxis={'categoryorder':'total ascending'},
                    margin=dict(t=15)
                )
                st.plotly_chart(fig_rol, use_container_width=True)

        # BLOQUE 4: GEOGRAFÍA
        st.markdown("**Distribución Geográfica (Top 15)**")
        if not df_filtered.empty and 'Ubicación Final' in df_filtered.columns:
            ubic = df_filtered['Ubicación Final'].value_counts().head(15).reset_index()
            ubic.columns = ['Lugar', 'Cantidad']
            
            fig_ubic = px.bar(
                ubic, 
                x='Lugar', 
                y='Cantidad', 
                text='Cantidad', 
                color_discrete_sequence=[C_BLACK],
                labels={'Lugar': 'Provincia Residencia'}
            )
            
            fig_ubic.update_traces(textposition='outside')
            
            fig_ubic.update_layout(
                plot_bgcolor='white', 
                yaxis_visible=False, 
                height=400,
                margin=dict(t=20, b=50)
            )
            
            st.plotly_chart(fig_ubic, use_container_width=True)
        
        # FOOTER
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #888; font-size: 12px;'>Dashboard generado con Python Streamlit</div>", 
            unsafe_allow_html=True
        )
    else:
        st.error("⚠️ No se pudo cargar el archivo 'results-survey1.csv'. Verifica que esté en la misma carpeta.")

except Exception as e:
    st.error(f"Error inesperado: {e}")