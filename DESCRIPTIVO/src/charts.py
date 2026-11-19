"""Figuras de Plotly para cada visual del dashboard."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data import MESES_CORTOS
from src.geo import CLAVE_POR_ESTADO, ESTADOS, load_geojson

AZUL, NARANJA = "#4E79A7", "#F28E2B"
COLOR_PROMO = {"Con descuento": AZUL, "Sin descuento": NARANJA}
COLOR_TEMPORADA = {"Invierno": "#4E79A7", "Otoño": "#F28E2B", "Primavera": "#E15759", "Verano": "#76B7B2"}
ORDEN_TEMPORADA = ["Invierno", "Primavera", "Verano", "Otoño"]
GRIS = "#8A8F98"
FONT = dict(family="Inter, Segoe UI, sans-serif", size=12)


def _base(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10), font=FONT,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    return fig


def _etiquetas_mes(periodos: pd.Series) -> dict:
    """Etiquetas en español; agrega el año si el rango cruza años."""
    varios = periodos.dt.year.nunique() > 1
    return {p: f"{MESES_CORTOS[p.month - 1]}{' ' + str(p.year)[2:] if varios else ''}" for p in periodos}


def _eje_meses(fig: go.Figure, periodos: pd.Series) -> None:
    p = pd.Series(sorted(periodos.unique()))
    etiquetas = _etiquetas_mes(p)
    fig.update_xaxes(tickmode="array", tickvals=list(p), ticktext=[etiquetas[x] for x in p], title_text="")


def _linea_promedio(fig: go.Figure, valor: float, texto: str) -> None:
    fig.add_hline(y=valor, line_dash="dot", line_color=GRIS, line_width=1.5,
                  annotation_text=texto, annotation_position="top left",
                  annotation_font=dict(color=GRIS, size=11), annotation_bgcolor="rgba(255,255,255,0.8)")


# INDEX: ---------------------------------------------------------------- mapa
def mapa_regiones(df: pd.DataFrame, region_sel: str | None) -> go.Figure:
    por_region = df.groupby("region").agg(ventas=("monto", "sum"), tickets=("ticket_id", "nunique"))
    por_region["ticket"] = por_region["ventas"] / por_region["tickets"]

    estados = pd.DataFrame(
        [(clave, nombre, region) for clave, (nombre, region) in ESTADOS.items()],
        columns=["clave", "estado", "region"],
    ).merge(por_region, left_on="region", right_index=True, how="inner")

    fig = px.choropleth(
        estados, geojson=load_geojson(), featureidkey="properties.id", locations="clave",
        color="ventas", color_continuous_scale=["#C6DBEF", "#6BAED6", "#2171B5", "#08306B"],
        custom_data=["region", "estado", "ventas", "ticket"],
    )
    fig.update_traces(
        marker_line_color="white", marker_line_width=0.6,
        hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                      "Ventas región: $%{customdata[2]:,.0f}<br>"
                      "Ticket promedio: $%{customdata[3]:,.1f}<extra></extra>",
    )
    if region_sel:  # resalta la región elegida: capa gris sobre las demás (siguen siendo clicables)
        otros = estados[estados["region"] != region_sel]
        fig.add_trace(go.Choropleth(
            geojson=load_geojson(), featureidkey="properties.id", locations=otros["clave"],
            z=[0] * len(otros), showscale=False,
            colorscale=[[0, "rgba(215,215,215,0.8)"], [1, "rgba(215,215,215,0.8)"]],
            marker_line_color="white", marker_line_width=0.6,
            customdata=otros[["region", "estado", "ventas", "ticket"]].values,
            hovertemplate=fig.data[0].hovertemplate,
        ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        clickmode="event+select", dragmode=False,
        coloraxis_colorbar=dict(title="Ventas ($)", tickprefix="$", tickformat="~s",
                                thickness=10, len=0.6, x=0.98),
    )
    return _base(fig, height=380)


# INDEX: ---------------------------------------------------------------- categoría
def ventas_categoria(df: pd.DataFrame) -> go.Figure:
    g = df.groupby(["categoria", "promocion"], as_index=False)["monto"].sum()
    orden = g.groupby("categoria")["monto"].sum().sort_values().index.tolist()
    fig = px.bar(
        g, y="categoria", x="monto", color="promocion", orientation="h",
        color_discrete_map=COLOR_PROMO, category_orders={"categoria": orden[::-1],
                                                        "promocion": list(COLOR_PROMO)},
        custom_data=["promocion"],
    )
    fig.update_traces(hovertemplate="<b>%{y}</b> · %{customdata[0]}<br>$%{x:,.0f}<extra></extra>")
    fig.update_xaxes(title_text="Venta ($)", tickprefix="$", tickformat="~s",
                     gridcolor="rgba(128,128,128,0.18)", showgrid=True)
    fig.update_yaxes(title_text="", showgrid=False)
    fig.update_layout(bargap=0.35)
    return _base(fig, height=380)


# INDEX: ---------------------------------------------------------------- clientes nuevos
def clientes_nuevos(df: pd.DataFrame) -> go.Figure:
    nuevos = df[df["es_nuevo"]].sort_values("fecha").drop_duplicates("cliente_id")  # primera compra
    g = nuevos.groupby(["periodo", "temporada"], as_index=False)["cliente_id"].nunique()
    g = g.rename(columns={"cliente_id": "clientes"})
    tot = g.groupby("temporada")["clientes"].sum()
    g["temporada_lbl"] = g["temporada"].map(lambda t: f"{t} ({tot[t]})")
    mapa_color = {f"{t} ({tot[t]})": c for t, c in COLOR_TEMPORADA.items() if t in tot}
    orden = [f"{t} ({tot[t]})" for t in ORDEN_TEMPORADA if t in tot]

    fig = px.bar(g, x="periodo", y="clientes", color="temporada_lbl",
                 color_discrete_map=mapa_color, category_orders={"temporada_lbl": orden},
                 custom_data=["temporada"])
    fig.update_traces(hovertemplate="%{customdata[0]}<br>%{y} clientes nuevos<extra></extra>")
    _eje_meses(fig, g["periodo"])
    fig.update_yaxes(title_text="Clientes nuevos")
    fig.update_layout(bargap=0.2, barmode="stack")
    return _base(fig)


# INDEX: ---------------------------------------------------------------- ticket promedio
def ticket_promocion(df: pd.DataFrame, ticket_global: float) -> go.Figure:
    g = df.groupby(["periodo", "promocion"]).agg(v=("monto", "sum"), t=("ticket_id", "nunique")).reset_index()
    g["ticket"] = g["v"] / g["t"]
    fig = px.line(g, x="periodo", y="ticket", color="promocion", markers=True,
                  color_discrete_map=COLOR_PROMO, category_orders={"promocion": list(COLOR_PROMO)},
                  custom_data=["promocion"])
    fig.update_traces(line_width=2.5, marker_size=5,
                      hovertemplate="%{customdata[0]}<br>$%{y:,.1f}<extra></extra>")
    _linea_promedio(fig, ticket_global, f"Promedio ${ticket_global:,.0f}")
    _eje_meses(fig, g["periodo"])
    # Eje ajustado a los datos (no desde $0) para que la diferencia entre líneas se aprecie
    lo = min(g["ticket"].min(), ticket_global)
    hi = max(g["ticket"].max(), ticket_global)
    pad = max((hi - lo) * 0.12, 5)
    fig.update_yaxes(title_text="Ticket promedio ($)", tickprefix="$", range=[lo - pad, hi + pad], nticks=6)
    return _base(fig)


# INDEX: ---------------------------------------------------------------- ventas vs año anterior
def ventas_vs_anio_anterior(df: pd.DataFrame, df_anterior: pd.DataFrame) -> go.Figure:
    """`df_anterior` = mismas condiciones pero un año antes; se alinea sumando 1 año."""
    act = df.groupby("periodo")["monto"].sum().rename("actual")
    ant = df_anterior.groupby("periodo")["monto"].sum()
    ant.index = ant.index + pd.DateOffset(years=1)
    g = pd.concat([act, ant.rename("anterior")], axis=1).reindex(act.index).reset_index()
    g["var"] = (g["actual"] / g["anterior"] - 1).where(g["anterior"] > 0)

    fig = go.Figure()
    if g["anterior"].notna().any():
        fig.add_trace(go.Scatter(
            x=g["periodo"], y=g["anterior"], name="Año anterior", mode="lines",
            line=dict(color=GRIS, width=2, dash="dash"),
            hovertemplate="Año anterior: $%{y:,.0f}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=g["periodo"], y=g["actual"], name="Periodo actual", mode="lines+markers",
        line=dict(color=AZUL, width=2.5), marker_size=5, customdata=g["var"],
        hovertemplate="Actual: $%{y:,.0f}<br>vs año anterior: %{customdata:+.1%}<extra></extra>",
    ))
    _eje_meses(fig, g["periodo"])
    fig.update_yaxes(title_text="Ventas ($)", tickprefix="$", tickformat="~s")
    fig.update_layout(hovermode="x unified")
    return _base(fig)
