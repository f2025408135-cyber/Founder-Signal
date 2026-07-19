# Synthetic Founder Dataset

Generated: 2026-07-19T04:17:26.502999

## Distribution

| Category | Count |
|---|---|
| cold_start | 10 |
| rich_signal | 12 |
| contradicted | 10 |
| missing_data | 8 |
| mixed | 10 |
| **Total** | **50** |

## Sectors

- AI infra: 7
- Climate: 8
- Consumer: 10
- DevTools: 7
- Fintech: 6
- Healthtech: 12

## Geographies

- DE: 8
- FR: 8
- GB: 7
- IN: 9
- PK: 8
- SG: 4
- US: 6

## Recommended Demo Fixtures

| Use case | Founder ID | Name | Company |
|---|---|---|---|
| Cold-start example | a8dfee45-92e5-4416-8162-46c8f0f67428 | Pavel Khan | PrismSystems |
| Rich-signal example | 66e3a8b4-e64a-4f88-b57f-ba6510128ffe | Adaeze Khan | PrismEnergy |
| Contradiction example | 7fdf7535-9290-44d9-b649-7fa3e5c872cd | Yelena Müller | ApexRobotics |
| Missing-data example | c1dd8c3a-c941-4dbc-90f6-3d85dbda0288 | Olamide Almeida | NovaTools |

## Schema

Each founder JSON file matches:
- `Claim` schema (BUILD_SPEC.md §3.1) — `confidence` left at 0.5, `flags` left empty (Validator fills these)
- `FounderScore` schema (BUILD_SPEC.md §3.2) — single `score_history` entry as seed

## Photos

Profile photos are fetched from randomuser.me API (https://randomuser.me/api/) —
free, explicitly designed for generating fake test/dummy profile data.

## Validation

All 50 founder JSON files validate against the Claim and FounderScore Pydantic schemas
with no missing required fields.
