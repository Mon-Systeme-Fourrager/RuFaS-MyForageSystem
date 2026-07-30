# Topographic Input Service

## ADDED Requirements

### Requirement: Fetch slope and aspect from Jérémie's LiDAR API

The service SHALL fetch slope and aspect from Jérémie's LiDAR API
for any field geometry provided as input. The API returns slope in
degrees, aspect in degrees from North, and a deterministic STAC ID
derived from the field geometry. The service MUST accept both
Polygon and MultiPolygon GeoJSON as input.

#### Scenario: Field with previously unseen geometry
- **WHEN** the simulation runner receives a field geometry not in
  the STAC cache
- **THEN** the service SHALL call Jérémie's API with the geometry
- **AND** the service SHALL parse the response into slope (degrees),
  aspect (degrees), and STAC ID
- **AND** the service SHALL write the response to the Supabase
  `topographic_cache` table
- **AND** the returned values SHALL be available for CSV writing

#### Scenario: Field with cached STAC ID
- **WHEN** the simulation runner receives a field geometry whose
  STAC ID matches an existing cache entry
- **THEN** the service SHALL retrieve slope and aspect from the
  Supabase cache without calling the API
- **AND** the retrieval SHALL complete in under 2 seconds

#### Scenario: Field with MultiPolygon geometry
- **WHEN** the input geometry is a MultiPolygon (multiple contiguous
  rings)
- **THEN** the service SHALL pass the MultiPolygon to the API
  without unwrapping
- **AND** the returned STAC ID SHALL be deterministic for the same
  MultiPolygon input

### Requirement: Convert slope units at documented boundaries

The service SHALL convert slope units at documented boundaries. The
API returns slope in degrees. RUFAS SCS-CN expects slope as a
fraction (m/m). The conversion MUST happen exactly once, at the
boundary between the API response and the RUFAS CSV writer, in a
centralized module.

#### Scenario: Degrees to fraction conversion for RUFAS
- **WHEN** the service prepares a Zone CSV for RUFAS
- **THEN** `degrees_to_fraction(slope_deg)` SHALL be called
- **AND** the written `angle_of_slope` column SHALL contain the
  fraction value
- **AND** function signatures touching slope SHALL document the
  expected unit

#### Scenario: Unit conversion tested with known values
- **WHEN** unit tests run
- **THEN** `degrees_to_fraction(1.298)` SHALL equal 0.0227 ± 0.0001
- **AND** `degrees_to_fraction(1.249)` SHALL equal 0.0218 ± 0.0001

### Requirement: Fail fast on missing LiDAR coverage or API errors

The service SHALL fail fast on missing LiDAR coverage or API
errors. Silent fallback to flat-field values is prohibited — it
would violate the no-fabrication rule in root CLAUDE.md.

#### Scenario: Field outside MRNF LiDAR coverage
- **WHEN** the API returns no data for a field geometry (outside
  Quebec or outside MRNF coverage)
- **THEN** the service SHALL raise `APICoverageError` with the field
  reference in the message
- **AND** the simulation runner SHALL NOT proceed with a default
  value
- **AND** the failure SHALL be logged with geometry hash and
  timestamp

#### Scenario: API timeout
- **WHEN** the API does not respond within the configured timeout
  (default 30 seconds)
- **THEN** the service SHALL raise `APITimeoutError`
- **AND** the simulation runner SHALL NOT proceed
- **AND** no partial cache entry SHALL be written

#### Scenario: API returns malformed response
- **WHEN** the API response cannot be parsed as JSON, or is missing
  slope or STAC ID fields
- **THEN** the service SHALL raise `APIResponseError` with the raw
  response body in the log
- **AND** no cache entry SHALL be written

### Requirement: Maintain an audit trail for every API interaction

The service SHALL maintain an audit trail for every API
interaction. Every call to Jérémie's API MUST be traceable to a
specific input geometry, timestamp, and STAC ID. This supports the
no-fabrication rule for scientific inputs.

#### Scenario: Successful API call
- **WHEN** the service completes an API call successfully
- **THEN** the log SHALL contain: STAC ID, geometry hash, latency
  (ms), response slope value, response aspect value, cache hit/miss
- **AND** the Supabase cache row SHALL contain: STAC ID, slope,
  aspect, geometry hash, API response timestamp

#### Scenario: Reproducing a past simulation
- **WHEN** an auditor needs to verify the slope value used in a
  past simulation
- **THEN** the STAC ID in the log SHALL match a row in the Supabase
  cache
- **AND** the cache row values SHALL match the CSV values written
  for that simulation

### Requirement: Integrate with the existing ingestion pipeline pattern

The service SHALL integrate with the existing ingestion pipeline
pattern. Per Maxime Leduc's 2026-07-28 weekly directive, new
external data sources MUST reuse the ingestion patterns established
by Rami (AWS Step Functions, Lambda, S3), not introduce new
pipeline architectures.

#### Scenario: New ingestion source in the codebase
- **WHEN** a new external data source is integrated into MSFourrager
- **THEN** it SHALL follow the AWS Step Functions / Lambda / S3
  pattern documented in the existing Open-Meteo bridge
- **AND** it SHALL NOT introduce a parallel ingestion architecture
