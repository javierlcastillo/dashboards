"""Filtros del sidebar, estado en session_state y chips de filtros activos."""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import streamlit as st

from src.data import MESES

TODOS = "Todos"


@dataclass
class Filtros:
    inicio: date
    fin: date
    meses: list[str] = field(default_factory=list)
    promocion: list[str] = field(default_factory=list)
    categoria: list[str] = field(default_factory=list)
    temporada: list[str] = field(default_factory=list)
    region: list[str] = field(default_factory=list)
    region_mapa: str | None = None
    monto: tuple[float, float] = (0.0, 0.0)
    monto_limites: tuple[float, float] = (0.0, 0.0)
    anio: str = TODOS


def _limites(ventas: pd.DataFrame):
    fmin, fmax = ventas["fecha"].min().date(), ventas["fecha"].max().date()
    mmin = float(int(ventas["monto"].min()))
    mmax = float(int(ventas["monto"].max()) + 1)
    return fmin, fmax, mmin, mmax


def _rango_anio(anio: str, fmin: date, fmax: date) -> tuple[date, date]:
    if anio == TODOS:
        return fmin, fmax
    y = int(anio)
    return max(date(y, 1, 1), fmin), min(date(y, 12, 31), fmax)


def _defaults(ventas: pd.DataFrame) -> dict:
    fmin, fmax, mmin, mmax = _limites(ventas)
    ultimo = str(ventas["anio"].max())
    return {
        "f_anio": ultimo,
        "f_fechas": _rango_anio(ultimo, fmin, fmax),
        "f_meses": [], "f_promocion": [], "f_categoria": [],
        "f_temporada": [], "f_region": [],
        "f_monto": (mmin, mmax),
        "region_mapa": None,
    }


def _init_state(ventas: pd.DataFrame) -> None:
    for k, v in _defaults(ventas).items():
        st.session_state.setdefault(k, v)
    st.session_state.setdefault("mapa_version", 0)


def limpiar(ventas: pd.DataFrame) -> None:
    for k, v in _defaults(ventas).items():
        st.session_state[k] = v
    st.session_state["mapa_version"] += 1  # fuerza a reiniciar la selección del mapa
    st.session_state.pop("_map_sig", None)


def quitar_region_mapa() -> None:
    st.session_state["region_mapa"] = None
    st.session_state["mapa_version"] += 1
    st.session_state.pop("_map_sig", None)


def sidebar(ventas: pd.DataFrame) -> Filtros:
    _init_state(ventas)
    fmin, fmax, mmin, mmax = _limites(ventas)

    def _on_anio():
        st.session_state["f_fechas"] = _rango_anio(st.session_state["f_anio"], fmin, fmax)

    sb = st.sidebar
    sb.header("Filtros")
    sb.button("Limpiar filtros", on_click=limpiar, args=(ventas,), icon=":material/filter_alt_off:",
              width="stretch")

    sb.subheader("Periodo")
    anios = [TODOS] + [str(a) for a in sorted(ventas["anio"].unique())]
    sb.selectbox("Año", anios, key="f_anio", on_change=_on_anio)
    sb.date_input("Rango de fechas", key="f_fechas", min_value=fmin, max_value=fmax, format="DD/MM/YYYY")
    sb.multiselect("Mes", MESES, key="f_meses", placeholder="Todos")

    sb.subheader("Segmentación")
    opts = lambda col: sorted(ventas[col].dropna().unique())  # noqa: E731
    sb.multiselect("Promoción", opts("promocion"), key="f_promocion", placeholder="Todas")
    sb.multiselect("Categoría", opts("categoria"), key="f_categoria", placeholder="Todas")
    sb.multiselect("Temporada", opts("temporada"), key="f_temporada", placeholder="Todas")
    sb.multiselect("Región", opts("region"), key="f_region", placeholder="Todas")
    sb.slider("Venta por transacción ($)", min_value=mmin, max_value=mmax, key="f_monto",
              step=1.0, format="$%d")

    fechas = st.session_state["f_fechas"]
    if isinstance(fechas, (tuple, list)):
        inicio = fechas[0] if len(fechas) > 0 else fmin
        fin = fechas[1] if len(fechas) > 1 else inicio  # rango a medio seleccionar
    else:
        inicio = fin = fechas

    return Filtros(
        inicio=inicio, fin=fin,
        meses=st.session_state["f_meses"],
        promocion=st.session_state["f_promocion"],
        categoria=st.session_state["f_categoria"],
        temporada=st.session_state["f_temporada"],
        region=st.session_state["f_region"],
        region_mapa=st.session_state["region_mapa"],
        monto=tuple(st.session_state["f_monto"]),
        monto_limites=(mmin, mmax),
        anio=st.session_state["f_anio"],
    )


def aplicar(ventas: pd.DataFrame, f: Filtros, *, fechas: bool = True,
            usar_region_mapa: bool = True, inicio: date | None = None, fin: date | None = None) -> pd.DataFrame:
    """Aplica los filtros. `fechas=False` omite el rango (útil para el periodo anterior)."""
    m = pd.Series(True, index=ventas.index)
    if fechas:
        ini, fi = inicio or f.inicio, fin or f.fin
        m &= ventas["fecha"].between(pd.Timestamp(ini), pd.Timestamp(fi))
    if f.meses:
        m &= ventas["mes_nombre"].isin(f.meses)
    for col, sel in (("promocion", f.promocion), ("categoria", f.categoria),
                     ("temporada", f.temporada), ("region", f.region)):
        if sel:
            m &= ventas[col].isin(sel)
    if usar_region_mapa and f.region_mapa:
        m &= ventas["region"] == f.region_mapa
    m &= ventas["monto"].between(*f.monto)
    return ventas[m]


def chips(f: Filtros, fmin: date, fmax: date) -> None:
    """Muestra los filtros activos como chips; la región del mapa se puede quitar."""
    items: list[str] = []
    if (f.inicio, f.fin) != (fmin, fmax):
        items.append(f"Fechas: {f.inicio:%d/%m/%Y} – {f.fin:%d/%m/%Y}")
    for nombre, sel in (("Mes", f.meses), ("Promoción", f.promocion), ("Categoría", f.categoria),
                        ("Temporada", f.temporada), ("Región", f.region)):
        if sel:
            items.append(f"{nombre}: {', '.join(sel)}")
    if f.monto != f.monto_limites:
        items.append(f"Venta: ${f.monto[0]:,.0f} – ${f.monto[1]:,.0f}")
    if f.region_mapa:
        items.append(f"Mapa: {f.region_mapa}")

    if not items:
        st.caption("Sin filtros activos · mostrando todos los datos")
        return

    html_chips = "".join(f'<span class="chip">{html.escape(t)}</span>' for t in items)
    c1, c2 = st.columns([6, 1], vertical_alignment="center")
    c1.markdown(f'<div class="chips">{html_chips}</div>', unsafe_allow_html=True)
    if f.region_mapa:
        c2.button(f"✕ Quitar {f.region_mapa}", on_click=quitar_region_mapa, width="stretch")
