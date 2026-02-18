# streamlit run app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Monitor Avance | Encuesta Cómic",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILOS CSS PERSONALIZADOS (AESTHETIC & BIG NUMBERS) ---
st.markdown("""
    <style>
    /* 1. FONDO GENERAL (Gris muy suave para contraste limpio) */
    .stApp {
        background-color: #F8F9FA !important;
        color: #2C3E50 !important;
    }
    
    /* 2. TÍTULOS CON MARCA ROJA VERTICAL */
    h1, h2, h3 {
        color: #2C3E50 !important;
        border-left: 5px solid #E74C3C !important;
        padding-left: 15px !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* 3. TARJETAS DE MÉTRICAS (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        padding: 20px !important;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        text-align: center;
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* ETIQUETAS DE MÉTRICAS */
    [data-testid="stMetricLabel"] {
        color: #7F8C8D !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }
    
    /* VALORES DE MÉTRICAS (GIGANTES 55px) */
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
        color: #E74C3C !important;
        font-size: 45px !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
    }
    
    /* 4. CAJA BLANCA PARA EL GAUGE (Columna 4) */
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        padding: 10px;
        height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* 5. SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E0E0E0;
    }
    
    /* AJUSTE PARA TÍTULOS DE GRÁFICOS */
    .gtitle {
        font-family: 'Arial', sans-serif !important;
        fill: #2C3E50 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. PALETA DE COLORES CORPORATIVA ---
C_RED    = '#E74C3C'
C_BLACK  = '#2C3E50'
C_BLUE   = '#3498DB'
C_YELLOW = '#F1C40F'
PALETTE  = [C_RED, C_BLACK, C_BLUE, C_YELLOW]

# --- 4. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def load_data():
    file_name = 'results-survey1.csv'
    try:
        # Intento 1: UTF-8 con punto y coma
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')
    except:
        try:
            # Intento 2: Latin-1 con punto y coma
            df = pd.read_csv(file_name, sep=';', encoding='latin-1')
        except:
            return None

    # LIMPIEZA CLAVE: Quitar espacios en blanco de los nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Relleno de datos faltantes para evitar errores
    if "A7. Rol Principal" in df.columns:
        df["A7. Rol Principal"] = df["A7. Rol Principal"].fillna("Sin especificar")
    
    if "A2. Identidad de género" in df.columns:
        df["A2. Identidad de género"] = df["A2. Identidad de género"].fillna("No responde")

    # Procesamiento de Fechas y Horas
    if 'Fecha' in df.columns and 'Hora' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        # Si alguna fecha falla, usar la fecha actual como fallback seguro
        df['Fecha_dt'] = df['Fecha_dt'].fillna(pd.Timestamp.today())
        df['Hora_dt'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
        
    # Procesamiento de Ubicación (Provincia o País)
    if 'A5. Provincia de residencia' in df.columns:
        df['Ubicación Final'] = df.apply(
            lambda x: x['A5. Provincia de residencia'] if pd.notna(x['A5. Provincia de residencia']) 
            else x.get('A5a. País Extranjero', 'Desconocido'), axis=1
        )
        df['Ubicación Final'] = df['Ubicación Final'].fillna("Desconocido")
        
    return df

# --- 5. LÓGICA PRINCIPAL ---
try:
    df = load_data()
    
    if df is None:
        st.error("⚠️ No se pudo leer el archivo 'results-survey1.csv'. Verifica que esté en la carpeta.")
    else:
        # --- SIDEBAR (FILTROS) ---
        with st.sidebar:
            st.header("🎛️ Filtros")
            
            # Filtro Rol
            if "A7. Rol Principal" in df.columns:
                roles = sorted(df["A7. Rol Principal"].unique())
                sel_rol = st.multiselect("Rol Principal:", ["Todos"] + list(roles), default=["Todos"])
                filtro_rol = roles if "Todos" in sel_rol else sel_rol
            else:
                filtro_rol = []
            
            # Filtro Fecha
            if 'Fecha_dt' in df.columns:
                min_d, max_d = df['Fecha_dt'].min().date(), df['Fecha_dt'].max().date()
                fechas = st.date_input("Fechas:", (min_d, max_d))
                inicio, fin = fechas if isinstance(fechas, tuple) and len(fechas)==2 else (min_d, max_d)

        # Aplicar Filtros
        mask = (df["A7. Rol Principal"].isin(filtro_rol)) & \
               (df['Fecha_dt'].dt.date >= inicio) & (df['Fecha_dt'].dt.date <= fin)
        df_filtered = df[mask]

        # --- CABECERA ---
        st.markdown(f"<h1>Monitor de Avance | <span style='color:{C_RED}'>Encuesta Mujeres en el Cómic 2026</span></h1>", unsafe_allow_html=True)
        st.markdown("Visión general del estado de la recolección de datos.")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECCIÓN KPIs ---
        META = 150
        total_real = len(df) # Total sin filtros para el % real
        pct_avance = (total_real / META) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Respuestas", len(df_filtered)) # Muestra filtrada
        c2.metric("Meta", META)
        c3.metric("Faltantes", META - total_real)
        
        with c4:
            # GAUGE (MEDIDOR)
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = pct_avance,
                title = {'text': "AVANCE GLOBAL", 'font': {'size': 12, 'color': "gray"}},
                number = {'suffix': "%", 'font': {'size': 30, 'color': C_RED, 'weight': 'bold'}}, # Tamaño ajustado
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 0, 'tickcolor': "white"},
                    'bar': {'color': C_RED},
                    'bgcolor': "#F0F2F6",
                    'borderwidth': 0,
                    'bordercolor': "white"
                }
            ))
            fig_g.update_layout(
                height=140, margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)', font={'family': "Arial"}
            )
            st.plotly_chart(fig_g, use_container_width=True)

        st.markdown("---")

        # --- FUNCIÓN DE ESTILO DE GRÁFICOS ---
        def aplicar_estilo(fig, mt=30):
            fig.update_layout(
                paper_bgcolor='white',
                plot_bgcolor='white',
                font={'color': C_BLACK, 'size': 14}, # Texto negro/gris oscuro legible
                margin=dict(l=20, r=50, t=mt, b=20), # Margen derecho extra para que no se corte
                showlegend=False
            )
            # Ejes visibles, finos y grises (Aesthetic)
            fig.update_xaxes(showline=True, linewidth=1, linecolor='#D1D5DB', gridcolor='#F0F2F6', zeroline=False)
            fig.update_yaxes(showline=True, linewidth=1, linecolor='#D1D5DB', gridcolor='#F0F2F6', zeroline=False)
            return fig

        # --- GRÁFICOS TEMPORALES ---
        st.markdown("### Dinámica de Respuesta")
        g1, g2 = st.columns((2, 1))
        
        with g1:
            st.markdown("**📅 Evolución Diaria**")
            diario = df_filtered.groupby('Fecha_dt').size().reset_index(name='N')
            fig1 = px.line(diario, x='Fecha_dt', y='N', markers=True)
            fig1.update_traces(line_color=C_BLACK, marker_color=C_RED, line_width=3, marker_size=8)
            fig1 = aplicar_estilo(fig1)
            st.plotly_chart(fig1, use_container_width=True)
            
        with g2:
            st.markdown("**⏰ Hora Punta**")
            if 'Hora_dt' in df_filtered.columns:
                horas = df_filtered['Hora_dt'].value_counts().sort_index().reindex(range(24), fill_value=0).reset_index()
                horas.columns = ['Hora', 'N']
                fig2 = px.bar(horas, x='Hora', y='N', text='N', color_discrete_sequence=[C_BLUE])
                fig2.update_traces(textposition='outside')
                fig2 = aplicar_estilo(fig2, mt=25) # Margen top 15 solicitado
                fig2.update_xaxes(tickmode='linear', dtick=4) # Menos etiquetas para limpiar
                st.plotly_chart(fig2, use_container_width=True)

        # --- GRÁFICOS DEMOGRÁFICOS ---
        st.markdown("### Perfil del Encuestado")
        g3, g4 = st.columns(2)
        
        with g3:
            st.markdown("**Género**")
            if 'A2. Identidad de género' in df_filtered.columns:
                gen = df_filtered['A2. Identidad de género'].value_counts().reset_index()
                gen.columns = ['Género', 'N']
                fig3 = px.pie(gen, values='N', names='Género', hole=0.5, color_discrete_sequence=PALETTE)
                fig3.update_layout(
                    paper_bgcolor='white', font={'color': C_BLACK, 'size': 20},
                    margin=dict(l=20, r=50, t=30, b=20),
                    legend=dict(orientation="h", y=-0.1, font=dict(size=15)) # Leyenda abajo
                )
                st.plotly_chart(fig3, use_container_width=True)
                
        with g4:
            st.markdown("**Roles Principales**")
            rol = df_filtered['A7. Rol Principal'].value_counts().head(7).reset_index()
            rol.columns = ['Rol', 'N']
            fig4 = px.bar(rol, y='Rol', x='N', orientation='h', text='N', color_discrete_sequence=[C_YELLOW])
            fig4.update_traces(textposition='inside', textfont_color='black')
            fig4 = aplicar_estilo(fig4)
            fig4.update_yaxes(autorange="reversed") # Ordenar de mayor a menor
            st.plotly_chart(fig4, use_container_width=True)

        # --- UBICACIÓN ---
        st.markdown("### Distribución Geográfica (Top 15)")
        geo = df_filtered['Ubicación Final'].value_counts().head(15).reset_index()
        geo.columns = ['Lugar', 'N']
        fig5 = px.bar(geo, x='Lugar', y='N', text='N', color_discrete_sequence=[C_BLACK])
        fig5.update_traces(textposition='outside')
        fig5 = aplicar_estilo(fig5)
        fig5.update_layout(margin=dict(b=60)) # Margen inferior para etiquetas largas
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown("---")
        st.caption("Dashboard generado automáticamente con Python & Streamlit.")

except Exception as e:
    st.error(f"Se ha producido un error inesperado: {e}")