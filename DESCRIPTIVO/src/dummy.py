"""Generador de datos dummy: data/ventas.csv y data/clientes.csv.

Uso:  python -m src.dummy
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.geo import ESTADOS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

INICIO = date(2025, 1, 1)
FIN = date(2026, 11, 19)
N_CLIENTES_REGISTRADOS = 2600
N_CLIENTES_NUEVOS = 450  # clientes que compran pero NO están en la tabla de clientes
N_TICKETS = 12000

CATEGORIAS = {  # categoría: (peso, monto base)
    "Calzado": (0.38, 360.0),
    "Casual": (0.26, 300.0),
    "Fitness": (0.20, 290.0),
    "Accesorios": (0.16, 230.0),
}
PESO_REGION = {"Centro": 0.38, "Occidente": 0.20, "Norte": 0.18, "Noroeste": 0.12, "Sureste": 0.12}
ESTACIONALIDAD = {1: 0.85, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.0,
                  7: 1.05, 8: 0.95, 9: 0.95, 10: 1.0, 11: 1.2, 12: 1.35}


def temporada(d: pd.Timestamp) -> str:
    md = (d.month, d.day)
    if (3, 21) <= md < (6, 21):
        return "Primavera"
    if (6, 21) <= md < (9, 23):
        return "Verano"
    if (9, 23) <= md < (12, 21):
        return "Otoño"
    return "Invierno"


def generar(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dias = pd.date_range(INICIO, FIN, freq="D")

    # --- clientes registrados ---
    reg_ids = [f"C{i:05d}" for i in range(1, N_CLIENTES_REGISTRADOS + 1)]
    clientes = pd.DataFrame({
        "cliente_id": reg_ids,
        "nombre": [f"Cliente {i}" for i in range(1, N_CLIENTES_REGISTRADOS + 1)],
        "fecha_alta": rng.choice(pd.date_range("2022-01-01", "2024-12-31"), N_CLIENTES_REGISTRADOS),
    })

    # --- fechas con estacionalidad ---
    w = np.array([ESTACIONALIDAD[d.month] for d in dias])
    w /= w.sum()

    # tickets de clientes registrados
    n_nuevos_tickets = int(N_TICKETS * 0.09)
    n_reg = N_TICKETS - n_nuevos_tickets
    fechas_reg = rng.choice(dias, n_reg, p=w)
    clientes_reg = rng.choice(reg_ids, n_reg)

    # tickets de clientes nuevos: cada uno compra a partir de su "primera fecha"
    nuevo_ids = [f"N{i:05d}" for i in range(1, N_CLIENTES_NUEVOS + 1)]
    primera = rng.choice(dias, N_CLIENTES_NUEVOS, p=w)
    idx = rng.integers(0, N_CLIENTES_NUEVOS, n_nuevos_tickets)
    offset = pd.to_timedelta(rng.integers(0, 90, n_nuevos_tickets), unit="D")
    fechas_nue = np.minimum(pd.DatetimeIndex(primera[idx]) + offset, pd.Timestamp(FIN))
    clientes_nue = np.array(nuevo_ids)[idx]
    # garantizar que cada cliente nuevo tenga su primera compra
    fechas_nue = np.concatenate([pd.DatetimeIndex(primera).values, pd.DatetimeIndex(fechas_nue).values])
    clientes_nue = np.concatenate([nuevo_ids, clientes_nue])

    fechas = pd.to_datetime(np.concatenate([fechas_reg, fechas_nue]))
    cli = np.concatenate([clientes_reg, clientes_nue])
    n = len(fechas)

    # --- geografía ---
    regiones = list(PESO_REGION)
    region = rng.choice(regiones, n, p=list(PESO_REGION.values()))
    estados_por_region = {r: [nom for nom, reg in ESTADOS.values() if reg == r] for r in regiones}
    estado = np.array([rng.choice(estados_por_region[r]) for r in region])

    # --- producto / promoción / montos ---
    cats = list(CATEGORIAS)
    categoria = rng.choice(cats, n, p=[c[0] for c in CATEGORIAS.values()])
    promo = rng.random(n) < 0.42
    unidades = np.clip(rng.poisson(3.3, n) + 1, 1, 12)
    base = np.array([CATEGORIAS[c][1] for c in categoria])
    estac = np.array([ESTACIONALIDAD[m] for m in fechas.month])
    monto = base * rng.lognormal(0, 0.35, n) * (0.88 + unidades * 0.03) * (0.6 + 0.4 * estac)
    monto = np.where(promo, monto * 0.8, monto).round(2)

    ventas = pd.DataFrame({
        "fecha": fechas.normalize(),
        "cliente_id": cli,
        "estado": estado,
        "region": region,
        "categoria": categoria,
        "promocion": np.where(promo, "Con descuento", "Sin descuento"),
        "monto": monto,
        "unidades": unidades,
    }).sort_values("fecha", kind="stable").reset_index(drop=True)
    ventas.insert(0, "ticket_id", [f"T{i:06d}" for i in range(1, len(ventas) + 1)])
    ventas["temporada"] = ventas["fecha"].map(temporada)
    return ventas, clientes


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    ventas, clientes = generar()
    ventas.to_csv(DATA_DIR / "ventas.csv", index=False, date_format="%Y-%m-%d")
    clientes.to_csv(DATA_DIR / "clientes.csv", index=False, date_format="%Y-%m-%d")
    print(f"ventas: {len(ventas):,} filas | clientes: {len(clientes):,} filas -> {DATA_DIR}")


if __name__ == "__main__":
    main()
