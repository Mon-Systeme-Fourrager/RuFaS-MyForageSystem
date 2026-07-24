# MSF Expert System — RUFAS Prototype

> **STATUS: research prototype with known unverified inputs.**
> Several model parameters are fabricated placeholders and are marked with
> `TODO:` in the source. See "Known limitations" below before citing any
> number from this work.

Research prototype for the manure application timing decision layer of the
Mon Système Fourrager (MSF) Expert System.

**Scientific question:** How to use multi-agroclimatic model integration to answer
questions about the right moment to apply manure, considering slope and
environmental conditions?

## What this is

RUFAS is a forward simulator — it computes what happens agronomically when manure
is applied on a given day, but it does not decide *when* to apply. This prototype
demonstrates the decision layer that closes that gap.

## Setup

Requires Python 3.12 + RUFAS installed as editable package:

```bash
conda create -n rufas python=3.12 -c conda-forge -y
conda activate rufas
pip install -e . -c constraints-release.txt
```

## Key scripts

| Script | What it does |
|---|---|
| `run_prototype.py` | Single RUFAS run — baseline manure application |
| `run_sweep.py` | Delay sweep 0-4 days, single weather year |
| `run_multiyr_sweep.py` | Full sweep: 5 delays × 6 weather years = 30 simulations |
| `analyze_multiyr.py` | Analysis + plot generation for multi-year sweep |
| `compaction_model.py` | Soil compaction risk (Carranza-Díaz et al. + Stettler et al. 2014) |
| `realtime_recommendation.py` | Live Open-Meteo forecast → RUFAS → recommendation |
| `verify_depth.py` | Verifies RUFAS records application depth correctly |

## Key findings

**1. Optimal delay is not fixed — it depends on rain timing**

Multi-year sweep (6 weather years, 30 simulations) shows the optimal delay varies
from 0 to 4 days depending on when the next significant rain event occurs. A fixed
"delay N days" rule would be wrong 5 years out of 6.

**Weather caveat:** these runs use `example_temperate_weather.csv`, the
generic temperate dataset shipped with RUFAS (simulation config uses
`FIPS_county_code: 55025` = Dane County, Wisconsin). **This is not Quebec
weather.** The years labelled 2003/2013/2020 etc. are years in that dataset,
not Quebec years. Conclusions about how the optimum shifts with rain timing
are about the *mechanism*; the specific day numbers do not transfer to Quebec.

| Year | Precip (mm) | First rain | Optimal delay |
|---|---|---|---|
| 2003 | 40 | day 202 | 0 days |
| 2013 | 87 | day 203 | 1 day |
| 2002 | 127 | day 202 | 4 days |
| 2010 | 247 | day 203 | 3 days |
| 2007 | 333 | day 208 | 4 days |
| 2020 | 30 | day 204 | 4 days |

**General rule:** apply the day AFTER the next significant rain event.

**2. The decision curve is non-monotonic**

Three metrics, three different optima (2013 weather year):
- Minimize runoff → delay 1 day (−44% vs applying today)
- Maximize available N → delay 2 days (+1.9%)
- Maximize root-zone N → delay 3 days (+17.8%)

The expert system must reason about a Pareto frontier, not a single optimum.

**3. RUFAS cannot model injection vs broadcast**

Injection at 30mm depth produces +52% MORE nitrate runoff than surface broadcast
in RUFAS — the opposite of empirical evidence. Root cause: the SCS-CN runoff model
uses top-layer N concentration, and 30mm falls inside RUFAS's layer 0. RUFAS treats
injected N identically to surface-applied N for runoff purposes.

**Implication:** RUFAS handles timing decisions correctly but cannot handle
application method decisions. An external model (ODEP, Terranimo) is required for
that dimension. This finding scientifically justifies the multi-model integration
approach.

## Data sources

- **Weather:** Open-Meteo API (real-time) + RUFAS example weather CSV (historical validation)
- **Manure composition (RT-06):** CRAAQ Guide de référence en fertilisation, Chapitre 10
- **N availability (RT-07):** CRAAQ CEFM/CEFO/CENtotal coefficients
- **Compaction:** functional form of the sigma_pc PTF is standard in the literature (see compaction_model.py docstring); the specific coefficients used are fabricated placeholders. See "Known limitations" below.

## References

- Stettler et al. (2014). Terranimo® — a web-based tool for evaluating soil compaction. *Landtechnik* 69(3):132-138
- Vadas & Powell (2013). SurPhos model. *Geoderma* 206:24-32
- Neitsch et al. (2011). SWAT Theoretical Documentation
- Parton et al. (1987). CENTURY model. *Soil Sci. Soc. Am. J.* 51:1173-1179
- Del Prado et al. (2011). SIMSDAIRY framework. *Sci. Total Environ.*

## Known limitations

| Item | Status |
|---|---|
| Weather data | Generic temperate dataset shipped with RUFAS (`FIPS_county_code: 55025` = Dane County, Wisconsin). NOT Quebec. |
| Machinery parameters | None included. Nebraska Tractor Test Lab and tyre catalogue inputs are needed before any worked example. |
| Quebec B-horizon soil properties | Not available. RT-08 holds surface texture only; sigma_pc needs subsoil clay, silt and organic carbon. |
| Schjonning & Lamande (2018) | Not read. The sigma_pc coefficients are verified against the soilphysics package source instead. |
| Stettler et al. (2014) | Not read. The 0.5 / 1.1 bands are verified against the package source and its documentation. |

## Verified sources

Verified means the source was read directly. Hashes are of the files as
downloaded on 2026-07-24.

| Source | How verified |
|---|---|
| RUFAS simulation outputs | Computed by RUFAS |
| RUFAS source-code findings | Files read directly |
| `quebec_soils.py` — 11 soil series | Michaud, A.R., M.A. Niang, A. Blais-Gagnon, W. Huertas (2020). *Caracterisation hydrologique des cours d'eau de Saint-Zotique*. IRDA. Tableau 5. PDF read. |
| Bulk density PTFs (A and B horizon) | Perreault, S., El Alem, A., Chokmani, K., Cambouris, A.N. (2022). *Agronomy* 12(2):526, Tables A1-A3. PDF read. |
| sigma_act — dynamic axle load | Carranza-Diaz, A.K. et al., Universidad Nacional de Colombia. Paper read. |
| sigma_act — contact area | Grecenko, A. (1995). *J. Terramechanics* 32(6):325-333, via the above. |
| sigma_pc coefficients | `soilphysics` v5.0 (GPL-2), `R/soilStrength2.R` line 7. SHA-256 `7F7200EF...15B3` |
| Risk bands 0.5 / 1.1 | `soilphysics` v5.0, `R/soilStrength.R` lines 76-77. SHA-256 `832AE88D...C21A` |
| Terranimo attribution of the bands | `man/soilStrength.Rd` lines 25-26. SHA-256 `63AECFE2...A42E` |
| Input units (Mg/m3, hPa) | `man/soilStrength2.Rd` lines 16-17. SHA-256 `C4BC2E07...FD1D` |
| Package version and licence | `DESCRIPTION`. SHA-256 `BC9219AD...1063` |

## Status

Research prototype — not production code. This branch is not intended for merge
into `dev-msf`.
