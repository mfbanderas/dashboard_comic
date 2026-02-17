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

# --- 2. ESTILOS CSS "AESTHETIC" (TEXTO GRANDE 40px) ---
st.markdown("""
    <style>
    /* 1. Fondo General Aesthetic */
    .stApp {
        background-color: #F0F2F6 !important;
        color: #262730 !important;
    }
    
    /* 2. Títulos con Marca Roja Vertical */
    h1, h2, h3 {
        color: #1F2937 !important;
        border-left: 6px solid #E74C3C !important;
        padding-left: 20px !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 3. Aumentar tamaño de texto general */
    p, li, label, .stMarkdown, div {
        font-size: 16px !important;
    }
    
    /* 4. Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Etiquetas (Label) */
    [data-testid="stMetricLabel"] {
        color: #6B7280 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* VALORES (Los números en rojo) - AHORA TAMAÑO 40px */
    [data-testid="stMetricValue"] {
        color: #E74C3C !important;
        font-size: 150px !important; /* <--- CAMBIO AQUÍ */
        font-weight: 900 !important;
    }
    
    /* 5. Caja Blanca para el Gauge */
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 10px;
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
    }
    </style>
""", unsafe_allow_html=True)

# Paleta de Colores
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
    
    # Rellenar vacíos
    if "A7. Rol Principal" in df.columns:
        df["A7. Rol Principal"] = df["A7. Rol Principal"].fillna("Sin especificar")
    
    if "A2. Identidad de género" in df.columns:
        df["A2. Identidad de género"] = df["A2. Identidad de género"].fillna("No responde")

    # Fechas
    if 'Fecha' in df.columns and 'Hora' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df['Fecha_dt'] = df['Fecha_dt'].fillna(pd.Timestamp.today())
        df['Hora_dt'] = pd.to_datetime(df['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
    elif 'Fecha de envío' in df.columns:
         df['Fecha_Completa'] = pd.to_datetime(df['Fecha de envío'], dayfirst=True, errors='coerce')
         df['Fecha_dt'] = df['Fecha_Completa'].dt.normalize()
         df['Hora_dt'] = df['Fecha_Completa'].dt.hour
         
    # Ubicación
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

        # --- 5. DASHBOARD ---
        st.markdown(f"<h1>Monitor Avance Estudio <span style='color:{C_RED}'>2026</span></h1>", unsafe_allow_html=True)
        st.markdown("Reporte diario de avance y calidad de la muestra.")
        st.markdown("<br>", unsafe_allow_html=True)

        # KPIs (ACTUALIZADOS CON TU LÓGICA)
        META = 150
        total_real = len(df)
        pct_avance = (total_real/META)*100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Respuestas", len(df_filtered)) # Filtradas
        with col2:
            st.metric("Meta", META)                   # Meta Fija
        with col3:
            st.metric("Faltantes", META - total_real) # Faltantes reales
            
        with col4:
            # GAUGE
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = pct_avance,
                title = {'text': "AVANCE %", 'font': {'size': 15, 'color': "#555"}}, 
                number = {'suffix': "%", 'font': {'size': 40, 'color': C_RED, 'weight': 'bold'}},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': C_RED}, 'bgcolor': "#f0f2f6"}
            ))
            fig_gauge.update_layout(
                height=130, 
                margin=dict(t=40, b=0, l=15, r=15), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font={'color': C_BLACK, 'family': 'Arial'}
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")

        # --- FUNCIÓN DE ESTILO (Letra Grande + Margen + Ejes Grises) ---
        def estilo_grafico(fig, margin_top=40):
            fig.update_layout(
                paper_bgcolor='white', 
                plot_bgcolor='white', 
                font={'color': '#2C3E50', 'size': 14}, # Letra más grande y oscura
                margin=dict(l=20, r=60, t=margin_top, b=20)
            )
            fig.update_xaxes(
                showline=True, linewidth=1, linecolor='#D1D5DB', 
                showgrid=False, zeroline=False,
                tickfont=dict(size=12)
            )
            fig.update_yaxes(
                showline=True, linewidth=1, linecolor='#D1D5DB', 
                showgrid=True, gridcolor='#F3F4F6',
                zeroline=False,
                tickfont=dict(size=12)
            )
            return fig

        # GRÁFICOS TEMPORALES
        st.markdown("### Dinámica de Respuesta")
        c1, c2 = st.columns((2, 1))
        
        with c1:
            st.markdown("**📅 Evolución Diaria**")
            diario = df_filtered.groupby('Fecha_dt').size().reset_index(name='Encuestas')
            fig_line = px.line(diario, x='Fecha_dt', y='Encuestas', markers=True)
            fig_line.update_traces(line_color=C_BLACK, marker_color=C_RED, line_width=3, marker_size=8)
            fig_line = estilo_grafico(fig_line)
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
                # Margen superior 15 para hora punta
                fig_bar_h = estilo_grafico(fig_bar_h, margin_top=15)
                fig_bar_h.update_xaxes(tickmode='linear', dtick=4)
                st.plotly_chart(fig_bar_h, use_container_width=True)

        # GRÁFICOS PERFIL
        st.markdown("### Perfil del Encuestado")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**Género**")
            col_genero = 'A2. Identidad de género'
            if col_genero in df_filtered.columns:
                genero = df_filtered[col_genero].value_counts().reset_index()
                genero.columns = ['Género', 'Cantidad']
                fig_pie = px.pie(genero, values='Cantidad', names='Género', hole=0.5, color_discrete_sequence=PALETTE)
                fig_pie.update_layout(
                    paper_bgcolor='white', 
                    font={'color': '#2C3E50', 'size': 14},
                    legend=dict(font=dict(size=12)),
                    margin=dict(l=20, r=60, t=30, b=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with c4:
            st.markdown("**Roles Principales**")
            roles = df_filtered['A7. Rol Principal'].value_counts().head(7).reset_index()
            roles.columns = ['Rol', 'Cantidad']
            fig_rol = px.bar(roles, y='Rol', x='Cantidad', orientation='h', text='Cantidad', color_discrete_sequence=[C_YELLOW])
            fig_rol.update_traces(textposition='inside', textfont=dict(color='black', size=14)) 
            fig_rol = estilo_grafico(fig_rol)
            fig_rol.update_xaxes(visible=False)
            st.plotly_chart(fig_rol, use_container_width=True)

        # GRÁFICO GEOGRAFÍA
        st.markdown("### Distribución Geográfica (Top 15)")
        ubic = df_filtered['Ubicación Final'].value_counts().head(15).reset_index()
        ubic.columns = ['Lugar', 'Cantidad']
        fig_ubic = px.bar(ubic, x='Lugar', y='Cantidad', text='Cantidad', color_discrete_sequence=[C_BLACK])
        fig_ubic.update_traces(textposition='outside')
        fig_ubic = estilo_grafico(fig_ubic, margin_top=30)
        fig_ubic.update_yaxes(visible=False)
        fig_ubic.update_layout(margin=dict(b=80, r=60)) 
        st.plotly_chart(fig_ubic, use_container_width=True)

        st.markdown("---")
        st.markdown("<div style='text-align: center; color: #666; font-size: 14px;'>Dashboard generado con Python Streamlit</div>", unsafe_allow_html=True)

    else:
        st.error("⚠️ Error: No se pudo cargar 'results-survey1.csv'.")

except Exception as e:
    st.error(f"Error inesperado: {e}")