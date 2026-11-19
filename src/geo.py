"""Geografía: mapeo estado -> región y carga del GeoJSON de México."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "mexico_states.geojson"

# Clave ISO 3166-2 (la que trae el GeoJSON en properties.id) -> (nombre, región)
ESTADOS: dict[str, tuple[str, str]] = {
    # Noroeste
    "MX-BCN": ("Baja California", "Noroeste"),
    "MX-BCS": ("Baja California Sur", "Noroeste"),
    "MX-SON": ("Sonora", "Noroeste"),
    "MX-SIN": ("Sinaloa", "Noroeste"),
    "MX-CHH": ("Chihuahua", "Noroeste"),
    "MX-DUR": ("Durango", "Noroeste"),
    # Norte
    "MX-COA": ("Coahuila", "Norte"),
    "MX-NLE": ("Nuevo León", "Norte"),
    "MX-TAM": ("Tamaulipas", "Norte"),
    "MX-ZAC": ("Zacatecas", "Norte"),
    "MX-SLP": ("San Luis Potosí", "Norte"),
    # Occidente
    "MX-JAL": ("Jalisco", "Occidente"),
    "MX-NAY": ("Nayarit", "Occidente"),
    "MX-COL": ("Colima", "Occidente"),
    "MX-MIC": ("Michoacán", "Occidente"),
    "MX-AGU": ("Aguascalientes", "Occidente"),
    "MX-GUA": ("Guanajuato", "Occidente"),
    # Centro
    "MX-CMX": ("Ciudad de México", "Centro"),
    "MX-MEX": ("México", "Centro"),
    "MX-MOR": ("Morelos", "Centro"),
    "MX-PUE": ("Puebla", "Centro"),
    "MX-TLA": ("Tlaxcala", "Centro"),
    "MX-HID": ("Hidalgo", "Centro"),
    "MX-QUE": ("Querétaro", "Centro"),
    "MX-GRO": ("Guerrero", "Centro"),
    # Sureste
    "MX-VER": ("Veracruz", "Sureste"),
    "MX-OAX": ("Oaxaca", "Sureste"),
    "MX-CHP": ("Chiapas", "Sureste"),
    "MX-TAB": ("Tabasco", "Sureste"),
    "MX-CAM": ("Campeche", "Sureste"),
    "MX-YUC": ("Yucatán", "Sureste"),
    "MX-ROO": ("Quintana Roo", "Sureste"),
}

REGIONES = ["Centro", "Noroeste", "Norte", "Occidente", "Sureste"]
REGION_POR_ESTADO = {nombre: region for nombre, region in ESTADOS.values()}
CLAVE_POR_ESTADO = {nombre: clave for clave, (nombre, _) in ESTADOS.items()}
REGION_POR_CLAVE = {clave: region for clave, (_, region) in ESTADOS.items()}


@lru_cache(maxsize=1)
def load_geojson() -> dict:
    with open(GEOJSON_PATH, encoding="utf-8") as fh:
        return json.load(fh)
