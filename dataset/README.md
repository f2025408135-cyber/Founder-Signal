# Synthetic Founder Dataset

Generated: 2026-07-19T09:45:57.147725

This dataset is the **canonical reference copy** of the 50 fictional founder records
used by the Founder-Signal demo. The source of truth at runtime is the Postgres
database (see `scripts/seed_dataset.py`); this folder exists for version control
and inspection.

## Distribution actually generated

| Category | Count |
|---|---|
| cold_start    | 10 |
| rich_signal   | 12 |
| contradicted  | 10 |
| missing_data  | 8 |
| mixed         | 10 |
| **Total**     | **50** |

> Categories can overlap (e.g. a founder can be both `rich_signal` and `contradicted`).
> Above counts are per-tag, so they may sum to more than 50.

## Sectors (6 ≥ 5 required)

- Healthtech: 12
- Climate: 11
- DevTools: 8
- Consumer: 8
- AI infra: 7
- Fintech: 4

## Geographies (7 ≥ 4 required, ISO-3166 alpha-2)

- GB: 11
- FR: 10
- IN: 9
- US: 8
- DE: 5
- PK: 4
- SG: 3

## Image sourcing

| Asset | Real fetched | Local SVG fallback |
|---|---|---|
| Photos (randomuser.me)        | 49 | 1 |
| University images (Wikimedia) | 50  | 0 |

- **Photos**: fetched from `https://randomuser.me/api/` (free, built for fake profile data).
  When the API is unreachable or `--no-fetch` is passed, the generator writes a
  deterministic initials-avatar SVG under `dataset/assets/avatars/<founder_id>.svg`
  and points `photo_url` at it.
- **University images**: searched via the Wikimedia Commons API (CC-licensed only —
  CC BY / CC BY-SA / CC0 / public domain). When no suitable image is found, the
  generator writes a generic campus-building SVG under
  `dataset/assets/campuses/<slug>.svg`.
- The `image_source` block on each founder record (and the same field in
  `index.json`) records which path was used, so the team can see at a glance
  which founders got real fetched images vs. local fallback placeholders before
  the demo.

## Recommended demo fixtures (one per category)

These four founder IDs should be referenced in `DEMO_SCRIPT.md` as the canonical
live-demo fixtures — each is the strongest-scoring example in its category so the
memo view has the richest content to render:

| Use case | founder_id | Name | Company | Sector / Geo |
|---|---|---|---|---|
| Cold-start example | `515777fd-48e8-4980-9de6-d5cd2dc1d939` | Nikolai Ali | ForgeEnergy | Climate / PK |
| Rich-signal example | `e6d64178-4ec0-41d1-94df-eb23860a0653` | Kenji Okafor | OrbitClimate | DevTools / PK |
| Contradiction example | `be84c3dc-ed82-4c1f-bc65-e1badb27e1e6` | Stefan Khan | AtlasStack | Healthtech / US |
| Missing-data example | `0f509bcc-fa90-45ed-8eef-621e9e5635cf` | Henrik García | MeshEnergy | AI infra / FR |

Canonical IDs:

```text
cold_start:    515777fd-48e8-4980-9de6-d5cd2dc1d939  (Nikolai Ali — ForgeEnergy)
rich_signal:   e6d64178-4ec0-41d1-94df-eb23860a0653  (Kenji Okafor — OrbitClimate)
contradicted:  be84c3dc-ed82-4c1f-bc65-e1badb27e1e6  (Stefan Khan — AtlasStack)
missing_data:  0f509bcc-fa90-45ed-8eef-621e9e5635cf  (Henrik García — MeshEnergy)
```

## Schema

Each founder JSON file validates against the BUILD_SPEC.md schemas:

- `claims[*]` matches **Claim** (§3.1). `confidence` is left at the default `0.5`
  and `flags` is left `[]` — the real Validator Agent fills these in when the
  pipeline runs.
- `founder_score_seed` matches **FounderScore** (§3.2) with a single starting
  `score_history` entry.
- `photo_url` and `university_image_url` are non-null on every record (real
  fetched URL or local SVG path).

## Reproducing

```bash
python scripts/dataset/generate_founders.py            # uses randomuser.me + Wikimedia
python scripts/dataset/generate_founders.py --no-fetch # offline-safe: every image is local SVG
python scripts/dataset/generate_founders.py --seed 42  # deterministic
```

Then validate + seed the database:

```bash
python scripts/dataset/validate_dataset.py
python scripts/seed_dataset.py
python scripts/verify_dataset.py
```
