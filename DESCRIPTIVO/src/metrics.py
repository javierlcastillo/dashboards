"""KPIs y comparativo contra el periodo anterior."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd


@dataclass
class KPIs:
    ticket_promedio: float
    ventas_totales: float
    productos_por_compra: float
    clientes_nuevos: int
    tickets: int


def calcular(df: pd.DataFrame) -> KPIs | None:
    if df.empty:
        return None
    tickets = df["ticket_id"].nunique()
    ventas = float(df["monto"].sum())
    return KPIs(
        ticket_promedio=ventas / tickets,
        ventas_totales=ventas,
        productos_por_compra=float(df["unidades"].sum()) / tickets,
        clientes_nuevos=int(df.loc[df["es_nuevo"], "cliente_id"].nunique()),
        tickets=tickets,
    )


def periodo_anterior(inicio: date, fin: date) -> tuple[date, date]:
    """Ventana inmediata anterior con la misma duración."""
    dur = (fin - inicio).days + 1
    return inicio - timedelta(days=dur), inicio - timedelta(days=1)


def delta_pct(actual: float, previo: float | None) -> str | None:
    if previo is None or previo == 0:
        return None
    return f"{(actual - previo) / previo:+.1%}"
