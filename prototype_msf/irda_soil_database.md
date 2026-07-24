# IRDA Quebec soil database - reference note

Identified 2026-07-25 via Catherine Bosse (IRDA). Not integrated.

Source: https://irda.qc.ca/fr/outils/donnees-pedologiques-sols/donnees-pedologiques/cartes-pedologiques-quebec-irda/
Guide: irda-donneesgeospatialescouverturepedologiquequebec-guide-mars2026.pdf
SHA-256 4C2C33986F2F9F92CA192F86E5E845F5C6987A4425C2ED82738745EE15AC7312
68 pages, read 2026-07-25.

## Structure

Three related tables, per the guide's acronym list (lines 119-123):

  BDS   Base de Donnees des Sols du Quebec - contains PPC and PPSD
  PPC   Proprietes Physico-Chimiques, PAR COUCHE DE SOL (per horizon)
  PPSD  Proprietes Pedologiques du Sol Dominant
  FCS   former Fichier des Couches de sol, replaced by PPC

## Fields confirmed present in PPC (verbatim from the guide)

  Horizon              nom de l'horizon (Ap1, Ap2, B)
  Argile               % argile
  Limon                % limon
  Sable                % sable
  SableTresGros/Gros/Moyen/Fin/TresFin   sand fractions
  MOS                  teneur en matiere organique, facteur 1,724
  MO_predite           teneur en matiere organique predite
  ProfondeurLimiteInf  profondeur de la limite inferieure des horizons
  Imputation_SableTF   flag: very fine sand imputed

Coverage: 160 soil series with analytical data, plus 71 more in the
PPC-EESSAQ dataset.

## Not found in the guide's field lists

  Bulk density (densite apparente) - appears only in narrative text about
  peat and humisol orders, not as a documented column. Would need direct
  inspection of the GeoPackage table headers to confirm.

  Organic carbon as a separate field - the guide gives MOS "calculee avec
  un facteur 1,724", which leaves open whether the stored column is OC or
  OM. Note that 1.724 is the same Van Bemmelen factor used in
  compaction_model.organic_carbon_from_om().

## Download formats

GeoPackage (QGIS), Geodatabase (ArcGIS), Shapefile, GeoJSON - full Quebec
coverage, 680 sheets at 1:20 000. Free.

## Why this was sought

sigma_pc in compaction_model.py needs B-horizon clay, silt and organic
carbon. RT-08 (ref_soil_series_quebec) holds surface texture only. PPC
covers the B horizon and would close that gap.

## Status

NOT integrated. Compaction work is paused pending a model from Slava
Adamchuk, who advised against assembling one from separate published
components. This note records the resource so it can be picked up if
needed.

Contact: Catherine Bosse, IRDA - available week of 17 August 2026.
