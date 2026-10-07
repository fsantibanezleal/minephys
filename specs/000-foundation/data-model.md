# Data model 000 — knowledge tables, bibliography and API snapshot
Spec: ./spec.md · Contracts: DC-000-02, DC-000-03, DC-000-04

Three artefacts cross the library boundary. Each has a JSON Schema 2020-12 file under `contracts/` (task T-000-001) and
a pure-Python validator in the library or in `tools/`. The two must agree on the fixtures in
`tests/contract/fixtures/` (valid and invalid cases for every rule below).

## 1. Knowledge table (DC-000-02) — `contracts/knowledge-table.schema.json`

One YAML file per domain: `src/minephys/knowledge/<table>.yaml`. Tables derived from share-alike sources live in
`src/minephys/knowledge/share-alike/<table>.yaml`.

### Table object

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | const `1` |
| `table` | string | equals the file stem; pattern `^[a-z][a-z0-9_]*$` |
| `title` | string | non-empty, English |
| `licence` | string | SPDX id; `CC-BY-4.0` for files in `knowledge/`; `CC-BY-SA-4.0` or `CC-BY-SA-3.0` for files in `knowledge/share-alike/` |
| `rows` | array of row objects | at least one row |

No other field is allowed (`additionalProperties: false`).

### Row object

| Field | Type | Rule |
|---|---|---|
| `id` | string | pattern `^[a-z][a-z0-9_]*$`; unique across all tables of the package |
| `quantity` | string | what the number is, in plain English (for example "diesel combustion CO₂ emission factor") |
| `value` | number, or string `"p/q"` | finite number, or an exact rational written as a string matching `^-?\d+/\d+$` (for published exponents such as `"19/30"`; the loader evaluates it as `p/q` in float64, so no rounded decimal enters the model); exactly one of `value` and `range` is present |
| `range` | object `{min, max}` | both finite numbers, `min ≤ max` |
| `units` | string | as published in the source; `"1"` for dimensionless |
| `role` | enum | `model_constant` (a number fixed by a published equation form or a named model variant), `parameter` (a typical value or range of a site or material input), `limit` (a regulatory limit or a validity bound of a model), `conversion` (an exact unit definition or a defined physical constant) |
| `citation` | string | a BibTeX key present in `references.bib` |
| `page` | string | page, table, figure or equation locator in the cited source; non-empty |
| `verification` | enum | `verified` or `UNVERIFIED` |
| `verified_on` | string (date) | `YYYY-MM-DD`; required when `verification` is `verified`, forbidden otherwise |
| `symbol` | string or array of strings | dotted path(s) of the exported object(s) that use the row, `minephys.<module>.<name>` |
| `notes` | string | optional: validity, conversion, caveats; for a transcription read only on a secondary source, "transcription read on `<key>` p. N" |

No other field is allowed.

### Validation rules beyond the schema (checked by the validator and by CI)

1. `id` unique across all tables.
2. `citation` resolves in the bibliography (DC-000-03).
3. Every `symbol` resolves to an object in its module's `__all__` (checked once the symbol is implemented; before
   that, the row's module spec lists it as planned).
4. A `verified` row is referenced by at least one test through `@pytest.mark.knowledge("<id>")` (FR-000-21).
5. A row whose `role` is `parameter` and whose verification is `UNVERIFIED` is never listed in a model card's
   `Knowledge rows` section (FR-000-22).
6. A `CC-BY-4.0` table cites no bibliography entry whose `licence` is a share-alike licence (FR-000-31).

### Example (illustrative)

```yaml
schema_version: 1
table: haulage
title: Haulage constants and parameters
licence: CC-BY-4.0
rows:
  - id: diesel_co2_kg_per_us_gal
    quantity: diesel fuel combustion CO2 emission factor
    value: 10.21
    units: kg CO2 / US gal
    role: model_constant
    citation: epa2025ghghub
    page: "Table 2, p. 2"
    verification: verified
    verified_on: "2026-10-06"
    symbol: minephys.haulage.co2_from_diesel
    notes: "combustion CO2 only; CH4 and N2O factors are in Table 5 (p. 3) of the same document"
```

## 2. Bibliography entry (DC-000-03) — `contracts/bibliography-entry.schema.json`

`references.bib` is BibTeX. The validator parses each entry into an object and validates it:

| Field | Type | Rule |
|---|---|---|
| `key` | string | pattern `^[a-z][a-z0-9_:-]*$`; unique |
| `entry_type` | enum | `article`, `book`, `inbook`, `inproceedings`, `techreport`, `manual`, `misc` |
| `author` or `organization` | string | at least one present |
| `title` | string | non-empty |
| `year` | integer | 1800–2100 |
| `doi` | string | pattern `^10\.\d{4,9}/\S+$` |
| `url` | string | `https://` or `http://` URL |
| `access` | enum | `open`, `paywalled`, `regulation`, `bibliographic-only` |
| `licence` | string | optional SPDX id of the source's own licence (required for share-alike sources) |
| `journal`, `booktitle`, `volume`, `number`, `pages`, `publisher`, `edition`, `note` | string | optional |

At least one of `doi` and `url` is present. Unknown BibTeX fields are an error, so that a typo cannot hide a citation.

## 3. Public API snapshot (DC-000-04) — `contracts/api-snapshot.schema.json`

`docs/reference/api-snapshot.json`, written by `tools/check_api.py --write` at each release:

| Field | Type | Rule |
|---|---|---|
| `version` | string | `X.YY.ZZZ` of the release that wrote it |
| `objects` | array | one entry per exported object, sorted by `name` |
| `objects[].name` | string | dotted path |
| `objects[].kind` | enum | `function`, `class`, `constant`, `module` |
| `objects[].parameters` | array | for functions: `{name, kind, default, unit}` in order; `default` is the `repr` of the default or `null`; `unit` is the bracketed unit from the docstring |
| `objects[].deprecated` | object or null | `{since, removal, replacement}` |

## 4. Exceptions and warnings (FR-000-32)

| Class | Base | Attributes | Raised or emitted when |
|---|---|---|---|
| `minephys.InputError` | `ValueError` | `argument: str` | non-finite value, shape, size, domain or option error (FR-000-10, -12…-15) |
| `minephys.InputTypeError` | `TypeError` | `argument: str` | non-real-numeric argument (FR-000-11) |
| `minephys.ValidityWarning` | `UserWarning` | `argument: str`, `bounds: tuple[float, float]`, `row: str` | outside a source's validity range or a unit tripwire (FR-000-16) |
| `minephys.ConvergenceError` | `RuntimeError` | `argument = None`, `last_iterate`, `residual`, `iterations` | solver did not converge (FR-000-17) |

Messages start with the function name and quote the argument: `"cycle_time(): argument 'haul' must be ≥ 0 [s], got
-3.0"`. Tests match on the `argument` attribute, not on the message wording.
