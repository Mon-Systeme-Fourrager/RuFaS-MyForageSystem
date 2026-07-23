# MSF Expert System — RUFAS Prototype

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
- **Compaction:** Carranza-Díaz et al. (UNAL) for σ_act + Keller et al. 2011 for σ_pc

## References

- Stettler et al. (2014). Terranimo® — a web-based tool for evaluating soil compaction. *Landtechnik* 69(3):132-138
- Vadas & Powell (2013). SurPhos model. *Geoderma* 206:24-32
- Neitsch et al. (2011). SWAT Theoretical Documentation
- Parton et al. (1987). CENTURY model. *Soil Sci. Soc. Am. J.* 51:1173-1179
- Del Prado et al. (2011). SIMSDAIRY framework. *Sci. Total Environ.*

## Status

Research prototype — not production code. This branch is not intended for merge
into `dev-msf`.
