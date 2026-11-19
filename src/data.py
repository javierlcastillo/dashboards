from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

VENTAS_COLS = ["ticket_id", "fecha", "cliente_id", "estado", "region", "categoria",
               "promocion", "temporada", "monto", "unidades"]
CLIENTES_COLS = ["cliente_id"]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _leer(nombre: str) -> pd.DataFrame | None:
    for ext in (".csv", ".xlsx"):
        ruta = DATA_DIR / f"{nombre}{ext}"
        if ruta.exists():
            return pd.read_csv(ruta) if ext == ".csv" else pd.read_excel(ruta)
    return None


def _validar(df: pd.DataFrame, cols: list[str], nombre: str) -> None:
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        raise ValueError(f"A '{nombre}' le faltan columnas: {', '.join(faltan)}")


@st.cache_data(show_spinner="Cargando datos…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    ventas, clientes = _leer("ventas"), _leer("clientes")
    if ventas is None or clientes is None:  # primera ejecución: genera dummy
        from src.dummy import generar
        ventas, clientes = generar()

    _validar(ventas, VENTAS_COLS, "ventas")
    _validar(clientes, CLIENTES_COLS, "clientes")

    ventas = ventas.copy()
    ventas["fecha"] = pd.to_datetime(ventas["fecha"])
    ventas["cliente_id"] = ventas["cliente_id"].astype(str)
    clientes = clientes.copy()
    clientes["cliente_id"] = clientes["cliente_id"].astype(str)

    # Cliente nuevo = cliente que compró pero no existe en la tabla de clientes
    ventas["es_nuevo"] = ~ventas["cliente_id"].isin(set(clientes["cliente_id"]))
    ventas["anio"] = ventas["fecha"].dt.year
    ventas["mes"] = ventas["fecha"].dt.month
    ventas["mes_nombre"] = ventas["mes"].map(lambda m: MESES[m - 1])
    ventas["periodo"] = ventas["fecha"].dt.to_period("M").dt.to_timestamp()
    return ventas, clientes
