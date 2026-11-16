# RadarPe · Dashboard (Streamlit)
import pandas as pd
import streamlit as st

st.set_page_config(page_title='RadarPe', layout='wide')

SECTORES = {'MIN': 'Minería e hidrocarburos', 'AGR': 'Agro y agroexportación', 'PES': 'Pesca y acuicultura',
            'MAN': 'Manufactura e industria', 'CON': 'Construcción e inmobiliario', 'COM': 'Comercio y retail',
            'TRA': 'Transporte y logística', 'TUR': 'Turismo y gastronomía', 'FIN': 'Finanzas y seguros',
            'ENE': 'Energía y telecomunicaciones'}
IMPACTO = {'R': 'Riesgo', 'O': 'Oportunidad', 'N': 'Neutral'}


@st.cache_data                                                       # lee los archivos una sola vez
def cargar():
    noticias = pd.read_csv('noticias.csv', parse_dates=['fecha'])
    pred = pd.read_csv('pred_sector_impacto.csv')
    return noticias, pred


noticias, pred = cargar()

# ---------- Filtros (barra lateral) ----------
st.sidebar.title('RadarPe')
f_min, f_max = noticias['fecha'].min().date(), noticias['fecha'].max().date()
rango = st.sidebar.date_input('Rango de fechas', (f_max - pd.Timedelta(days=6), f_max), min_value=f_min, max_value=f_max)
if len(rango) != 2:                                                   # mientras se elige la segunda fecha
    st.stop()
sectores = st.sidebar.multiselect('Sector', list(SECTORES), default=['MIN'], format_func=SECTORES.get)
impactos = st.sidebar.multiselect('Impacto', list(IMPACTO), default=list(IMPACTO), format_func=IMPACTO.get)

# ---------- Aplicar filtros ----------
en_fecha = noticias[(noticias['fecha'].dt.date >= rango[0]) & (noticias['fecha'].dt.date <= rango[1])]
elegidas = pred[pred['sector'].isin(sectores) & pred['impacto'].isin(impactos)]
res = en_fecha.merge(elegidas, on='id')                               # una fila por par noticia-sector

# ---------- Indicadores ----------
st.title('RadarPe · Noticias económicas por sector e impacto')
total, relevantes = len(en_fecha), res['id'].nunique()
c1, c2, c3, c4 = st.columns(4)
c1.metric('Noticias del periodo', total)
c2.metric('Noticias relevantes', relevantes)
c3.metric('Riesgos', res.loc[res['impacto'] == 'R', 'id'].nunique())
c4.metric('Lectura necesaria', f'{relevantes / total:.0%}' if total else '–')   # % del periodo que hay que leer

# ---------- Impacto por sector ----------
if not res.empty:
    tabla = pd.crosstab(res['sector'].map(SECTORES), res['impacto'].map(IMPACTO))
    st.subheader('Impacto por sector')
    st.bar_chart(tabla)

# ---------- Eventos (grupos del clustering) ----------
st.subheader('Eventos')
if res.empty:
    st.info('No hay noticias con estos filtros.')
eventos = res.groupby('grupo').agg(n=('id', 'nunique'), fecha=('fecha', 'min')).sort_values(['n', 'fecha'], ascending=[False, False])
for grupo in eventos.index:
    g = res[res['grupo'] == grupo].sort_values('fecha')
    principal = g.iloc[0]                                             # la noticia más antigua del grupo da el título
    medios = ', '.join(sorted(g['medio'].unique()))
    with st.expander(f"{principal['titulo']}  ·  {g['id'].nunique()} noticia(s)  ·  {medios}"):
        for _, n in g.drop_duplicates('id').iterrows():
            marcas = ', '.join(f"{s} ({IMPACTO[i]})" for s, i in g.loc[g['id'] == n['id'], ['sector', 'impacto']].values)
            st.markdown(f"**{n['fecha'].date()} · {n['medio']}** · [{n['titulo']}]({n['link']})  \n{marcas}")
