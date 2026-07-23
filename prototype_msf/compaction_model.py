"""
Soil Compaction Model for MSF Expert System
Based on:
- Carranza-Díaz et al. (UNAL) — contact area + applied stress (sigma_act)
- Stettler et al. 2014, Landtechnik 69(3):132-138 — precompression stress (sigma_pc)
- Grečenko 1995 — tire contact area equations
"""

import math

# ─────────────────────────────────────────────
# PART 1 — Applied stress (sigma_act)
# Source: Carranza-Díaz et al., UNAL
# ─────────────────────────────────────────────

def dynamic_rear_weight(
    static_rear_weight_kN: float,
    static_front_weight_kN: float,
    traction_force_kN: float,
    hitch_height_m: float,
    wheelbase_m: float,
    implement_angle_deg: float = 0.0
) -> float:
    """
    Calculate dynamic rear wheel load (PDD_trasero).
    Equation 1b from Carranza-Díaz et al.

    Args:
        static_rear_weight_kN: Static rear axle weight (kN)
        static_front_weight_kN: Static front axle weight (kN)
        traction_force_kN: Implement traction force (kN)
        hitch_height_m: Hitch bar height from ground (m)
        wheelbase_m: Distance between front and rear axles (m)
        implement_angle_deg: Implement angle with horizontal (degrees)

    Returns:
        Dynamic rear wheel load (kN)
    """
    theta = math.radians(implement_angle_deg)
    # Moment equilibrium at front axle contact point
    # PDT = PET + (FT * cos(θ) * H) / DE
    dynamic_rear = (static_rear_weight_kN +
                   (traction_force_kN * math.cos(theta) * hitch_height_m) / wheelbase_m)
    return dynamic_rear


def contact_area_geometric(
    total_diameter_m: float,
    static_load_radius_m: float,
    section_width_m: float,
    C1: float = 1.65
) -> float:
    """
    Nominal geometric contact area (Grečenko 1989, eq. 2).
    A_oj = C1 * sqrt((dk - 2*rs) * bk * rs)

    Args:
        total_diameter_m: Total tire diameter dk (m)
        static_load_radius_m: Static loaded radius rs (m)
        section_width_m: Section width bk (m)
        C1: Coefficient for agricultural traction wheels (default 1.65)

    Returns:
        Nominal geometric contact area (m²)
    """
    deflection = total_diameter_m - 2 * static_load_radius_m
    return C1 * math.sqrt(deflection * section_width_m * static_load_radius_m)


def contact_area_experimental(
    static_load_radius_m: float,
    section_width_m: float,
    tire_load_kN: float,
    inflation_pressure_kPa: float
) -> float:
    """
    Nominal experimental contact area (Sitkei & Söhne 1969, cited by Grečenko 1995, eq. 3).
    Based on dimensional analysis.

    Args:
        static_load_radius_m: Static loaded radius rs (m)
        section_width_m: Section width bk (m)
        tire_load_kN: Load on tire Wj (kN)
        inflation_pressure_kPa: Tire inflation pressure p (kPa)

    Returns:
        Nominal experimental contact area (m²)
    """
    # Dimensionless ratio W/(p * rs * bk)
    ratio = tire_load_kN / (inflation_pressure_kPa * static_load_radius_m * section_width_m)
    return static_load_radius_m * section_width_m * ratio


def applied_stress(
    dynamic_rear_weight_kN: float,
    contact_area_m2: float,
    correction_factor: float = 0.87
) -> float:
    """
    Applied stress to soil (sigma_act) in kPa.
    sigma_act = F / (A * alpha_w)

    Args:
        dynamic_rear_weight_kN: Dynamic rear wheel load (kN)
        contact_area_m2: Nominal contact area (m²)
        correction_factor: Area correction factor alpha_w (0.87-0.99, default 0.87 = conservative)

    Returns:
        Applied stress sigma_act (kPa)
    """
    corrected_area = contact_area_m2 * correction_factor
    force_kN_per_wheel = dynamic_rear_weight_kN / 2  # per wheel (rear axle has 2 wheels)
    return force_kN_per_wheel / corrected_area  # kPa = kN/m²


# ─────────────────────────────────────────────
# PART 2 — Precompression stress (sigma_pc)
# Source: Stettler et al. 2014, Landtechnik 69(3):132-138
# ─────────────────────────────────────────────

def precompression_stress(
    clay_content_pct: float,
    matric_potential_kPa: float
) -> float:
    """
    Soil precompression stress (sigma_pc) in kPa.
    Based on Stettler et al. 2014 pedotransfer function.
    sigma_pc = f(clay%, matric_potential)

    Reference equation form (Keller et al. 2011, cited in Stettler 2014):
    log(sigma_pc) = a + b * log(|matric_potential|) + c * clay_content

    Coefficients from Keller et al. 2011 (valid for mineral soils):
    a = 0.9, b = 0.3, c = 0.009

    Args:
        clay_content_pct: Clay content (%)
        matric_potential_kPa: Soil matric potential (kPa, negative = dry, use absolute value)

    Returns:
        Precompression stress sigma_pc (kPa)
    """
    # Use absolute value of matric potential
    psi = abs(matric_potential_kPa)
    if psi <= 0:
        psi = 1  # avoid log(0)

    # Pedotransfer function (Keller et al. 2011)
    log_sigma_pc = 0.9 + 0.3 * math.log10(psi) + 0.009 * clay_content_pct
    return 10 ** log_sigma_pc


# ─────────────────────────────────────────────
# PART 3 — Risk classification (Terranimo logic)
# Source: Stettler et al. 2014
# ─────────────────────────────────────────────

def compaction_risk(sigma_act_kPa: float, sigma_pc_kPa: float) -> dict:
    """
    Classify compaction risk by comparing applied stress vs precompression stress.
    Terranimo traffic light system (Stettler et al. 2014):

    GREEN:  sigma_act < sigma_pc           → No permanent compaction
    YELLOW: sigma_pc < sigma_act < 1.5*sigma_pc → Moderate risk
    RED:    sigma_act > 1.5 * sigma_pc     → Irreversible compaction

    Args:
        sigma_act_kPa: Applied stress from machinery (kPa)
        sigma_pc_kPa: Precompression stress of soil (kPa)

    Returns:
        dict with risk level, color, ratio, and recommendation
    """
    ratio = sigma_act_kPa / sigma_pc_kPa

    if ratio < 1.0:
        return {
            "risk": "LOW",
            "color": "GREEN",
            "ratio": round(ratio, 3),
            "sigma_act": round(sigma_act_kPa, 1),
            "sigma_pc": round(sigma_pc_kPa, 1),
            "recommendation": "Safe to traffic. No permanent compaction expected.",
            "can_enter_field": True
        }
    elif ratio < 1.5:
        return {
            "risk": "MODERATE",
            "color": "YELLOW",
            "ratio": round(ratio, 3),
            "sigma_act": round(sigma_act_kPa, 1),
            "sigma_pc": round(sigma_pc_kPa, 1),
            "recommendation": "Moderate compaction risk. Consider lighter machinery or waiting for drier conditions.",
            "can_enter_field": False
        }
    else:
        return {
            "risk": "HIGH",
            "color": "RED",
            "ratio": round(ratio, 3),
            "sigma_act": round(sigma_act_kPa, 1),
            "sigma_pc": round(sigma_pc_kPa, 1),
            "recommendation": "Irreversible compaction risk. Do NOT traffic the field.",
            "can_enter_field": False
        }


# ─────────────────────────────────────────────
# PART 4 — Main expert system call
# ─────────────────────────────────────────────

def evaluate_compaction_risk(
    # Machinery inputs (from MSF or user)
    static_rear_weight_kN: float,
    static_front_weight_kN: float,
    traction_force_kN: float,
    hitch_height_m: float,
    wheelbase_m: float,
    # Tire inputs (from Nebraska test / catalog)
    total_diameter_m: float,
    static_load_radius_m: float,
    section_width_m: float,
    inflation_pressure_kPa: float,
    tire_load_kN: float,
    # Soil inputs (from Open-Meteo + Soil Canada/IRDA)
    clay_content_pct: float,
    matric_potential_kPa: float,
    # Optional
    implement_angle_deg: float = 0.0,
) -> dict:
    """
    Full compaction risk evaluation for the MSF Expert System.
    Combines Carranza-Díaz et al. (sigma_act) + Stettler et al. 2014 (sigma_pc).

    Returns complete risk assessment dictionary.
    """
    # Step 1: Dynamic rear wheel load
    rear_load = dynamic_rear_weight(
        static_rear_weight_kN, static_front_weight_kN,
        traction_force_kN, hitch_height_m, wheelbase_m, implement_angle_deg
    )

    # Step 2: Contact area (use geometric method, conservative)
    area_geo = contact_area_geometric(total_diameter_m, static_load_radius_m, section_width_m)
    area_exp = contact_area_experimental(static_load_radius_m, section_width_m, tire_load_kN, inflation_pressure_kPa)
    area_used = min(area_geo, area_exp)  # conservative: smaller area = higher stress

    # Step 3: Applied stress
    sigma_act = applied_stress(rear_load, area_used)

    # Step 4: Precompression stress
    sigma_pc = precompression_stress(clay_content_pct, matric_potential_kPa)

    # Step 5: Risk classification
    result = compaction_risk(sigma_act, sigma_pc)
    result["rear_dynamic_load_kN"] = round(rear_load, 2)
    result["contact_area_m2"] = round(area_used, 4)

    return result


# ─────────────────────────────────────────────
# TEST — Massey Ferguson 243 (from Carranza-Díaz et al.)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== MSF Expert System — Compaction Risk Model ===")
    print("Based on: Carranza-Díaz et al. (UNAL) + Stettler et al. 2014")
    print()

    # Test case: Massey Ferguson 243 from the original paper
    # Soil: wet clay (Quebec spring conditions)
    result = evaluate_compaction_risk(
        # Machinery — Massey Ferguson 243
        static_rear_weight_kN=21.3,
        static_front_weight_kN=12.7,
        traction_force_kN=8.0,
        hitch_height_m=0.45,
        wheelbase_m=2.15,
        # Tires — Goodyear catalog (from paper)
        total_diameter_m=1.35,
        static_load_radius_m=0.58,
        section_width_m=0.38,
        inflation_pressure_kPa=120.0,
        tire_load_kN=17.2,
        # Soil — wet clay Quebec spring (high risk scenario)
        clay_content_pct=35.0,
        matric_potential_kPa=10.0,  # wet soil
        implement_angle_deg=0.0,
    )

    print(f"Applied stress (σ_act):        {result['sigma_act']} kPa")
    print(f"Precompression stress (σ_pc):  {result['sigma_pc']} kPa")
    print(f"Ratio σ_act/σ_pc:             {result['ratio']}")
    print(f"Risk level:                    {result['color']} — {result['risk']}")
    print(f"Can enter field:               {result['can_enter_field']}")
    print(f"Recommendation:                {result['recommendation']}")
    print()

    # Test 2: Same machinery, dry soil (low risk)
    result_dry = evaluate_compaction_risk(
        static_rear_weight_kN=21.3,
        static_front_weight_kN=12.7,
        traction_force_kN=8.0,
        hitch_height_m=0.45,
        wheelbase_m=2.15,
        total_diameter_m=1.35,
        static_load_radius_m=0.58,
        section_width_m=0.38,
        inflation_pressure_kPa=120.0,
        tire_load_kN=17.2,
        # Dry soil
        clay_content_pct=35.0,
        matric_potential_kPa=100.0,  # dry soil
    )

    print("--- Dry soil scenario ---")
    print(f"Applied stress (σ_act):        {result_dry['sigma_act']} kPa")
    print(f"Precompression stress (σ_pc):  {result_dry['sigma_pc']} kPa")
    print(f"Risk level:                    {result_dry['color']} — {result_dry['risk']}")
    print(f"Can enter field:               {result_dry['can_enter_field']}")
