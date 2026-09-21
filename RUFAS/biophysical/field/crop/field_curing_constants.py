"""Constants for the opt-in pre-harvest field-curing phase (cutting -> storage).

Two source groups, each cited per-constant below:

- DAFOSYM respiration/rain terms (Eq.7, 9, 10, 11) -- Rotz, Black, Mertens &
  Buckmaster (1989), "DAFOSYM" (PDF in ``00-inbox/``).
- Rotz & Chen (1985) drying-rate coefficients (Eq.2/Eq.5) -- "Alfalfa Drying
  Model for the Field Environment," *Trans. ASAE* 28(5):1686-1691 (PDF in
  ``00-inbox/``).

Both are primary sources, verified 2026-09-16 (see
``PLAN_add-preharvest-field-curing-phase.md``).
"""

CELSIUS_TO_FAHRENHEIT_SCALE: float = 9.0 / 5.0
"""Multiplicative term of the C-to-F conversion used by DAFOSYM's
Fahrenheit-calibrated respiration equation (Eq.7). Not present anywhere in
`RUFAS/general_constants.py`'s `GeneralConstants` (checked 2026-09-16 --
that class, not `RUFAS/units.py`, is where reusable conversion factors like
`MM_TO_M`/`KCAL_TO_MJ`/`CELSIUS_TO_KELVIN` actually live; `units.py` is only
the `MeasurementUnits` label Enum) -- defined here, scoped to this module's
own DAFOSYM calls only."""

CELSIUS_TO_FAHRENHEIT_OFFSET: float = 32.0
"""Additive term of the C-to-F conversion, paired with
CELSIUS_TO_FAHRENHEIT_SCALE above."""

MM_TO_INCHES_DIVISOR: float = 25.4
"""Unit conversion for DAFOSYM's inches-calibrated rain equations (Eq.9,
10) against RuFaS's mm weather data. Same "not in GeneralConstants, defined
here" reasoning as CELSIUS_TO_FAHRENHEIT_SCALE above."""

FIELD_CURING_RESPIRATION_COEFFICIENT: float = 0.00239
"""Leading coefficient of DAFOSYM's respiration loss,
RL = 0.00239*(AMC-0.27)*exp(0.038*AT_F), fraction DM lost per 12h period.
Rotz, Black, Mertens & Buckmaster (1989), DAFOSYM, Eq.7, p.86."""

FIELD_CURING_RESPIRATION_MOISTURE_THRESHOLD: float = 0.27
"""Wet-basis moisture threshold (AMC) below which DAFOSYM's respiration
loss (Eq.7) is zero. Rotz, Black, Mertens & Buckmaster (1989), DAFOSYM,
Eq.7, p.86."""

FIELD_CURING_RESPIRATION_TEMP_COEFFICIENT_F: float = 0.038
"""Temperature-exponent coefficient of DAFOSYM's respiration loss (Eq.7),
applied to AT_F, avg temp in deg F (convert from RuFaS's Celsius input via
CELSIUS_TO_FAHRENHEIT_SCALE/OFFSET before calling). Rotz, Black, Mertens &
Buckmaster (1989), DAFOSYM, Eq.7, p.86."""

FIELD_CURING_RAIN_LEAF_LOSS_COEFFICIENT: float = 0.094
"""Coefficient of DAFOSYM's rain-induced leaf DM loss,
RNLL = 0.094*RAIN_IN. RAIN_IN = rainfall, inches (convert from RuFaS's mm
input via MM_TO_INCHES_DIVISOR before calling). Rotz, Black, Mertens &
Buckmaster (1989), DAFOSYM, Eq.9, p.86."""

FIELD_CURING_RAIN_LEAF_LOSS_CAP_FRACTION: float = 0.15
"""Ceiling on RNLL (rain-induced leaf DM loss) as a fraction of plant DM.
Rotz, Black, Mertens & Buckmaster (1989), DAFOSYM, Eq.9, p.86."""

FIELD_CURING_LEACHING_RAIN_COEFFICIENT: float = 0.28
"""Rain leaching loss RNL = (1-NDF)*(1-exp(-0.28*RAIN_IN)). RAIN_IN =
rainfall, inches (same conversion as FIELD_CURING_RAIN_LEAF_LOSS_COEFFICIENT
above). Rotz, Black, Mertens & Buckmaster (1989), DAFOSYM, Eq.10, p.86."""

FIELD_CURING_LEACHING_CP_MULTIPLIER: float = 1.2
"""CP change under leaching: CPf = CPi*(1-1.2*RNL)/(1-RNL). Rotz, Black,
Mertens & Buckmaster (1989), DAFOSYM, Eq.11, p.86."""

FIELD_CURING_RNL_MAX: float = 0.99
"""Numerical guard, not a DAFOSYM threshold: CPf = CPi*(1-1.2*RNL)/(1-RNL)
(Eq.11) has a division singularity as RNL -> 1 (possible for a low-NDF crop
under heavy accumulated rain). RNL is clamped to this value before use in
Eq.11/Eq.12, the same "numerical guard, not a scientific threshold" pattern
as `BEEF_DMI_MIN_NE_CONCENTRATION` (RUFAS/biophysical/CLAUDE.md's own cited
example)."""

DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT: float = 9.30
"""Chemical-conditioning multiplier on the solar-insolation term of Rotz &
Chen (1985)'s drying-rate constant DR (dry-bulb-temperature form, Eq.5):
DR = [SI*(1+9.30*AR) + 5.42*DB] /
     [66.4*SM + SD*(2.06-0.97*DAY)*(1.55+21.9*AR) + 3037]
"Alfalfa Drying Model for the Field Environment," Trans. ASAE 28(5):
1686-1691, Eq.5, R2=0.75 (model development). Chosen over the paper's Eq.4
(VPD form) because RuFaS tracks no humidity/VPD anywhere (CurrentDayConditions
has no such field) -- SI/DB are directly available (incoming_light,
mean_air_temperature); AR (chemical conditioning) is fixed at 0.0 pending
any chemical-conditioning input, matching RuFaS's current absence of that
concept."""

DRYING_RATE_DRY_BULB_COEFFICIENT: float = 5.42
"""Dry-bulb-temperature (DB) coefficient of Eq.5's numerator -- see
DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation and
citation.

**OPEN VERIFICATION ITEM (deliberately left open, not resolved by this
change)**: DB's units in Rotz & Chen (1985)'s own Eq.5 are not
independently confirmed here -- `dry_bulb_drying_rate` (field_curing.py)
passes `dry_bulb_temp_c` through as Celsius, unconverted, pending this.
`Curing_DRAFT_Rotz1985_1995.md`'s glossary
(05-dev/msf/fourrager/04_Resources/) states "DB DRY BULB TEMPERATURE, DEG C"
for this same equation, but that file is itself a secondary reconstruction,
not the primary paper's own stated units (a prior OCR extraction of
Rotz1985.pdf's own Table 2 was garbled and inconclusive on this point).
Re-read `00-inbox/silage_pdfs/Rotz1985.pdf`'s Notation/Methods section
directly for DB's stated units before treating this as resolved -- if it
turns out to need Fahrenheit, convert at the call site using
`CELSIUS_TO_FAHRENHEIT_SCALE`/`_OFFSET` above, alongside the confirmed
DAFOSYM (Eq.7/9/10) conversions."""

DRYING_RATE_SOIL_MOISTURE_COEFFICIENT: float = 66.4
"""Soil-moisture (SM) coefficient of Eq.5's denominator -- see
DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation and
citation."""

DRYING_RATE_DAY_INTERCEPT: float = 2.06
"""Intercept of the DAY (mowing-day indicator) term in Eq.5's denominator --
see DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation
and citation."""

DRYING_RATE_DAY_SLOPE: float = 0.97
"""Slope of the DAY (mowing-day indicator) term in Eq.5's denominator --
see DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation
and citation."""

DRYING_RATE_APPLICATION_DENOMINATOR_INTERCEPT: float = 1.55
"""Intercept of the chemical-application-rate (AR) term in Eq.5's
denominator -- see DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the
full equation and citation."""

DRYING_RATE_APPLICATION_DENOMINATOR_SLOPE: float = 21.9
"""Slope of the chemical-application-rate (AR) term in Eq.5's denominator --
see DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation
and citation."""

DRYING_RATE_DENOMINATOR_CONSTANT: float = 3037.0
"""Additive constant in Eq.5's denominator -- see
DRYING_RATE_SOLAR_APPLICATION_COEFFICIENT above for the full equation and
citation."""

MJ_PER_M2_DAY_TO_W_PER_M2: float = 1_000_000.0 / 86_400.0
"""Converts RuFaS's `CurrentDayConditions.incoming_light` (MJ/m2 -- the
dataclass's own docstring says only "Incoming light radiation energy
(MJ/m^2)", not explicitly "daily total"; treating it as one is a reasonable
but not literally-confirmed inference from context) into the average W/m2
(instantaneous power flux) that Rotz & Chen (1985) states `SI` is measured in
(confirmed directly in the paper's own parameter list, 'SI = solar
insolation, W/m2'). Standard J/s <-> J/day identity (1e6 J/MJ / 86400 s/day),
not an invented equation -- but note this yields a *daily-average* SI, and
the paper's own field methodology for what SI value they used per data
point was never independently verified. **OPEN VERIFICATION ITEM**: the
methodological match between "daily average" and what Rotz & Chen actually
measured remains open, lower-priority, same class as the DB-units item
above."""

SWATH_MOISTURE_EQUILIBRIUM_FRACTION: float = 0.0
"""Equilibrium moisture content, set to zero per Rotz & Chen (1985)'s own
finding that it provided the best fit in the 80-20% wb range (see paper
text before Eq.2) -- M(t) = M0*exp(-DR*T) reduces to this when Me=0."""
