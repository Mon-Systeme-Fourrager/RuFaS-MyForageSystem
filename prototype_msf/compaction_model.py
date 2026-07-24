"""
Soil compaction risk for the MSF Expert System.

Chain:
  1. machinery      -> dynamic rear axle load        (Carranza-Diaz et al.)
  2. tyre specs     -> nominal contact area          (Grecenko 1995)
  3. load / area    -> sigma_act, applied stress
  4. clay + OC      -> bulk density                  (Perreault et al. 2022)
  5. BD + suction   -> sigma_pc, soil strength       (soilphysics soilStrength2)
  6. act vs pc      -> GREEN / YELLOW / RED          (soilphysics soilStrength)

VERIFIED SOURCES
  Files were downloaded to disk and read; SHA-256 recorded 2026-07-24.

  Carranza-Diaz, A.K., Sandoval Pabon, R.L., Forero Cabrera, N.M.,
    Castillo Herran, B. Herramienta computacional para determinar efectos
    en el suelo como consecuencia del paso de maquinaria agricola.
    Universidad Nacional de Colombia.  [paper read]

  Grecenko, A. (1995). Tyre footprint area on hard ground computed from
    catalogue values. Journal of Terramechanics 32(6): 325-333.
    [equations taken from the above paper, which cites it]

  Perreault, S., El Alem, A., Chokmani, K., Cambouris, A.N. (2022).
    Development of Pedotransfer Functions to Predict Soil Physical
    Properties in Southern Quebec (Canada). Agronomy 12(2): 526.
    DOI 10.3390/agronomy12020526. Open access, CC BY.  [PDF read]

  R package `soilphysics` v5.0 (2022-06-06), GPL (>= 2).
    Anderson Rodrigo da Silva and Renato Paiva de Lima.
    github.com/arsilva87/soilphysics
      R/soilStrength2.R    7F7200EFCAE286CCF73719923134710D40DDE871B1CA4672F37BE1D3F18915B3
      R/soilStrength.R     832AE88DECFFB96E07A7480451A776991AAD1949D03083966883196EE2ADC21A
      man/soilStrength2.Rd C4BC2E07678F9F2E2292AEA22CEE6ECA3FC1662733AD6C04FA970A2792F4FD1D
      man/soilStrength.Rd  63AECFE224611731A77C571CD6A10BC551727855684ABDF10FB37B5FDF4AA42E
      DESCRIPTION          BC9219ADC7030F84FA6E97D80848EE867D261F28070BFC2DB1523E8EF4DB1063

NOT READ
  Schjonning, P.; Lamande, M. (2018). Geoderma 320: 115-125.
    The soilphysics package attributes soilStrength2() to this paper.
    Cited here as attributed by the package, not as a primary source.

  Stettler, M. et al. (2014). Landtechnik 69(3): 132-138.
    man/soilStrength.Rd attributes the 0.5 / 1.1 bands to Terranimo,
    citing this paper. Same caveat.

NOT AVAILABLE
  Verified machinery parameters. No worked example is included; see the
  note at the bottom of this file.

  Verified Quebec B-horizon soil properties. RT-08 holds surface texture
  only. The IRDA PPC dataset (Proprietes Physico-Chimiques, par couche de
  sol) has Argile, Limon, Sable and MOS by horizon including B - see
  prototype_msf/irda_soil_database.md. Bulk density did not appear in the
  guide's field lists and would need checking against the GeoPackage itself.
"""

import math


# =============================================================
# PART 1 - Applied stress (sigma_act)
# Source: Carranza-Diaz et al. (UNAL); Grecenko (1995)
# =============================================================

def dynamic_rear_weight(
    static_rear_weight_kN: float,
    traction_force_kN: float,
    hitch_height_m: float,
    wheelbase_m: float,
    implement_angle_deg: float = 0.0,
) -> float:
    """
    Dynamic rear AXLE load, from moment equilibrium at the front axle
    contact point. Carranza-Diaz et al., eq. 1a:

        PDT = PET + FT * [ H/DE + tan(theta) * (B/DE + 1) ]

    The B/DE term is omitted here: B (horizontal offset of the implement
    draft point) is not available. With implement_angle_deg = 0 the term
    vanishes and the simplification is exact.

    Args:
        static_rear_weight_kN: static rear axle weight PET (kN)
        traction_force_kN:     implement draft force FT (kN)
        hitch_height_m:        drawbar height H (m)
        wheelbase_m:           wheelbase DE (m)
        implement_angle_deg:   implement angle with the horizontal (deg)

    Returns:
        Dynamic rear AXLE load (kN). Divide by the number of rear wheels
        for per-wheel load.
    """
    if implement_angle_deg != 0.0:
        raise NotImplementedError(
            "Non-zero implement angle requires the B parameter (horizontal "
            "offset of the draft point), which is not available. "
            "See eq. 1a in Carranza-Diaz et al."
        )
    return static_rear_weight_kN + (traction_force_kN * hitch_height_m) / wheelbase_m


def contact_area_geometric(
    total_diameter_m: float,
    static_load_radius_m: float,
    section_width_m: float,
    C1: float = 1.65,
) -> float:
    """
    Nominal geometric contact area of ONE tyre (Grecenko 1989, eq. 2):

        A_oj = C1 * sqrt( (dk - 2*rs) * bk * rs )

    C1 = 1.65 for agricultural traction wheels.
    """
    deflection = total_diameter_m - 2 * static_load_radius_m
    if deflection <= 0:
        raise ValueError(
            f"total_diameter_m ({total_diameter_m}) must exceed "
            f"2 * static_load_radius_m ({2*static_load_radius_m})"
        )
    return C1 * math.sqrt(deflection * section_width_m * static_load_radius_m)


def contact_area_experimental(
    static_load_radius_m: float,
    section_width_m: float,
    tire_load_kN: float,
    inflation_pressure_kPa: float,
) -> float:
    """
    Nominal experimental contact area of ONE tyre, from dimensional
    analysis (Sitkei & Sohne 1969, cited by Grecenko 1995).
    """
    ratio = tire_load_kN / (inflation_pressure_kPa
                            * static_load_radius_m * section_width_m)
    return static_load_radius_m * section_width_m * ratio


def applied_stress(
    axle_load_kN: float,
    contact_area_m2: float,
    n_wheels_per_axle: int = 2,
    correction_factor: float = 0.87,
) -> float:
    """
    Applied stress at the tyre-soil interface (sigma_act), in kPa.

        sigma_act = (axle_load / n_wheels) / (area * alpha_w)

    kN/m2 = kPa, so no unit conversion is needed.

    Per-wheel is the correct convention: soilphysics stressTraffic()
    documents its load input as "wheel load, kg" (man/stressTraffic.Rd:23)
    with no internal division by wheel count.

    Args:
        axle_load_kN:       dynamic axle load (kN)
        contact_area_m2:    contact area of ONE tyre (m2)
        n_wheels_per_axle:  2 for singles, 4 for duals
        correction_factor:  area correction alpha_w; 0.87 is the
                            conservative end of the 0.87-0.99 range
    """
    corrected_area = contact_area_m2 * correction_factor
    load_per_wheel = axle_load_kN / n_wheels_per_axle
    return load_per_wheel / corrected_area


# =============================================================
# PART 2 - Bulk density (Quebec-calibrated)
# Source: Perreault et al. (2022), Agronomy 12(2):526
# =============================================================

def organic_carbon_from_om(organic_matter_pct: float) -> float:
    """
    Organic matter -> organic carbon, Van Bemmelen factor (OM = OC * 1.724).
    Conventional approximation.
    """
    return organic_matter_pct / 1.724


def bulk_density_quebec_B(silt_pct: float, clay_pct: float,
                          oc_pct: float) -> float:
    """
    Bulk density, B HORIZON (subsoil). Perreault et al. (2022) Table A2,
    stepwise forward regression:

        rho_b = exp[ ln( -0.6911 + 0.0165*Si - 2.2053*C^0.1248
                         + 5.3959*OC^-0.0874 ) / 2.4488 ]

    The division by 2.4488 back-transforms the power transform documented
    for rho_b in the B horizon (Table 3). Equivalent to Y^(1/2.4488).

    R2 = 0.33, NSE = 0.27, RMSE = 0.18 g/cm3, Bias = 0.01

    B horizon rather than A: sigma_pc below is calibrated on subsoil just
    under the plough layer. Quebec A-horizon densities (0.95-1.3 Mg/m3,
    driven by high organic matter) fall below that calibration range and
    drive sigma_pc to implausible values near zero.

    Args:
        silt_pct: silt (%)
        clay_pct: clay (%)
        oc_pct:   organic carbon (%)

    Returns:
        Bulk density (Mg/m3).
    """
    Y = (-0.6911
         + 0.0165 * silt_pct
         - 2.2053 * (clay_pct ** 0.1248)
         + 5.3959 * (oc_pct ** -0.0874))
    if Y <= 0:
        raise ValueError(
            f"Perreault B-horizon PTF returned a non-positive intermediate "
            f"({Y:.4f}) for silt={silt_pct}, clay={clay_pct}, OC={oc_pct}. "
            f"Inputs are outside the calibration range."
        )
    return Y ** (1 / 2.4488)


def bulk_density_quebec_A(clay_pct: float, oc_pct: float) -> float:
    """
    Bulk density, A HORIZON (topsoil). Perreault et al. (2022) Table A1:

        rho_b = -0.0478*C^0.4072 - 0.5903*OC^0.2750 + 2.1906

    R2 = 0.28, NSE = 0.16, RMSE = 0.15 g/cm3, Bias = 0.00
    No transformation is applied to rho_b in the A horizon (Table 3).

    Provided for completeness. NOT used for sigma_pc - see the note in
    bulk_density_quebec_B.
    """
    return -0.0478 * (clay_pct ** 0.4072) - 0.5903 * (oc_pct ** 0.2750) + 2.1906


# =============================================================
# PART 3 - Precompression stress (sigma_pc)
#
# soilphysics v5.0, R/soilStrength2.R line 7, then lines 9-13:
#     out <- -26.51 + (25.57*BD) - (20.40*clay) + (10.26*clay*pF)
#     for (j in 1:length(out)) { if (out[j] < 0) {out[j] <- 0} }
#     return(out^2)
# SHA-256 7F7200EFCAE286CCF73719923134710D40DDE871B1CA4672F37BE1D3F18915B3
#
# The package attributes the model to Schjonning & Lamande (2018),
# which has not been read.
# =============================================================

def precompression_stress(bulk_density_Mg_m3: float,
                          clay_fraction: float,
                          matric_suction_hPa: float) -> float:
    """
    Precompression stress (sigma_pc), kPa.

    UNITS - read carefully:
        bulk_density_Mg_m3  Mg/m3 (= g/cm3)   man/soilStrength2.Rd:17
        matric_suction_hPa  hPa; 1 kPa = 10 hPa  man/soilStrength2.Rd:16
        clay_fraction       FRACTION 0-1, NOT a percentage

    On the clay unit. man/soilStrength2.Rd line 15 documents clay.content
    as a percentage, but line 48 of the same file passes clay.content=0.3
    in its worked example. The documentation is wrong. The clay terms
    reduce to clay * (-20.40 + 10.26*pF), so a percentage scales that
    contribution 100-fold: a 50% clay soil at pF 3 would return
    279,088 kPa - harder than concrete. As a fraction the same soil
    returns 210 kPa. Fraction is the only physically possible reading.

    Note that soilStrength() in the same package - the Severiano (2013)
    model - branches on clay.content > 52, i.e. it uses a PERCENTAGE.
    The two functions differ.

    Behaviour: the clay terms cancel at pF = 20.40/10.26 = 1.988. Below
    that suction clay reduces strength, above it clay increases strength.

    Calibration: European arable subsoil. The package example sweeps
    suction 60-1000 hPa (pF 1.78-3.0); outside that range is extrapolation.

    Returns:
        sigma_pc (kPa). Returns 0.0 where the model truncates, which
        signals that the inputs are outside the calibration range.
    """
    if matric_suction_hPa <= 0:
        raise ValueError("matric_suction_hPa must be > 0")
    if not 0.0 <= clay_fraction <= 1.0:
        raise ValueError(
            f"clay_fraction must be a fraction 0-1, not a percentage. "
            f"Got {clay_fraction}."
        )

    pF = math.log10(matric_suction_hPa)
    out = (-26.51
           + 25.57 * bulk_density_Mg_m3
           - 20.40 * clay_fraction
           + 10.26 * clay_fraction * pF)
    if out < 0:
        out = 0.0
    return out ** 2


# =============================================================
# PART 4 - Risk bands
#
# soilphysics v5.0, R/soilStrength.R lines 76-77:
#     pcs05 <- pcs*0.5
#     pcs11 <- pcs*1.1
# SHA-256 832AE88DECFFB96E07A7480451A776991AAD1949D03083966883196EE2ADC21A
#
# man/soilStrength.Rd lines 25-26 document both as "the lower/upper limit
# of precompression stress according to the Terranimo model criteria
# (see Stettler et al. 2014)".
# SHA-256 63AECFE224611731A77C571CD6A10BC551727855684ABDF10FB37B5FDF4AA42E
#
# Stettler et al. (2014) has not been read.
#
# The multipliers are defined inside soilStrength() (Severiano 2013), not
# soilStrength2(). The .Rd presents them as a general Terranimo criterion
# rather than one tied to a particular sigma_pc model, which is why they
# are applied here to the Schjonning & Lamande sigma_pc.
# =============================================================

def compaction_risk(sigma_act_kPa: float, sigma_pc_kPa: float) -> dict:
    """
    GREEN   sigma_act <  0.5 * sigma_pc
    YELLOW  0.5*sigma_pc <= sigma_act <= 1.1 * sigma_pc
    RED     sigma_act >  1.1 * sigma_pc
    """
    if sigma_pc_kPa <= 0:
        return {
            "risk": "UNDEFINED",
            "color": "GREY",
            "ratio": None,
            "sigma_act": round(sigma_act_kPa, 1),
            "sigma_pc": 0.0,
            "LL_Pc": None,
            "UL_Pc": None,
            "recommendation": ("sigma_pc truncated to zero: inputs outside "
                               "the calibration range of the PTF. No "
                               "classification possible."),
            "can_enter_field": False,
        }

    ll = 0.5 * sigma_pc_kPa
    ul = 1.1 * sigma_pc_kPa

    if sigma_act_kPa < ll:
        risk, colour, ok = "LOW", "GREEN", True
        msg = "Below the lower Terranimo limit."
    elif sigma_act_kPa <= ul:
        risk, colour, ok = "MODERATE", "YELLOW", False
        msg = ("Between the Terranimo limits. Consider lighter machinery "
               "or drier conditions.")
    else:
        risk, colour, ok = "HIGH", "RED", False
        msg = "Above the upper Terranimo limit."

    return {
        "risk": risk,
        "color": colour,
        "ratio": round(sigma_act_kPa / sigma_pc_kPa, 3),
        "sigma_act": round(sigma_act_kPa, 1),
        "sigma_pc": round(sigma_pc_kPa, 1),
        "LL_Pc": round(ll, 1),
        "UL_Pc": round(ul, 1),
        "recommendation": msg,
        "can_enter_field": ok,
    }


# =============================================================
# PART 5 - Full evaluation
# =============================================================

def evaluate_compaction_risk(
    # machinery
    static_rear_weight_kN: float,
    traction_force_kN: float,
    hitch_height_m: float,
    wheelbase_m: float,
    # tyre
    total_diameter_m: float,
    static_load_radius_m: float,
    section_width_m: float,
    inflation_pressure_kPa: float,
    tire_load_kN: float,
    n_wheels_per_axle: int,
    # soil, B horizon
    silt_pct: float,
    clay_pct: float,
    organic_matter_pct: float,
    matric_suction_hPa: float,
) -> dict:
    """
    Runs the full chain. All soil inputs refer to the B horizon.
    """
    axle_load = dynamic_rear_weight(
        static_rear_weight_kN, traction_force_kN,
        hitch_height_m, wheelbase_m,
    )

    area_geo = contact_area_geometric(
        total_diameter_m, static_load_radius_m, section_width_m)
    area_exp = contact_area_experimental(
        static_load_radius_m, section_width_m,
        tire_load_kN, inflation_pressure_kPa)
    area_used = min(area_geo, area_exp)

    sigma_act = applied_stress(axle_load, area_used, n_wheels_per_axle)

    oc_pct = organic_carbon_from_om(organic_matter_pct)
    bd = bulk_density_quebec_B(silt_pct, clay_pct, oc_pct)
    sigma_pc = precompression_stress(bd, clay_pct / 100.0, matric_suction_hPa)

    result = compaction_risk(sigma_act, sigma_pc)
    result.update({
        "axle_load_kN": round(axle_load, 2),
        "contact_area_geometric_m2": round(area_geo, 4),
        "contact_area_experimental_m2": round(area_exp, 4),
        "contact_area_used_m2": round(area_used, 4),
        "bulk_density_Mg_m3": round(bd, 3),
        "organic_carbon_pct": round(oc_pct, 2),
        "matric_suction_hPa": matric_suction_hPa,
    })
    return result


if __name__ == "__main__":
    print(__doc__)
    print("No worked example is included.")
    print()
    print("Verified machinery parameters are not available. Required:")
    print("  - Nebraska Tractor Test Lab report: static axle weights,")
    print("    wheelbase, drawbar height, draft force")
    print("  - Tyre catalogue: total diameter, static loaded radius,")
    print("    section width, inflation pressure")
    print()
    print("Verified Quebec B-horizon soil properties are also not available.")
    print("RT-08 (ref_soil_series_quebec) holds surface texture only;")
    print("sigma_pc needs subsoil clay, silt and organic carbon.")
