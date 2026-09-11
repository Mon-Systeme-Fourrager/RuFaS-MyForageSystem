"""
Domain constants and equation coefficients for the Silage Preseal phase (Silostg.for's ``PRESEAL``
subroutine, lines 634-714), kept out of ``silage.py`` per ``RUFAS/biophysical/CLAUDE.md``'s "Constants
must live in dedicated *_constants.py modules per domain; do not inline magic numbers" rule.

"""

"""
Shared respiration-model constants for the Preseal phase (Silostg.for:643, PRESEAL subroutine).
K and KM are Michaelis-Menten-derived diffusion constants; FC is the CO2-dependent respiration
correction factor; PSIA is atmospheric oxygen concentration (fraction). All four are fixed across
crop types in the source.

"""
PRESEAL_K = 9.0
PRESEAL_KM = 0.055
PRESEAL_FC = 0.756
PRESEAL_ATMOSPHERIC_OXYGEN_FRACTION = 0.21
"""Fixed initial silage pH under IFSM's no-acid-treatment default (Silostg.for:269-271, FACID=0)."""
PRESEAL_INITIAL_PH = 5.8
"""Preseal exposure time is capped at 3 days (Silostg.for:267) and floored at 0 (Silostg.for:268)."""
PRESEAL_EXPOSURE_CAP_DAYS = 3.0
"""Fallback exposure time (3 hours) for the newest plot in a silo with no successor yet (Silostg.for:261)."""
PRESEAL_FALLBACK_EXPOSURE_DAYS = 0.125
"""
Fraction of respired dry matter retained as water rather than lost as gas, per Silostg.for:697,708
(spec §5.1's own citation for this fact). Silostg.for:707-708's PLOT(NPL,11)/PLOT(NPL,3) update uses
a 72/180 gas-loss ratio; solving for the resulting fresh-mass change shows only that 72/180 leaves the
crop, while the complementary 108/180 stays as retained moisture. This constant is that retained
(1 - 72/180) fraction — see the `moisture_loss_kg` sign in `Silage._finalize_preseal_loss`: only the
gas-lost fraction of dry matter leaves the crop as fresh mass, while the water-retained fraction
stays behind.
"""
PRESEAL_WATER_RETENTION_FRACTION = 1.0 - 72.0 / 180.0

"""
Maximum daily respiration rate coefficients (``MUMAX``, per unit dry-matter fraction), by crop type
(Silostg.for:649-655): haylage/alfalfa uses the higher rate, corn silage the lower one.

"""
PRESEAL_ALFALFA_MAX_RESPIRATION_RATE = 4.8
PRESEAL_NON_ALFALFA_MAX_RESPIRATION_RATE = 2.9

"""Minimum silage thickness (cm) used in the diffusion-path calculation (``THICK``, Silostg.for:659)."""
PRESEAL_MIN_THICKNESS_CM = 100.0
"""Depth-to-thickness unit conversion, meters to centimeters, in the same ``THICK`` term (Silostg.for:659)."""
PRESEAL_DEPTH_M_TO_CM = 100.0
"""
Diffusion coefficient's temperature-scaling factor and Celsius offset (``D``, Silostg.for:660):
``D = factor * (offset_c + temperature_c)**2``. The offset is the source's own literal ``273.``, not
the full 273.15 Celsius-to-Kelvin conversion (`GeneralConstants.CELSIUS_TO_KELVIN`) — kept distinct so
this translation matches the source bit-for-bit rather than silently changing its numeric output.

"""
PRESEAL_DIFFUSION_COEFFICIENT_FACTOR = 0.0086
PRESEAL_DIFFUSION_TEMPERATURE_OFFSET_C = 273.0
"""Effective diffusion-path tortuosity through packed silage, fixed in the source (``TAU``, Silostg.for:661)."""
PRESEAL_TORTUOSITY = 2.0 / 3.0
"""
Numerator of the maximum-relative-density relationship (``RHOMAX = numerator / (numerator -
dry_matter_fraction)``, Silostg.for:662).
"""
PRESEAL_MAX_RELATIVE_DENSITY_NUMERATOR = 3.0
"""Fractional ceiling applied to relative density before it reaches the theoretical maximum (Silostg.for:663)."""
PRESEAL_RELATIVE_DENSITY_CAP_FRACTION = 0.99
"""Bulk-density unit conversion (kg DM/m3 to g DM/cm3) used in the relative-density calculation (Silostg.for:663)."""
PRESEAL_DENSITY_KG_PER_M3_TO_G_PER_CM3 = 0.001

"""
Dry-matter-fraction threshold above which the respiration factor (``FD``) is fixed at its saturated
minimum (Silostg.for:665-666).
"""
PRESEAL_HIGH_DRY_MATTER_THRESHOLD = 0.693
"""Saturated respiration factor used above `PRESEAL_HIGH_DRY_MATTER_THRESHOLD` (Silostg.for:666)."""
PRESEAL_HIGH_DRY_MATTER_RESPIRATION_FACTOR = 0.0384
"""Dry-matter-fraction threshold below which the respiration factor is fixed at 1.0 (Silostg.for:667,670)."""
PRESEAL_LOW_DRY_MATTER_THRESHOLD = 0.20
"""
Quadratic respiration-factor coefficients (``FD``, Silostg.for:668), fit between
`PRESEAL_LOW_DRY_MATTER_THRESHOLD` and `PRESEAL_HIGH_DRY_MATTER_THRESHOLD`:
``intercept - linear_coefficient * dm_fraction + quadratic_coefficient * dm_fraction**2``.

"""
PRESEAL_RESPIRATION_FACTOR_INTERCEPT = 1.93
PRESEAL_RESPIRATION_FACTOR_LINEAR_COEFFICIENT = 5.46
PRESEAL_RESPIRATION_FACTOR_QUADRATIC_COEFFICIENT = 3.94

"""
Temperature (degrees C) above which the Preseal temperature factor (``FT``) saturates at 1.0
(Silostg.for:674-675).
"""
PRESEAL_TEMPERATURE_FACTOR_SATURATION_C = 25.0
"""
Sub-saturation temperature-factor coefficients (``FT``, Silostg.for:677):
``coefficient * exp(rate * temperature_c)``.
"""
PRESEAL_TEMPERATURE_FACTOR_COEFFICIENT = 0.178
PRESEAL_TEMPERATURE_FACTOR_RATE = 0.069
"""pH-factor normalization constants (``FPH``, Silostg.for:679): ``(ph - offset) / scale``."""
PRESEAL_PH_FACTOR_OFFSET = 3.0
PRESEAL_PH_FACTOR_SCALE = 3.5

"""Per-day dry-matter loss coefficient applied to the average respiration rate (``DMLPD``, Silostg.for:685)."""
PRESEAL_LOSS_PER_DAY_COEFFICIENT = 0.0299

"""
Self-heating temperature-rise coefficients (``DELT``, Silostg.for:697, "TEMPERATURE RISE ASSUMING 70%
RETENTION OF HEAT GENERATED"): converts a day's DM-loss (kg) into a temperature rise (degrees C), via
``energy_coefficient * loss_today_kg * heat_retention_fraction / (denominator_a / dm_fraction -
denominator_b)``.

"""
PRESEAL_TEMPERATURE_RISE_ENERGY_COEFFICIENT = 8436.0
PRESEAL_TEMPERATURE_RISE_HEAT_RETENTION_FRACTION = 0.7
PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_A = 2.22
PRESEAL_TEMPERATURE_RISE_DENOMINATOR_COEFFICIENT_B = 1.22
