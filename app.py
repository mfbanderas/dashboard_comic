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

# --- 2. ESTILOS CSS (Forzar Modo Claro y Textos Oscuros) ---
st.markdown("""
    <style>
    /* 1. Fondo de toda la aplicación BLANCO */
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* 2. Todos los textos (H1, H2, Párrafos) en NEGRO PURO */
    h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown {
        color: #000000 !important;
    }
    
    /* 3. Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #F9FAFB !important; /* Gris muy clarito para diferenciar */
        border: 1px solid #E5E7EB !important;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        height: 140px;
    }
    
    /* Etiquetas y Valores de Métricas */
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricValue"] {
        color: #E74C3C !important; /* Rojo corporativo */
    }
    
    /* 4. Caja para el Gauge (Columna 4) */
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {
        background-color: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        padding: 10px;
        height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Sidebar blanca */
    [data-testid="stSidebar"] {
        background-color: #F3F4F6 !important;
    }
    
    /* Arreglo para títulos de Plotly */
    .gtitle {
        fill: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Colores
C_RED = '#E74C3C'
C_BLACK = '#000000' # Negro puro
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

    # Limpieza de nombres de columna
    df.columns = df.columns.str.strip()
    
    # Rellenar vacíos
    if "A7. Rol Principal" in df.columns:
        df["A7. Rol Principal"] = df["A7. Rol Principal"].fillna("Sin especificar")
    
    if "A2. Identidad de género" in df.columns:
        df["A2. Identidad de género"] = df["A2. Identidad de género"].fillna("No responde")

    # Procesar fechas
    if 'Fecha' in df.columns and 'Hora' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        # Fallback si fecha es nula
        df['Fecha_dt'] = df['Fecha_dt'].fillna(pd.Timestamp.today())
        df['Hora_dt'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
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
        df['Ubicación Final'] = df['Ubicación Final'].fillna("Desconocido")
        
    return df

try:
    df = load_data()
    if df is not None:
        # --- 4. FILTROS ---
        with st.sidebar:
            st.header("🎛️ Panel de Control")
            
            if "A7. Rol Principal" in df.columns:
                roles_unicos = sorted(df["A7. Rol Principal"].unique())
                seleccion_roles = st.multiselect(
                    "Rol Profesional:", 
                    options=["(Seleccionar Todos)"] + list(roles_unicos), 
                    default=["(Seleccionar Todos)"]
                )
                roles_activos = roles_unicos if "(Seleccionar Todos)" in seleccion_roles else seleccion_roles
            else:
                roles_activos = []
            
            if 'Fecha_dt' in df.columns:
                min_date = df['Fecha_dt'].min().date()
                max_date = df['Fecha_dt'].max().date()
                fechas = st.date_input("Rango de Fechas:", value=(min_date, max_date))
                if isinstance(fechas, tuple) and len(fechas) == 2:
                    start_date, end_date = fechas
                else:
                    start_date, end_date = min_date, max_date

        mask = (df["A7. Rol Principal"].isin(roles_activos)) & \
               (df['Fecha_dt'].dt.date >= start_date) & \
               (df['Fecha_dt'].dt.date <= end_date)
        
        df_filtered = df[mask]

        # --- 5. VISUALIZACIÓN ---
        st.markdown(f"<h1>Monitor Avance Estudio | Mujeres en el Cómic <span style='color:{C_RED}'>2026</span></h1>", unsafe_allow_html=True)
        st.markdown("Reporte diario de avance y calidad de la muestra.")

        # KPIs
        META = 150
        total_real = len(df)
        pct_avance = (total_real/META)*100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Muestra Filtrada", len(df_filtered))
        col2.metric("Total Real", total_real)
        col3.metric("Faltantes", META - total_real)
        
        with col4:
            # GAUGE
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = pct_avance,
                title = {'text': "AVANCE %", 'font': {'size': 14, 'color': "black"}}, # TEXTO NEGRO
                number = {'suffix': "%", 'font': {'size': 36, 'color': C_RED}},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': C_RED}, 'bgcolor': "white"}
            ))
            fig_gauge.update_layout(
                height=130, 
                margin=dict(t=40, b=0, l=15, r=15), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font={'color': 'black', 'family': 'Arial'} # FUENTE NEGRA GLOBAL
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")

        # GRÁFICOS
        st.markdown("### 1. Dinámica de Respuesta")
        c1, c2 = st.columns((2, 1))
        
        with c1:
            st.markdown("**📅 Evolución Diaria**")
            diario = df_filtered.groupby('Fecha_dt').size().reset_index(name='Encuestas')
            fig_line = px.line(diario, x='Fecha_dt', y='Encuestas', markers=True)
            fig_line.update_traces(line_color='#2C3E50', marker_color=C_RED)
            fig_line.update_layout(
                paper_bgcolor='white', 
                plot_bgcolor='white', 
                font={'color': 'black'}, # TEXTO NEGRO
                yaxis_gridcolor='#EEEEEE',
                xaxis_gridcolor='#EEEEEE'
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
        with c2:
            st.markdown("**⏰ Horas Punta**")
            if 'Hora_dt' in df_filtered.columns:
                horas = df_filtered['Hora_dt'].value_counts().sort_index().reset_index()
                horas.columns = ['Hora', 'Cantidad']
                all_hours = pd.DataFrame({'Hora': range(24)})
                horas = all_hours.merge(horas, on='Hora', how='left').fillna(0)
                fig_bar_h = px.bar(horas, x='Hora', y='Cantidad', text='Cantidad', color_discrete_sequence=[C_BLUE])
                fig_bar_h.update_traces(textposition='outside')
                fig_bar_h.update_layout(
                    paper_bgcolor='white', 
                    plot_bgcolor='white', 
                    font={'color': 'black'}, # TEXTO NEGRO
                    xaxis=dict(tickmode='linear', dtick=1), 
                    yaxis_gridcolor='#EEEEEE'
                )
                st.plotly_chart(fig_bar_h, use_container_width=True)

        st.markdown("### 2. Perfil del Encuestado")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**Género**")
            col_genero = 'A2. Identidad de género'
            if col_genero in df_filtered.columns:
                genero = df_filtered[col_genero].value_counts().reset_index()
                genero.columns = ['Género', 'Cantidad']
                fig_pie = px.pie(genero, values='Cantidad', names='Género', hole=0.5, color_discrete_sequence=PALETTE)
                # Leyenda y textos en negro
                fig_pie.update_layout(
                    paper_bgcolor='white', 
                    font={'color': 'black'},
                    legend=dict(font=dict(color="black"))
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with c4:
            st.markdown("**Roles Principales**")
            roles = df_filtered['A7. Rol Principal'].value_counts().head(7).reset_index()
            roles.columns = ['Rol', 'Cantidad']
            fig_rol = px.bar(roles, y='Rol', x='Cantidad', orientation='h', text='Cantidad', color_discrete_sequence=[C_YELLOW])
            fig_rol.update_traces(textposition='inside', textfont=dict(color='black')) # Texto dentro de barra negro
            fig_rol.update_layout(
                paper_bgcolor='white', 
                plot_bgcolor='white', 
                font={'color': 'black'}, # Ejes en negro
                xaxis_visible=False
            )
            st.plotly_chart(fig_rol, use_container_width=True)

        st.markdown("**Distribución Geográfica (Top 15)**")
        ubic = df_filtered['Ubicación Final'].value_counts().head(15).reset_index()
        ubic.columns = ['Lugar', 'Cantidad']
        fig_ubic = px.bar(ubic, x='Lugar', y='Cantidad', text='Cantidad', color_discrete_sequence=['#000000'])
        fig_ubic.update_traces(textposition='outside')
        fig_ubic.update_layout(
            paper_bgcolor='white', 
            plot_bgcolor='white', 
            font={'color': 'black'}, # Texto ejes negro
            yaxis_visible=False, 
            margin=dict(b=50)
        )
        st.plotly_chart(fig_ubic, use_container_width=True)

        st.markdown("---")
        st.markdown("<div style='text-align: center; color: black; font-size: 12px;'>Dashboard generado con Python Streamlit</div>", unsafe_allow_html=True)

    else:
        st.error("⚠️ Error: No se pudo cargar 'results-survey1.csv'.")

except Exception as e:
    st.error(f"Error inesperado: {e}")