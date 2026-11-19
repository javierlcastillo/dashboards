"""Dashboard de ventas
"""
from __future__ import annotations

import streamlit as st
from dateutil.relativedelta import relativedelta

from src import charts, filters, metrics
from src.data import load_data
from src.geo import REGION_POR_CLAVE

st.set_page_config(page_title="Dashboard de ventas", page_icon=":bar_chart:", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2rem;}
      [data-testid="stMetricValue"] {font-size: 2.1rem; font-weight: 600;}
      [data-testid="stMetricLabel"] p {font-size: 0.95rem;}
      .chips {display: flex; flex-wrap: wrap; gap: 6px;}
      .chip {background: rgba(78,121,167,0.14); color: inherit; border: 1px solid rgba(78,121,167,0.35);
             border-radius: 999px; padding: 2px 10px; font-size: 0.82rem; white-space: nowrap;}
      h3 {font-weight: 500 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}

ventas, clientes = load_data()
f = filters.sidebar(ventas)
fmin, fmax = ventas["fecha"].min().date(), ventas["fecha"].max().date()

df = filters.aplicar(ventas, f)
df_mapa = filters.aplicar(ventas, f, usar_region_mapa=False)  # el mapa muestra todas las regiones

# Periodo anterior (misma duración, mismos filtros salvo fechas)
p_ini, p_fin = metrics.periodo_anterior(f.inicio, f.fin)
df_prev = filters.aplicar(ventas, f, inicio=p_ini, fin=p_fin) if p_fin >= fmin else df.iloc[0:0]

k = metrics.calcular(df)
kp = metrics.calcular(df_prev)

# INDEX: ------------------------------------------------------------------ encabezado + KPIs
st.title("Dashboard de ventas")

c1, c2, c3, c4 = st.columns(4)
if k is None:
    for c, lbl in zip((c1, c2, c3, c4), ("Ticket promedio ($ por compra)", "Ventas totales ($)",
                                         "Productos por compra (unidades)", "Clientes nuevos (#)")):
        c.metric(lbl, "—", border=True)
else:
    ayuda = (f"Comparado con {p_ini:%d/%m/%Y} – {p_fin:%d/%m/%Y}" if kp
             else "Sin datos del periodo anterior para comparar")
    c1.metric("Ticket promedio ($ por compra)", f"${k.ticket_promedio:,.1f}",
              metrics.delta_pct(k.ticket_promedio, kp and kp.ticket_promedio), border=True, help=ayuda)
    c2.metric("Ventas totales ($)", f"${k.ventas_totales:,.0f}",
              metrics.delta_pct(k.ventas_totales, kp and kp.ventas_totales), border=True, help=ayuda)
    c3.metric("Productos por compra (unidades)", f"{k.productos_por_compra:,.2f}",
              metrics.delta_pct(k.productos_por_compra, kp and kp.productos_por_compra), border=True, help=ayuda)
    c4.metric("Clientes nuevos (#)", f"{k.clientes_nuevos:,}",
              metrics.delta_pct(k.clientes_nuevos, kp and kp.clientes_nuevos), border=True,
              help="Clientes que compraron y no existen en la tabla de clientes. " + ayuda)

filters.chips(f, fmin, fmax)

if df_mapa.empty:
    st.info("No hay ventas con los filtros seleccionados. Ajusta o limpia los filtros.", icon=":material/search_off:")
    st.stop()

# INDEX: ------------------------------------------------------------------ fila 2: mapa + categoría
col_mapa, col_cat = st.columns([3, 2], gap="large")

with col_mapa:
    st.subheader("Ventas por región ($)")
    st.caption("Haz clic en un estado para filtrar el dashboard por su región.")
    key = f"mapa_{st.session_state['mapa_version']}"
    evento = st.plotly_chart(charts.mapa_regiones(df_mapa, f.region_mapa), key=key, on_select="rerun",
                             selection_mode="points", config=PLOTLY_CFG, width="stretch")
    puntos = (evento or {}).get("selection", {}).get("points", []) if evento else []
    claves = tuple(sorted(p.get("location") for p in puntos if p.get("location")))
    # solo reaccionamos a selecciones nuevas; para quitarla se usa el chip / "Limpiar filtros"
    if claves and claves != st.session_state.get("_map_sig"):
        st.session_state["_map_sig"] = claves
        nueva = REGION_POR_CLAVE.get(claves[-1])
        if nueva and nueva != st.session_state.get("region_mapa"):
            st.session_state["region_mapa"] = nueva
            st.rerun()

if df.empty:
    st.info("No hay ventas para la región seleccionada con estos filtros.", icon=":material/search_off:")
    st.stop()

with col_cat:
    st.subheader("Ventas por categoría")
    st.plotly_chart(charts.ventas_categoria(df), config=PLOTLY_CFG, width="stretch")

# INDEX: ------------------------------------------------------------------ fila 3
a, b, c = st.columns(3, gap="large")
with a:
    st.subheader("Clientes nuevos por temporada")
    if df["es_nuevo"].any():
        st.plotly_chart(charts.clientes_nuevos(df), config=PLOTLY_CFG, width="stretch")
    else:
        st.caption("No hay clientes nuevos en este periodo.")
with b:
    st.subheader("Ticket promedio: con y sin descuento")
    st.plotly_chart(charts.ticket_promocion(df, k.ticket_promedio), config=PLOTLY_CFG, width="stretch")
with c:
    st.subheader("Ventas por mes vs año anterior")
    ini_ant = f.inicio - relativedelta(years=1)
    fin_ant = f.fin - relativedelta(years=1)
    df_anio_ant = filters.aplicar(ventas, f, inicio=ini_ant, fin=fin_ant)
    st.plotly_chart(charts.ventas_vs_anio_anterior(df, df_anio_ant), config=PLOTLY_CFG, width="stretch")
