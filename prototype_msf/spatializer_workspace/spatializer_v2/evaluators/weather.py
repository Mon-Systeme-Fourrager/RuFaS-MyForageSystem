"""
Weather Evaluator para Spatializer v0.2 - MSFourrager.

FUNDAMENTO CIENTÍFICO:
======================

Todos los umbrales, sub-criterios y lógica de scoring de este evaluator
están fundamentados en:

Brassard, P., L. Mila Saavedra, J. St-Gelais et S. Godbout. 2026.
"Développement des connaissances sur la fonction de l'agrométéorologie
sur l'épandage du fumier et la réduction des émissions de GES."
Rapport final IRDA et MAPAQ. 43 pages. Publié 28 janvier 2026.
URL: https://irda.qc.ca/media/5urgveg5/irda-meteoepandage-rapport-janvier2026.pdf

Este paper del IRDA (Institut de Recherche et de Développement en
Agroenvironnement) en colaboración con el MAPAQ (Ministère de l'Agriculture,
des Pêcheries et de l'Alimentation du Québec) hace la revisión completa de
literatura científica sobre el impacto de las condiciones meteorológicas
en las pérdidas de N (volatilización de NH3, denitrificación N2O) y P
(runoff, erosión, lessivage) durante el épandage en el contexto de Quebec.

FUENTES PRIMARIAS COMPILADAS EN BRASSARD ET AL. 2026:
- Temperatura: Brassard et al. 2024, Huijsmans 2003, Svensson 1994, Pedersen 2021
- Viento: Sommer et al. 1991, Huijsmans 2001, Thompson et al. 1990
- Precipitación: ALFAM2 (Hafner et al. 2019), Sharpe 2004, Chambers 2000
- Timing horario: Gordon et al. 2000, Sommer & Olesen 2000, Moal et al. 1995

SUB-CRITERIOS DEL EVALUATOR:
1. Temperatura (min/max sobre horizonte): freeze stop, 25°C stop, escala continua
2. Viento (max sobre horizonte): stops y escala continua fundamentada
3. Precipitación (sum 72h + max hourly): stops por erosión, zona óptima 2-10mm

AGREGACIÓN: Geometric mean (Adamchuk 2011).

NOTA: humedad relativa NO es sub-criterio independiente. Según Huijsmans 2001
citado en Brassard et al. 2026, humedad actúa como factor de compensación
(+25% humedad puede compensar +2 m/s viento), no como criterio principal.
Se incluye en el output solo como información contextual.

MODELO ALFAM2:
El paper describe el modelo ALFAM2 (Ammonia Volatilization from Field-Applied
Manure v2, Hafner et al. 2019) como el estándar internacional validado con
1,895 parcelas experimentales. IRDA-MAPAQ lo usan como base para su OAD
oficial. Nuestro evaluator NO wrapea ALFAM2 (evitando dependencias R/Excel),
sino que aplica los umbrales derivados de su base de datos y de la literatura
compilada en Brassard et al. 2026.

HISTORIAL:
Esta versión (2026-09-11) reemplaza el enfoque anterior de tres propuestas de
scoring no calibradas (strict / moderate / continuous), cuyos umbrales eran
PROPOSAL sin fuente. La humedad relativa dejó de ser sub-criterio, y el
viento — omisión crítica de aquella versión — pasó a serlo.

GRANULARIDAD TEMPORAL (v4.2):
=============================

Diferentes sub-criterios usan diferentes agregaciones temporales según
lo que operacionalmente importa:

1. Ventana horaria de aplicación (application_hour_start/end, default 6h-18h):
   - temp_max: pico térmico durante épandage
   - wind_max: viento durante épandage
   - humidity_max: humedad durante épandage (solo info)

   Rationale: Sommer & Olesen 2000, Gordon et al. 2000, Moal et al. 1995
   citados en Brassard et al. 2026 — épandage soirée/tôt matin reduce
   volatilización 28-56%.

2. 24 horas completas:
   - temp_min: para freeze stop
   - precip_max_hourly: para stop de erosión

   Rationale:
   - Helada nocturna congela suelo que sigue helado en horas de aplicación.
   - Intensidad erosiva importa durante y justo después del épandage,
     no 3 días después.

3. 72 horas completas:
   - precip_next_72h_mm: suma para stop acumulado
   - precip_next_72h_mm: para score continuo

   Rationale: Chambers 2000 (citado en Brassard 2026): acumulado post-
   aplicación causa runoff y erosión hasta varios días después.

La ventana horaria es parametrizable via application_hour_start y
application_hour_end en WeatherInputs. Slava/Maxime pueden ajustar
sin recodear.

CAMBIOS EN v4.2:
- Fix B: freeze stop ahora sobre 24h completas (era: ventana horaria)
- Fix C: precip_max_hourly ahora sobre 24h (era: 72h)

CAMBIOS EN v4.1:
- Los agregados de temperatura, viento y humedad pasaron de 24 h completas
  a la ventana horaria de aplicación.

UNIDADES:
Open-Meteo devuelve ``wind_speed_10m`` en km/h por defecto. El cliente envía
``wind_speed_unit=ms`` en cada petición para que llegue en m/s, que es la
unidad de los umbrales de Brassard et al. 2026. Ver
``weather_client.config.WIND_SPEED_UNIT``.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from weather_client import OpenMeteoClient
from weather_client.models import ForecastResult

from .base import EvaluationResult

logger = logging.getLogger(__name__)

# ============================================================
# Variables Open-Meteo usadas
# ============================================================

VAR_TEMPERATURE = "temperature_2m"          # [°C]
VAR_WIND = "wind_speed_10m"                 # [m/s] — requiere wind_speed_unit=ms
VAR_PRECIPITATION = "precipitation"         # [mm]
VAR_HUMIDITY = "relative_humidity_2m"       # [%] — solo contexto

#: Ventana fija de precipitación, en horas. Los umbrales de Chambers 2000 y
#: la zona óptima de ALFAM2 están expresados sobre 72 h, independientemente
#: del horizonte que el caller pida para temperatura y viento.
PRECIP_WINDOW_HOURS: int = 72

#: Ventana horaria de aplicación por defecto (hora local del sitio).
#: 6 h = tôt matin (Sommer & Olesen 2000), 18 h = soirée (Gordon et al. 2000).
DEFAULT_APPLICATION_HOUR_START: int = 6
DEFAULT_APPLICATION_HOUR_END: int = 18

#: Ventana, en horas, sobre la que se busca la intensidad horaria máxima de
#: precipitación para el stop de erosión de Chambers 2000 (Fix C, v4.2).
#: La intensidad erosiva importa durante y justo después del épandage: un
#: chubasco en la hora 70 no debe bloquear la aplicación de hoy.
PRECIP_INTENSITY_WINDOW_HOURS: int = 24

# ============================================================
# Umbrales — Brassard et al. 2026 (IRDA-MAPAQ)
# ============================================================

# --- Temperatura, sección 3.6.2.3
TEMP_FREEZE_STOP_C: float = 0.0       # Brassard et al. 2026
TEMP_HIGH_STOP_C: float = 25.0        # Brassard et al. 2024
TEMP_NO_EFFECT_MAX_C: float = 14.0    # Pedersen 2021
TEMP_MID_C: float = 20.0              # Huijsmans 2003

# --- Viento, sección 3.6.2.3
WIND_NO_EFFECT_MAX_MS: float = 2.5    # Sommer et al. 1991
WIND_PLATEAU_MAX_MS: float = 4.0      # Sommer et al. 1991
WIND_STOP_MS: float = 8.0             # seguridad operacional

# --- Precipitación, secciones 3.6.2.3 y 3.7.1
PRECIP_HOURLY_STOP_MM: float = 4.0    # Chambers 2000
PRECIP_72H_STOP_MM: float = 15.0      # Chambers 2000
PRECIP_OPTIMAL_MIN_MM: float = 2.0    # ALFAM2 (Hafner et al. 2019)
PRECIP_OPTIMAL_MAX_MM: float = 10.0   # ALFAM2 (Hafner et al. 2019)

# --- Verdict
VERDICT_GOOD_MIN: float = 0.7
VERDICT_OK_MIN: float = 0.3


# ============================================================
# Dataclasses
# ============================================================


@dataclass
class WeatherInputs:
    """
    Ubicación y ventana de pronóstico para una evaluación meteorológica.

    Attributes
    ----------
    latitude, longitude
        Grados decimales. Open-Meteo ajusta a su grilla; las coordenadas
        servidas quedan registradas en el contexto del resultado.
    horizon_hours
        Horizonte de pronóstico. La precipitación siempre usa
        :data:`PRECIP_WINDOW_HOURS` (72 h), porque los umbrales de
        Chambers 2000 están definidos sobre esa ventana.
    application_hour_start, application_hour_end
        Ventana horaria de aplicación (hora local del sitio) sobre la que
        se agregan temperatura, viento y humedad. Default: 6h-18h.

        Justificación: Brassard et al. 2026 recomienda épandage en soirée
        (18h) o tôt matin (6h) — Gordon et al. 2000, Sommer & Olesen 2000,
        Moal et al. 1995 reportan 28-56% menor volatilización en esas horas.
        La ventana 6h-18h cubre ambos óptimos del paper.

        Nota: la precipitación NO se restringe a esta ventana. Se evalúa
        sobre 72h completas porque impacta durante y después de la aplicación.
    override_temp_min_c, override_temp_max_c, override_wind_max_ms,
    override_precip_next_72h_mm, override_precip_max_hourly_mm
        Ganchos de testing. Cuando **los cinco** están puestos no se hace
        ninguna llamada HTTP. Un override parcial sí llama al API y
        sustituye solo los campos dados.
    """

    latitude: float
    longitude: float
    horizon_hours: int = 24

    # Ventana horaria de aplicación (parametrizable)
    application_hour_start: int = DEFAULT_APPLICATION_HOUR_START
    application_hour_end: int = DEFAULT_APPLICATION_HOUR_END

    override_temp_min_c: Optional[float] = None
    override_temp_max_c: Optional[float] = None
    override_wind_max_ms: Optional[float] = None
    override_precip_next_72h_mm: Optional[float] = None
    override_precip_max_hourly_mm: Optional[float] = None

    def fully_overridden(self) -> bool:
        """``True`` cuando los cinco valores los da el caller."""
        return all(
            v is not None
            for v in (
                self.override_temp_min_c,
                self.override_temp_max_c,
                self.override_wind_max_ms,
                self.override_precip_next_72h_mm,
                self.override_precip_max_hourly_mm,
            )
        )


@dataclass
class WeatherResult(EvaluationResult):
    """
    Resultado de la evaluación meteorológica.

    Hereda ``score``, ``verdict`` y ``context`` de
    :class:`~.base.EvaluationResult`.

    Attributes
    ----------
    temp_min_c, temp_max_c
        Mínima y máxima sobre el horizonte [°C].
    wind_max_ms
        Viento máximo sobre el horizonte [m/s].
    precip_next_72h_mm
        Precipitación acumulada en 72 h [mm].
    precip_max_hourly_mm
        Precipitación horaria máxima en 72 h [mm/h].
    sub_scores
        Sub-scores por criterio antes de la agregación.
    stops_triggered
        Stops categóricos disparados, con su justificación y fuente. Lista
        vacía cuando no hubo ninguno.
    recommended_time_window, timing_reasoning
        Recomendación horaria de épandage (Gordon et al. 2000,
        Sommer & Olesen 2000, Moal et al. 1995).
    application_window_hours
        Ventana horaria usada, como ``"6h-18h"``.
    temp_min_window, temp_max_window, wind_window, precip_sum_window,
    precip_max_hourly_window
        Ventana temporal de la que sale cada agregado. No todas coinciden —
        ver GRANULARIDAD TEMPORAL en el docstring del módulo.
    hours_evaluated
        Número real de horas del horizonte que cayeron dentro de la ventana.
    humidity_max_pct
        Humedad relativa máxima [%]. **Solo información.** No entra al
        scoring: según Huijsmans 2001 (en Brassard et al. 2026) actúa como
        factor de compensación, no como criterio independiente.
    """

    temp_min_c: float = float("nan")
    temp_max_c: float = float("nan")
    wind_max_ms: float = float("nan")
    precip_next_72h_mm: float = float("nan")
    precip_max_hourly_mm: float = float("nan")
    sub_scores: Dict[str, float] = field(default_factory=dict)
    stops_triggered: List[str] = field(default_factory=list)
    recommended_time_window: str = ""
    timing_reasoning: str = ""
    application_window_hours: str = ""
    hours_evaluated: int = 0
    # Trazabilidad temporal (v4.2)
    temp_min_window: str = ""
    temp_max_window: str = ""
    wind_window: str = ""
    precip_sum_window: str = ""
    precip_max_hourly_window: str = ""
    humidity_max_pct: float = float("nan")


# ============================================================
# Ventana horaria de aplicación
# ============================================================


def filter_forecast_by_hour_window(
    forecast: Dict[str, Sequence[Any]],
    hour_start: int,
    hour_end: int,
    horizon_hours: int,
) -> Dict[str, Any]:
    """
    Filtra las series horarias del forecast a solo horas dentro de
    ``[hour_start, hour_end]`` (inclusive) durante las próximas
    ``horizon_hours``.

    Retorna dict con las mismas keys pero listas filtradas.
    Solo aplica a: ``temperature_2m``, ``wind_speed_10m``,
    ``relative_humidity_2m``. ``precipitation`` y
    ``precipitation_probability`` se retornan sin filtrar.

    Justificación de la ventana (Brassard et al. 2026, IRDA-MAPAQ,
    sección 3.6.2.3): el épandage se recomienda en soirée (18h) o tôt matin
    (6h), donde Gordon et al. 2000 reporta 28-56% menos volatilización,
    Sommer & Olesen 2000 un 50%, y Moal et al. 1995 un 37.5-45%. Agregar
    temperatura y viento sobre las 24 h completas mide horas en las que
    nadie va a aplicar.

    La precipitación queda fuera del filtro a propósito: llueve sobre el
    fumier ya aplicado, de día o de noche.

    Assumes ``forecast["time"]`` contiene timestamps ISO en hora local del
    sitio (Open-Meteo con ``timezone=auto``).

    Args:
        forecast: dict con listas horarias, incluyendo ``"time"``
        hour_start: hora inicio ventana (0-23)
        hour_end: hora fin ventana inclusive (0-23)
        horizon_hours: número de horas del horizonte

    Returns:
        dict con series filtradas para variables meteorológicas
        (excepto precipitación que queda sin filtrar), más
        ``"_application_window"`` con metadata de depuración.

    Raises:
        ValueError: si no queda ninguna hora dentro de la ventana, si el
            rango horario es inválido, o si ``forecast`` no trae ``"time"``.
    """
    if not 0 <= hour_start <= 23 or not 0 <= hour_end <= 23:
        raise ValueError(
            f"hour_start y hour_end deben estar en 0-23, "
            f"recibido [{hour_start}, {hour_end}]"
        )
    if hour_start > hour_end:
        raise ValueError(
            f"Ventana [{hour_start}h-{hour_end}h] cruza medianoche; "
            f"no soportado. Usar hour_start <= hour_end."
        )
    if "time" not in forecast:
        raise ValueError(
            "forecast no trae 'time'; no se puede determinar la hora local. "
            "Pedir el pronóstico con timezone=auto."
        )

    times = list(forecast["time"])[:horizon_hours]

    # Índices de horas dentro de la ventana
    valid_indices = []
    for i, ts in enumerate(times):
        try:
            hour = datetime.fromisoformat(ts).hour
        except (ValueError, TypeError):
            # Fallback: parse manual "YYYY-MM-DDTHH:MM"
            try:
                hour = int(str(ts)[11:13])
            except (ValueError, IndexError):
                # Sin hora legible: se asume que el índice 0 es la hora 0.
                # Documentado como fallback; no debería ocurrir con Open-Meteo.
                hour = i % 24
        if hour_start <= hour <= hour_end:
            valid_indices.append(i)

    if not valid_indices:
        raise ValueError(
            f"No hay horas dentro de ventana [{hour_start}h-{hour_end}h] "
            f"en las próximas {horizon_hours}h. Revisar timezone del forecast."
        )

    filtered: Dict[str, Any] = {}

    # Variables que SE filtran por ventana horaria
    for key in (VAR_TEMPERATURE, VAR_WIND, VAR_HUMIDITY):
        if key in forecast:
            series = list(forecast[key])
            filtered[key] = [series[i] for i in valid_indices if series[i] is not None]

    # Variables que NO se filtran (precipitación post-aplicación)
    for key in (VAR_PRECIPITATION, "precipitation_probability"):
        if key in forecast:
            filtered[key] = [v for v in forecast[key] if v is not None]

    # Metadata para debug
    filtered["_application_window"] = {
        "hour_start": hour_start,
        "hour_end": hour_end,
        "hours_in_window": len(valid_indices),
        "total_horizon_hours": horizon_hours,
        "first_hour_in_window": times[valid_indices[0]] if times else None,
        "last_hour_in_window": times[valid_indices[-1]] if times else None,
    }

    return filtered


# ============================================================
# Scoring por sub-criterio
# ============================================================


def score_temperature(
    temp_min_c: float, temp_max_c: float
) -> Tuple[float, Optional[str]]:
    """
    Sub-criterio de temperatura.

    IMPORTANTE — granularidad temporal (v4.2):
    - temp_min: agregado sobre 24h COMPLETAS (para detectar helada nocturna
      que congela suelo, afectando infiltración durante horas de aplicación).
    - temp_max: agregado sobre ventana horaria de aplicación (para evaluar
      pico térmico durante épandage real).

    Rationale: un suelo helado a las 6 AM sigue sin infiltrar a las 8 AM.
    La señal de helada nocturna es operacionalmente relevante aunque el
    épandage se haga a media mañana.

    Umbrales (Brassard et al. 2026):
    - temp_min < 0°C → categorical stop (freeze, sin infiltración)
    - temp_max > 25°C → categorical stop (Brassard et al. 2024: pertes
      grandement affectées)
    - 0-14°C → excelente (Pedersen 2021)
    - 14-20°C → aceptable (Huijsmans 2003: +54% loss por +10°C)
    - 20-25°C → riesgo alto (Svensson 1994: triple loss de 14 a 24°C)

    Fuente compilada en Brassard et al. 2026, IRDA-MAPAQ, sección 3.6.2.3.

    Returns
    -------
    tuple
        ``(score, stop_reason)``; ``stop_reason`` es ``None`` si no hay stop.
    """
    if temp_min_c < TEMP_FREEZE_STOP_C:
        return (0.0, "temp_min < 0°C (freeze, no infiltración)")
    if temp_max_c > TEMP_HIGH_STOP_C:
        return (
            0.0,
            "temp_max > 25°C (Brassard et al. 2024: pertes grandement affectées)",
        )

    if temp_max_c <= TEMP_NO_EFFECT_MAX_C:
        return (1.0, None)  # excelente (Pedersen 2021: sin efecto major)
    if temp_max_c <= TEMP_MID_C:
        # Interpolación linear 14→20°C: 1.0 → 0.7
        # Base: Huijsmans 2003 +54% loss de 10 a 20°C
        return (1.0 - (temp_max_c - TEMP_NO_EFFECT_MAX_C) * (0.3 / 6), None)
    # 20-25°C. Interpolación linear 20→25°C: 0.7 → 0.3
    # Base: Svensson 1994 triple loss de 14 a 24°C
    return (0.7 - (temp_max_c - TEMP_MID_C) * (0.4 / 5), None)


def score_wind(wind_max_ms: float) -> Tuple[float, Optional[str]]:
    """
    Puntúa el viento máximo sobre el horizonte.

    Umbrales de literatura (fuentes compiladas en Brassard et al. 2026,
    IRDA-MAPAQ, sección 3.6.2.3):

    - ``< 2.5 m/s`` → excelente (Sommer et al. 1991: sin efecto)
    - ``2.5-4 m/s`` → aceptable (Sommer et al. 1991: plateau)
    - ``4-8 m/s`` → riesgo alto (Huijsmans 2001: +2 m/s = +65% volatilización)
    - ``> 8 m/s`` → stop categórico (viento operacionalmente peligroso)

    Thompson et al. 1990 aporta evidencia adicional del efecto del viento
    sobre la volatilización de NH3.

    Fuente compilada en Brassard et al. 2026, IRDA-MAPAQ.

    Returns
    -------
    tuple
        ``(score, stop_reason)``.
    """
    if wind_max_ms > WIND_STOP_MS:
        return (0.0, "wind > 8 m/s (viento operacionalmente peligroso)")

    if wind_max_ms <= WIND_NO_EFFECT_MAX_MS:
        return (1.0, None)  # excelente
    if wind_max_ms <= WIND_PLATEAU_MAX_MS:
        # Interpolación 2.5→4 m/s: 1.0 → 0.6
        return (1.0 - (wind_max_ms - WIND_NO_EFFECT_MAX_MS) * (0.4 / 1.5), None)
    # 4-8 m/s. Interpolación 4→8 m/s: 0.6 → 0.2
    return (0.6 - (wind_max_ms - WIND_PLATEAU_MAX_MS) * (0.4 / 4), None)


def score_precipitation(
    precip_next_72h_mm: float, precip_max_hourly_mm: float
) -> Tuple[float, Optional[str]]:
    """
    Sub-criterio de precipitación.

    IMPORTANTE — granularidad temporal (v4.2):
    - precip_next_72h_mm: suma sobre 72h (Chambers 2000: acumulado post-
      aplicación causa runoff/erosión)
    - precip_max_hourly_mm: máximo hourly sobre 24h próximas (intensidad
      erosiva importa DURANTE y JUSTO después del épandage, no 3 días después)

    Umbrales (Brassard et al. 2026):
    Categorical stops:
    - precip_max_hourly > 4 mm/h en 24h → stop (Chambers 2000: erosión hídrica)
    - precip_next_72h > 15 mm → stop (Chambers 2000: acumulado erosivo)

    Escala continua:
    - 2-10 mm en 72h → excelente (ALFAM2: pluie modérée reduce hasta 3% pérdidas)
    - < 2 mm → aceptable con volatilización alta (Brassard: absence de pluie)
    - 10-15 mm → aceptable con riesgo runoff moderado

    Sharpe 2004 aporta evidencia sobre pérdidas de P por runoff tras épandage.

    Fuente compilada en Brassard et al. 2026, IRDA-MAPAQ, secciones 3.6.2.3
    y 3.7.1.

    Returns
    -------
    tuple
        ``(score, stop_reason)``.
    """
    if precip_max_hourly_mm > PRECIP_HOURLY_STOP_MM:
        return (
            0.0,
            f"precip {precip_max_hourly_mm}mm/h > 4 mm/h (Chambers 2000: erosión)",
        )
    if precip_next_72h_mm > PRECIP_72H_STOP_MM:
        return (
            0.0,
            f"precip 72h {precip_next_72h_mm}mm > 15 mm "
            f"(Chambers 2000: riesgo erosión)",
        )

    if PRECIP_OPTIMAL_MIN_MM <= precip_next_72h_mm <= PRECIP_OPTIMAL_MAX_MM:
        return (1.0, None)  # zona óptima (ALFAM2: pluie modérée reduce hasta 3%)
    if precip_next_72h_mm < PRECIP_OPTIMAL_MIN_MM:
        # Poca lluvia: volatilización alta esperada. Linear 0→2 mm: 0.5 → 1.0
        return (0.5 + (precip_next_72h_mm / PRECIP_OPTIMAL_MIN_MM) * 0.5, None)
    # 10 < precip <= 15. Linear 10→15 mm: 1.0 → 0.6
    return (1.0 - (precip_next_72h_mm - PRECIP_OPTIMAL_MAX_MM) * (0.4 / 5), None)


# ============================================================
# Agregación y verdict
# ============================================================


def aggregate_scores(sub_scores: Dict[str, float]) -> float:
    """
    Media geométrica de los sub-scores (Adamchuk 2011, Geoderma 163:63-73).

    Si CUALQUIER sub-score es 0.0 (stop categórico), el resultado es 0.0.
    La multiplicación penaliza los fallos críticos de un solo factor, que es
    exactamente lo que un stop categórico significa.

    Raises
    ------
    ValueError
        Si ``sub_scores`` está vacío.
    """
    if not sub_scores:
        raise ValueError("sub_scores must not be empty")
    if any(s == 0.0 for s in sub_scores.values()):
        return 0.0

    n = len(sub_scores)
    product = math.prod(sub_scores.values())
    return product ** (1 / n)


def get_verdict(score: float) -> str:
    """Mapea el score compuesto a la etiqueta de verdict."""
    if score >= VERDICT_GOOD_MIN:
        return "good"
    if score >= VERDICT_OK_MIN:
        return "ok"
    return "bad"


def get_recommended_timing() -> Tuple[str, str]:
    """
    Devuelve la ventana horaria recomendada para el épandage.

    Fuentes compiladas en Brassard et al. 2026, IRDA-MAPAQ, sección 3.6.2.3:

    - Gordon et al. 2000: soirée reduce volatilisation 28-56%
    - Sommer & Olesen 2000: aplicación 6h/18h reduce 50%
    - Moal et al. 1995: soirée reduce 37.5-45%

    La recomendación es constante: no depende del pronóstico, solo del ciclo
    diurno de temperatura, radiación y déficit de presión de vapor.
    """
    return (
        "18h-6h",
        "Épandage en soirée (18h) o tôt matin (6h) reduce volatilización 28-56% "
        "según Gordon et al. 2000, Sommer & Olesen 2000, Moal et al. 1995. "
        "Razón: temperatura, rayonnement y déficit presión vapor más bajos.",
    )


# ============================================================
# Evaluator
# ============================================================


class WeatherEvaluator:
    """
    Evalúa las condiciones meteorológicas para aplicación de fumier en una
    ubicación, usando el pronóstico de Open-Meteo.

    Todos los umbrales provienen de Brassard et al. 2026 (IRDA-MAPAQ); ver
    el docstring del módulo para la lista completa de fuentes primarias.

    Cada :meth:`evaluate` hace **una** petición HTTP, de 72 h como mínimo,
    porque los umbrales de precipitación están definidos sobre esa ventana.
    La temperatura y el viento se agregan solo sobre ``horizon_hours``.
    """

    def __init__(self, client: OpenMeteoClient) -> None:
        """
        Parameters
        ----------
        client
            Cliente Open-Meteo ya configurado. El evaluator no construye uno
            para que el timeout y el endpoint sigan siendo del caller y para
            poder testear contra un stub.
        """
        self.client: OpenMeteoClient = client

    def _get_forecast(self, inputs: WeatherInputs) -> ForecastResult:
        """
        Pide el pronóstico. Siempre 72 h como mínimo, por la ventana de
        precipitación de Chambers 2000.
        """
        hours = max(inputs.horizon_hours, PRECIP_WINDOW_HOURS)
        return self.client.get_forecast(
            latitude=inputs.latitude,
            longitude=inputs.longitude,
            hours=hours,
            variables=(VAR_TEMPERATURE, VAR_WIND, VAR_PRECIPITATION, VAR_HUMIDITY),
        )

    def evaluate(self, inputs: WeatherInputs) -> WeatherResult:
        """
        Evalúa condiciones meteorológicas para aplicación de fumier.

        Basado en umbrales de literatura recopilados en:
        Brassard et al. 2026 (IRDA-MAPAQ).

        Todos los agregados de temperatura, viento y humedad se calculan
        sobre la ventana horaria de aplicación
        ``[application_hour_start, application_hour_end]`` para alinear con
        la recomendación del paper de épandage en soirée/tôt matin
        (Gordon et al. 2000: -28 a -56%; Sommer & Olesen 2000: -50%;
        Moal et al. 1995: -37.5 a -45%).

        Excepciones deliberadas a esa ventana (v4.2):

        - ``temp_min`` se agrega sobre las 24 h completas, porque una helada
          nocturna congela un suelo que sigue sin infiltrar a media mañana
          (Fix B).
        - ``precip_max_hourly`` se agrega sobre las próximas 24 h, no 72:
          la intensidad erosiva importa durante y justo después del épandage
          (Fix C).
        - ``precip_next_72h_mm`` sí se suma sobre 72 h completas (impacto
          post-aplicación, Chambers 2000).

        Con overrides completos no se hace ninguna llamada ni filtrado: el
        caller entrega los agregados ya calculados.

        Returns
        -------
        WeatherResult

        Raises
        ------
        WeatherError
            O una subclase, si falla la petición de pronóstico.
        """
        time_window, timing_reasoning = get_recommended_timing()
        window_label = (
            f"{inputs.application_hour_start}h-{inputs.application_hour_end}h"
        )

        if inputs.fully_overridden():
            # Overrides completos: el filtrado horario no aplica, porque el
            # caller ya entrega los agregados finales.
            temp_min_c = float(inputs.override_temp_min_c)
            temp_max_c = float(inputs.override_temp_max_c)
            wind_max_ms = float(inputs.override_wind_max_ms)
            precip_next_72h_mm = float(inputs.override_precip_next_72h_mm)
            precip_max_hourly_mm = float(inputs.override_precip_max_hourly_mm)
            humidity_max_pct = float("nan")
            hours_evaluated = 0
            context: Dict[str, Any] = {"source": "override"}
        else:
            raw = self._get_forecast(inputs)
            raw_forecast: Dict[str, Sequence[Any]] = {
                "time": raw.times,
                **raw.values,
            }

            # Filtrar por ventana horaria de aplicación
            forecast = filter_forecast_by_hour_window(
                raw_forecast,
                hour_start=inputs.application_hour_start,
                hour_end=inputs.application_hour_end,
                horizon_hours=inputs.horizon_hours,
            )
            window_meta = forecast["_application_window"]
            hours_evaluated = window_meta["hours_in_window"]

            # Temperatura max, viento y humedad: solo la ventana de aplicación
            temps_window = forecast[VAR_TEMPERATURE]
            winds = forecast[VAR_WIND]
            humidities = forecast[VAR_HUMIDITY]

            # temp_min sobre 24h COMPLETAS (para freeze stop — Fix B).
            # Rationale: helada nocturna congela suelo que sigue helado en
            # horas de aplicación.
            temps_full = [
                v
                for v in raw_forecast[VAR_TEMPERATURE][: inputs.horizon_hours]
                if v is not None
            ]

            # Precipitación:
            # - sum sobre 72h (Chambers 2000: acumulado post-aplicación importa)
            # - max hourly sobre 24h (intensidad erosiva importa DURANTE y
            #   JUSTO después del épandage, no 3 días después) — Fix C
            precips_72h = [
                v
                for v in raw_forecast[VAR_PRECIPITATION][:PRECIP_WINDOW_HOURS]
                if v is not None
            ]
            precips_24h = [
                v
                for v in raw_forecast[VAR_PRECIPITATION][
                    :PRECIP_INTENSITY_WINDOW_HOURS
                ]
                if v is not None
            ]

            temp_min_c = min(temps_full)
            temp_max_c = max(temps_window)
            wind_max_ms = max(winds)
            humidity_max_pct = max(humidities)
            precip_next_72h_mm = sum(precips_72h)
            precip_max_hourly_mm = max(precips_24h)

            # Overrides parciales: `is not None`, nunca `or`, porque 0.0 es
            # un valor legítimo y falsy para las cinco variables.
            if inputs.override_temp_min_c is not None:
                temp_min_c = float(inputs.override_temp_min_c)
            if inputs.override_temp_max_c is not None:
                temp_max_c = float(inputs.override_temp_max_c)
            if inputs.override_wind_max_ms is not None:
                wind_max_ms = float(inputs.override_wind_max_ms)
            if inputs.override_precip_next_72h_mm is not None:
                precip_next_72h_mm = float(inputs.override_precip_next_72h_mm)
            if inputs.override_precip_max_hourly_mm is not None:
                precip_max_hourly_mm = float(inputs.override_precip_max_hourly_mm)

            context = {
                "source": "open-meteo",
                "requested_latitude": inputs.latitude,
                "requested_longitude": inputs.longitude,
                "served_latitude": raw.latitude,
                "served_longitude": raw.longitude,
                "timezone": raw.timezone,
                "elevation_m": raw.elevation,
                "horizon_hours": inputs.horizon_hours,
                "precip_window_hours": PRECIP_WINDOW_HOURS,
                "application_window": window_meta,
                "first_timestamp": raw.times[0] if raw.times else None,
                "units": dict(raw.units),
                "raw_response": raw.raw_response,
            }

        temp_score, temp_stop = score_temperature(temp_min_c, temp_max_c)
        wind_score, wind_stop = score_wind(wind_max_ms)
        precip_score, precip_stop = score_precipitation(
            precip_next_72h_mm, precip_max_hourly_mm
        )

        sub_scores = {
            "temperature": temp_score,
            "wind": wind_score,
            "precipitation": precip_score,
        }
        stops_triggered = [
            s for s in (temp_stop, wind_stop, precip_stop) if s is not None
        ]

        score = aggregate_scores(sub_scores)
        verdict = get_verdict(score)

        logger.info(
            "Weather evaluated: score=%.3f verdict=%s stops=%d "
            "(T %.1f-%.1f C, wind %.1f m/s, precip72h %.1f mm)",
            score, verdict, len(stops_triggered),
            temp_min_c, temp_max_c, wind_max_ms, precip_next_72h_mm,
        )

        return WeatherResult(
            score=score,
            verdict=verdict,
            temp_min_c=temp_min_c,
            temp_max_c=temp_max_c,
            wind_max_ms=wind_max_ms,
            precip_next_72h_mm=precip_next_72h_mm,
            precip_max_hourly_mm=precip_max_hourly_mm,
            sub_scores=sub_scores,
            stops_triggered=stops_triggered,
            recommended_time_window=time_window,
            timing_reasoning=timing_reasoning,
            application_window_hours=window_label,
            hours_evaluated=hours_evaluated,
            temp_min_window=f"{inputs.horizon_hours}h",
            temp_max_window=window_label,
            wind_window=window_label,
            precip_sum_window=f"{PRECIP_WINDOW_HOURS}h",
            precip_max_hourly_window=f"{PRECIP_INTENSITY_WINDOW_HOURS}h",
            humidity_max_pct=humidity_max_pct,
            context=context,
        )
