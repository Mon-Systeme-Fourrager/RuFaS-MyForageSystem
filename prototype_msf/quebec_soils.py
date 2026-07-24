"""
Quebec Soil Profiles Database
Source: Michaud, A.R., M.A. Niang, A. Blais-Gagnon, W. Huertas (2020).
        Caracterisation hydrologique des cours d'eau de Saint-Zotique.
        Rapport final. IRDA. Tableau 5.

A craaq_group field (G1/G2/G3) was removed on 2026-07-24. It had been
assigned using clay-content thresholds that were not taken from any
CRAAQ publication. The same correction was applied to RT-08 in Supabase.

Python mirror of RT-08 (public.ref_soil_series_quebec in Supabase).
Used by compaction_model.py and integrated_decision.py for sigma_pc calculation.

Hydrologic groups (A-D) follow USDA-SCS classification:
  A = low runoff potential (sandy, high infiltration)
  D = high runoff potential (clayey, low infiltration)

CRAAQ groups (G1/G2/G3) used by RT-07 CENtotal coefficients:
  G1 = clay soils (>30% clay)
  G2 = loam soils (15-30% clay)
  G3 = sandy soils (<15% clay)
"""

QUEBEC_SOILS = {
    "shefford_loam_graveleux": {
        "name_fr": "Shefford loam graveleux",
        "name_en": "Shefford gravelly loam",
        "hydrologic_group": "B",
        "clay_pct": 13.0,
        "silt_pct": 41.0,
        "sand_pct": 46.0,
        "very_fine_sand_pct": 13.0,
        "organic_matter_pct": 16.8,
        "permeability_code": 3,
        "structure_code": 2,
        "erodibility_factor": 0.03385,
        "natural_p_mg_kg": 1392,
        "area_ha": 693.26,
    },
    "sainte_rosalie_loam_argileux": {
        "name_fr": "Sainte-Rosalie loam argileux",
        "name_en": "Sainte-Rosalie clay loam",
        "hydrologic_group": "C",
        "clay_pct": 32.0,
        "silt_pct": 37.0,
        "sand_pct": 30.0,
        "very_fine_sand_pct": 7.0,
        "organic_matter_pct": 7.0,
        "permeability_code": 5,
        "structure_code": 4,
        "erodibility_factor": 0.03532,
        "natural_p_mg_kg": 803,
        "area_ha": 561.62,
    },
    "sorel_sable": {
        "name_fr": "Sorel sable",
        "name_en": "Sorel sand",
        "hydrologic_group": "A",
        "clay_pct": 3.0,
        "silt_pct": 7.0,
        "sand_pct": 91.0,
        "very_fine_sand_pct": 10.0,
        "organic_matter_pct": 2.1,
        "permeability_code": 3,
        "structure_code": 1,
        "erodibility_factor": 0.00835,
        "natural_p_mg_kg": 537,
        "area_ha": 462.24,
    },
    "saint_zotique_loam_sableux": {
        "name_fr": "Saint-Zotique loam sableux",
        "name_en": "Saint-Zotique sandy loam",
        "hydrologic_group": "D",
        "clay_pct": 10.0,
        "silt_pct": 31.0,
        "sand_pct": 59.0,
        "very_fine_sand_pct": 30.0,
        "organic_matter_pct": 10.1,
        "permeability_code": 3,
        "structure_code": 2,
        "erodibility_factor": 0.04057,
        "natural_p_mg_kg": 779,
        "area_ha": 216.41,
    },
    "soulanges_loam_sableux": {
        "name_fr": "Soulanges loam sableux",
        "name_en": "Soulanges sandy loam",
        "hydrologic_group": "C",
        "clay_pct": 7.0,
        "silt_pct": 33.0,
        "sand_pct": 60.0,
        "very_fine_sand_pct": 37.0,
        "organic_matter_pct": 5.5,
        "permeability_code": 3,
        "structure_code": 2,
        "erodibility_factor": 0.0492,
        "natural_p_mg_kg": 847,
        "area_ha": 198.17,
    },
    "sainte_rosalie_argile": {
        "name_fr": "Sainte-Rosalie argile",
        "name_en": "Sainte-Rosalie clay",
        "hydrologic_group": "C",
        "clay_pct": 45.0,
        "silt_pct": 27.0,
        "sand_pct": 28.0,
        "very_fine_sand_pct": 7.0,
        "organic_matter_pct": 6.4,
        "permeability_code": 5,
        "structure_code": 4,
        "erodibility_factor": 0.02699,
        "natural_p_mg_kg": 803,
        "area_ha": 178.43,
    },
    "courval_loam_sableux": {
        "name_fr": "Courval loam sableux",
        "name_en": "Courval sandy loam",
        "hydrologic_group": "C",
        "clay_pct": 13.0,
        "silt_pct": 16.0,
        "sand_pct": 70.0,
        "very_fine_sand_pct": 24.0,
        "organic_matter_pct": 4.5,
        "permeability_code": 3,
        "structure_code": 2,
        "erodibility_factor": 0.02378,
        "natural_p_mg_kg": 503,
        "area_ha": 95.50,
    },
    "saint_amable_sable": {
        "name_fr": "Saint-Amable sable",
        "name_en": "Saint-Amable sand",
        "hydrologic_group": "C",
        "clay_pct": 3.0,
        "silt_pct": 7.0,
        "sand_pct": 90.0,
        "very_fine_sand_pct": 15.0,
        "organic_matter_pct": 4.8,
        "permeability_code": 4,
        "structure_code": 1,
        "erodibility_factor": 0.01283,
        "natural_p_mg_kg": 447,
        "area_ha": 61.94,
    },
    "beaudette_loam_limoneux": {
        "name_fr": "Beaudette loam limoneux",
        "name_en": "Beaudette silt loam",
        "hydrologic_group": "C",
        "clay_pct": 18.0,
        "silt_pct": 56.0,
        "sand_pct": 26.0,
        "very_fine_sand_pct": 15.0,
        "organic_matter_pct": 6.0,
        "permeability_code": 4,
        "structure_code": 3,
        "erodibility_factor": 0.04991,
        "natural_p_mg_kg": 489,
        "area_ha": 27.07,
    },
    "saint_bernard_loam_sableux": {
        "name_fr": "Saint-Bernard loam sableux",
        "name_en": "Saint-Bernard sandy loam",
        "hydrologic_group": "B",
        "clay_pct": 12.0,
        "silt_pct": 27.0,
        "sand_pct": 61.0,
        "very_fine_sand_pct": 19.0,
        "organic_matter_pct": 10.3,
        "permeability_code": 4,
        "structure_code": 2,
        "erodibility_factor": 0.03196,
        "natural_p_mg_kg": 923,
        "area_ha": 22.33,
    },
    "saint_urbain_argile": {
        "name_fr": "Saint-Urbain argile",
        "name_en": "Saint-Urbain clay",
        "hydrologic_group": "B",
        "clay_pct": 47.0,
        "silt_pct": 31.0,
        "sand_pct": 21.0,
        "very_fine_sand_pct": 3.0,
        "organic_matter_pct": 6.6,
        "permeability_code": 3,
        "structure_code": 4,
        "erodibility_factor": 0.01988,
        "natural_p_mg_kg": 726,
        "area_ha": 15.57,
    },
}


def get_craaq_group(clay_pct: float) -> str:
    """
    Not implemented.

    An earlier version assigned CRAAQ soil groups using clay thresholds
    (>30% G1, 15-30% G2, <15% G3). Those thresholds were not taken from
    any CRAAQ publication and have been removed. The same correction was
    applied to RT-08 in Supabase (ref_soil_series_quebec.craaq_group is
    now NULL).

    The CRAAQ group is needed to select CENtotal coefficients in RT-07.
    Obtain the official definition from CRAAQ before reimplementing.
    """
    raise NotImplementedError(
        "CRAAQ soil group thresholds are not available from a cited source. "
        "See the docstring."
    )


def get_soil(soil_key: str) -> dict:
    """Retrieve a Quebec soil profile by key."""
    if soil_key not in QUEBEC_SOILS:
        available = ", ".join(QUEBEC_SOILS.keys())
        raise KeyError(f"Unknown soil '{soil_key}'. Available: {available}")
    return QUEBEC_SOILS[soil_key].copy()


def list_soils_by_clay() -> list:
    """List all soils sorted by clay content (highest first)."""
    return sorted(
        [(k, v["name_fr"], v["clay_pct"])
         for k, v in QUEBEC_SOILS.items()],
        key=lambda x: x[2],
        reverse=True
    )


if __name__ == "__main__":
    print("=" * 75)
    print("QUEBEC SOIL PROFILES - Michaud et al. 2020 (IRDA)")
    print("Python mirror of RT-08 (public.ref_soil_series_quebec)")
    print("=" * 75)
    print()
    print(f"{'Soil series':<32} {'Clay %':<8} {'Hydro':<7} {'Area (ha)':<10}")
    print("-" * 75)
    for key, name, clay in list_soils_by_clay():
        soil = QUEBEC_SOILS[key]
        print(f"{name:<32} {clay:<8.1f} {soil['hydrologic_group']:<7} {soil['area_ha']:<10.2f}")
    print("-" * 75)
    print()
    print("Hydrologic groups: A = low runoff, D = high runoff (USDA-SCS)")
