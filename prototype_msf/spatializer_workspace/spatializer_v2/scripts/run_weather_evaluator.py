"""
run_weather_evaluator.py — Spatializer v0.2, MSFourrager

Corre el WeatherEvaluator sobre ocho ubicaciones reales de Quebec y compara
tres granularidades temporales, imprime tablas y escribe un CSV.

Un único modelo de scoring, con umbrales fundamentados en:

    Brassard, P., L. Mila Saavedra, J. St-Gelais et S. Godbout. 2026.
    "Développement des connaissances sur la fonction de l'agrométéorologie
    sur l'épandage du fumier et la réduction des émissions de GES."
    Rapport final IRDA et MAPAQ. 43 pages. Publié 28 janvier 2026.
    https://irda.qc.ca/media/5urgveg5/irda-meteoepandage-rapport-janvier2026.pdf

Comparación 3-way de granularidad temporal
------------------------------------------
Los tres modos usan **los mismos umbrales y las mismas funciones de scoring**.
Lo único que cambia es de qué ventana sale cada agregado:

===========  ==========  ==========  ==========  ==========  ==============
modo         temp_min    temp_max    wind_max    precip_sum  precip_max/h
===========  ==========  ==========  ==========  ==========  ==============
v4.0         24h         24h         24h         72h         72h
v4.1         6h-18h      6h-18h      6h-18h      72h         72h
v4.2         **24h**     6h-18h      6h-18h      72h         **24h**
===========  ==========  ==========  ==========  ==========  ==============

v4.0 y v4.1 se reproducen calculando sus agregados desde el mismo pronóstico
y pasándolos por ``WeatherInputs`` con overrides completos. Así el scoring es
literalmente el mismo código en los tres casos, y una sola llamada al API por
ubicación alimenta los tres modos.

Uso
---
    python spatializer_v2/scripts/run_weather_evaluator.py

Correr desde la raíz del repo, ``C:\\Proyectos\\terranimo-test``.
"""

import csv
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from spatializer_v2.evaluators.weather import (  # noqa: E402
    PRECIP_INTENSITY_WINDOW_HOURS,
    PRECIP_WINDOW_HOURS,
    VAR_HUMIDITY,
    VAR_PRECIPITATION,
    VAR_TEMPERATURE,
    VAR_WIND,
    WeatherEvaluator,
    WeatherInputs,
    filter_forecast_by_hour_window,
)
from weather_client import OpenMeteoClient, WeatherError  # noqa: E402

CSV_NAME = "weather_evaluator_2026-09-11_v42.csv"

HORIZON_HOURS = 24
APP_HOUR_START = 6
APP_HOUR_END = 18
WINDOW_LABEL = f"{APP_HOUR_START}h-{APP_HOUR_END}h"

MODES = ("v4.0", "v4.1", "v4.2")

LOCATIONS: List[Tuple[str, float, float]] = [
    ("Montreal", 45.5017, -73.5673),
    ("Sherbrooke", 45.4042, -71.8929),
    ("Trois-Rivieres", 46.3432, -72.5432),
    ("Gatineau", 45.4765, -75.7013),
    ("Saguenay", 48.3878, -71.0464),
    ("Rimouski", 48.4489, -68.5209),
    ("Val-d'Or", 48.0975, -77.7828),
    ("Sainte-Anne-de-Bellevue", 45.4059, -73.9430),
]


def _clean(values: Sequence[Any]) -> List[float]:
    return [v for v in values if v is not None]


def aggregates_for_mode(
    mode: str, raw: Dict[str, Sequence[Any]]
) -> Dict[str, float]:
    """
    Calcula los cinco agregados para un modo de granularidad temporal.

    Usa el mismo pronóstico crudo en los tres modos, así que cualquier
    diferencia viene de la ventana, nunca de los datos.
    """
    windowed = filter_forecast_by_hour_window(
        raw, APP_HOUR_START, APP_HOUR_END, HORIZON_HOURS
    )
    full_temps = _clean(raw[VAR_TEMPERATURE][:HORIZON_HOURS])
    full_winds = _clean(raw[VAR_WIND][:HORIZON_HOURS])
    win_temps = _clean(windowed[VAR_TEMPERATURE])
    win_winds = _clean(windowed[VAR_WIND])
    p72 = _clean(raw[VAR_PRECIPITATION][:PRECIP_WINDOW_HOURS])
    p24 = _clean(raw[VAR_PRECIPITATION][:PRECIP_INTENSITY_WINDOW_HOURS])

    if mode == "v4.0":
        return {
            "temp_min": min(full_temps), "temp_max": max(full_temps),
            "wind_max": max(full_winds), "precip_sum": sum(p72),
            "precip_max": max(p72),
        }
    if mode == "v4.1":
        return {
            "temp_min": min(win_temps), "temp_max": max(win_temps),
            "wind_max": max(win_winds), "precip_sum": sum(p72),
            "precip_max": max(p72),
        }
    # v4.2 — el fix
    return {
        "temp_min": min(full_temps), "temp_max": max(win_temps),
        "wind_max": max(win_winds), "precip_sum": sum(p72),
        "precip_max": max(p24),
    }


def main() -> int:
    client = OpenMeteoClient()
    evaluator = WeatherEvaluator(client)

    print("=" * 116)
    print("WEATHER EVALUATOR v4.2 — umbrales de Brassard et al. 2026 (IRDA-MAPAQ)")
    print(f"Horizonte: {HORIZON_HOURS}h  |  ventana aplicación: {WINDOW_LABEL}  "
          f"|  precip sum: {PRECIP_WINDOW_HOURS}h  "
          f"|  precip max/h: {PRECIP_INTENSITY_WINDOW_HOURS}h")
    print("=" * 116)

    print("\nPing Open-Meteo...")
    t0 = time.perf_counter()
    try:
        client.ping()
    except WeatherError as exc:
        print(f"  FAIL: {type(exc).__name__}: {exc}")
        return 1
    print(f"  OK ({time.perf_counter() - t0:.2f}s)")

    results: Dict[str, Dict[str, Any]] = {m: {} for m in MODES}
    failures: List[Tuple[str, str]] = []

    t_all = time.perf_counter()
    for label, lat, lon in LOCATIONS:
        try:
            fc = client.get_forecast(
                lat, lon, hours=max(HORIZON_HOURS, PRECIP_WINDOW_HOURS)
            )
        except WeatherError as exc:
            failures.append((label, f"{type(exc).__name__}: {exc}"))
            print(f"  {label}: FALLÓ — {exc}")
            continue

        raw: Dict[str, Sequence[Any]] = {"time": fc.times, **fc.values}
        for mode in MODES:
            agg = aggregates_for_mode(mode, raw)
            r = evaluator.evaluate(WeatherInputs(
                latitude=lat, longitude=lon, horizon_hours=HORIZON_HOURS,
                application_hour_start=APP_HOUR_START,
                application_hour_end=APP_HOUR_END,
                override_temp_min_c=agg["temp_min"],
                override_temp_max_c=agg["temp_max"],
                override_wind_max_ms=agg["wind_max"],
                override_precip_next_72h_mm=agg["precip_sum"],
                override_precip_max_hourly_mm=agg["precip_max"],
            ))
            results[mode][label] = (r, agg, fc)
    elapsed = time.perf_counter() - t_all

    # ------------------------------------------------- tabla principal v4.2
    print()
    print("-" * 116)
    print(
        f"{'Location':<26} {'TempMin':>8} {'TempMinWindow':>14} {'TempMax':>8} "
        f"{'WindMax':>8} {'P72h':>7} {'PmaxH':>6} {'PrecipMaxWindow':>16} "
        f"{'Score':>7} {'Verdict':>8}"
    )
    print("-" * 116)
    for label, _, _ in LOCATIONS:
        if label not in results["v4.2"]:
            continue
        r, agg, _ = results["v4.2"][label]
        print(
            f"{label:<26} {r.temp_min_c:>8.1f} {r.temp_min_window:>14} "
            f"{r.temp_max_c:>8.1f} {r.wind_max_ms:>8.2f} "
            f"{r.precip_next_72h_mm:>7.1f} {r.precip_max_hourly_mm:>6.1f} "
            f"{r.precip_max_hourly_window:>16} {r.score:>7.3f} {r.verdict:>8}"
        )
    print("-" * 116)
    print(f"{len(results['v4.2'])} ubicaciones en {elapsed:.2f}s "
          f"({len(results['v4.2'])} llamadas, {len(failures)} fallos)")

    # ------------------------------------------------------ tabla 3-way
    print()
    print("=" * 116)
    print("COMPARACIÓN 3-WAY de granularidad temporal")
    print("=" * 116)
    print(
        f"{'Location':<26} {'v4.0':>16} {'v4.1':>16} {'v4.2':>16} "
        f"{'Δ v4.1→v4.2':>12}  Cambios v4.1→v4.2"
    )
    print("-" * 116)
    changed_41_42 = 0
    changed_40_42 = 0
    for label, _, _ in LOCATIONS:
        if label not in results["v4.2"]:
            continue
        r40 = results["v4.0"][label][0]
        r41 = results["v4.1"][label][0]
        r42 = results["v4.2"][label][0]
        delta = r42.score - r41.score
        if r41.verdict != r42.verdict:
            changed_41_42 += 1
            note = f"{r41.verdict} → {r42.verdict}"
        else:
            note = "sin cambio"
        if r40.verdict != r42.verdict:
            changed_40_42 += 1
        print(
            f"{label:<26} {r40.score:>8.3f} {r40.verdict:>7} "
            f"{r41.score:>8.3f} {r41.verdict:>7} "
            f"{r42.score:>8.3f} {r42.verdict:>7} "
            f"{delta:>+12.3f}  {note}"
        )
    print("-" * 116)
    print(f"Cambios de verdict v4.1 → v4.2: {changed_41_42}/{len(results['v4.2'])}")
    print(f"Cambios de verdict v4.0 → v4.2: {changed_40_42}/{len(results['v4.2'])}")

    # ----------------------------------------- de dónde vino la diferencia
    print()
    print("Agregados por modo (donde difieren):")
    for label, _, _ in LOCATIONS:
        if label not in results["v4.2"]:
            continue
        a41 = results["v4.1"][label][1]
        a42 = results["v4.2"][label][1]
        diffs = [
            f"{k}: {a41[k]:.2f}→{a42[k]:.2f}"
            for k in a41
            if abs(a41[k] - a42[k]) > 1e-9
        ]
        print(f"  {label:<26} {', '.join(diffs) if diffs else '(idénticos)'}")

    for label, err in failures:
        print(f"  FALLO  {label}: {err}")

    # --------------------------------------------------------------- csv
    rows: List[Dict[str, Any]] = []
    for mode in MODES:
        for label, lat, lon in LOCATIONS:
            if label not in results[mode]:
                continue
            r, agg, fc = results[mode][label]
            rows.append({
                "mode": mode,
                "location": label,
                "latitude_requested": lat,
                "longitude_requested": lon,
                "latitude_served": fc.latitude,
                "longitude_served": fc.longitude,
                "timezone": fc.timezone,
                "first_timestamp": fc.times[0] if fc.times else None,
                "horizon_hours": HORIZON_HOURS,
                "application_window": WINDOW_LABEL,
                "temp_min_c": round(r.temp_min_c, 3),
                "temp_min_window": "24h" if mode != "v4.1" else WINDOW_LABEL,
                "temp_max_c": round(r.temp_max_c, 3),
                "temp_max_window": "24h" if mode == "v4.0" else WINDOW_LABEL,
                "wind_max_ms": round(r.wind_max_ms, 3),
                "wind_window": "24h" if mode == "v4.0" else WINDOW_LABEL,
                "precip_next_72h_mm": round(r.precip_next_72h_mm, 3),
                "precip_sum_window": "72h",
                "precip_max_hourly_mm": round(r.precip_max_hourly_mm, 3),
                "precip_max_hourly_window": "24h" if mode == "v4.2" else "72h",
                "sub_temperature": round(r.sub_scores["temperature"], 6),
                "sub_wind": round(r.sub_scores["wind"], 6),
                "sub_precipitation": round(r.sub_scores["precipitation"], 6),
                "score": round(r.score, 6),
                "verdict": r.verdict,
                "n_stops": len(r.stops_triggered),
                "stops_triggered": " | ".join(r.stops_triggered),
                "recommended_time_window": r.recommended_time_window,
            })

    if rows:
        out = Path(__file__).resolve().parent / CSV_NAME
        fieldnames = list(rows[0].keys())
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print()
        print(f"CSV escrito: {out}  ({len(rows)} filas, {len(fieldnames)} columnas)")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
