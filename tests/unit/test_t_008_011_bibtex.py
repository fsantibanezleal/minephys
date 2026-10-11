"""T-008-011 (FR-008-03): the BibTeX-subset parser with the DC-000-03 rules.

Expected public API (`minephys.knowledge`): `bibliography()` -> tuple of frozen `Reference` objects whose attributes are the parsed
fields (`key`, `entry_type`, `author`, `organization`, `title`, `year` (an int), `doi`, `url`, `access`, `licence`, `journal`,
`booktitle`, `volume`, `number`, `pages`, `publisher`, `edition`, `note`; a field the entry does not have is None), and
`validate_tables(folder)` whose report lists the rule violations of `references.bib` as errors with `file` ending in `references.bib`
and `field` naming the field (the message names the entry key). The BibTeX subset (spec 008 section 7):
`@type{key, field = {...} | "..." | digits, ...}` with nested braces, `%` comment lines and blank lines between entries, field names
and entry types case-insensitive, UTF-8 text, `@string`, `@preamble` and `@comment` unsupported.

Oracles: hand-written BibTeX text with the expected parsed entries (tests/_knowledge_fixtures.py `GOOD_BIB`), and one-field mutations
of it, each with the rule it breaks (DC-000-03: key pattern, entry type, author or organization, title, year in 1800-2100, DOI
and URL patterns, access enum, licence enum, optional fields only from the allowed list, unknown fields rejected).
The brace policy (whether protective inner braces are kept in the value) is not fixed by the spec: values are compared with braces
removed where braces occur.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import _knowledge_fixtures as fx
import pytest


def _k():
    return importlib.import_module("minephys.knowledge")


def _bib_errors(tmp_path: Path, bib: str):
    folder = fx.write_tree(
        tmp_path / "k", bib=bib, equations=None, glossary=None, tables={"haulage": fx.good_tables()["haulage"]}
    )
    return list(_k().validate_tables(folder).errors)


def _on_bib(errors, field=None, key=None):
    out = []
    for e in errors:
        if not str(e.file).replace("\\", "/").endswith("references.bib"):
            continue
        if field is not None and e.field != field:
            continue
        if key is not None and key not in str(e):
            continue
        out.append(e)
    return out


@pytest.mark.req("FR-008-03")
@pytest.mark.oracle(
    "hand-calculation", "GOOD_BIB parsed by hand: four entries, three value syntaxes, comment line, integer years"
)
def test_fr_008_03_the_good_bibliography_parses_to_the_hand_written_entries(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    got = fx.run_api(
        base,
        """
import dataclasses
out = {}
for r in K.bibliography():
    out[r.key] = {k: v for k, v in dataclasses.asdict(r).items() if v is not None}
print(json.dumps(out))
""",
    )
    assert set(got) == {"doe2020", "agency2025", "sharealike2019", "epa2025ghghub"}
    assert got["doe2020"] == {
        "key": "doe2020",
        "entry_type": "article",
        "author": "Doe, Jane and Munoz, Maria",
        "title": "A Sourced Model of Comminution Energy",
        "journal": "Journal of Tests",
        "year": 2020,
        "doi": "10.1000/xyz123",
        "access": "open",
    }
    assert got["agency2025"] == {
        "key": "agency2025",
        "entry_type": "techreport",
        "organization": "Example Agency",
        "title": "Emission factors",
        "year": 2025,  # an unquoted, unbraced integer value
        "url": "https://example.org/factors.pdf",
        "access": "regulation",
    }
    assert got["epa2025ghghub"]["title"] == "GHG Emission Factors Hub"  # a "double-quoted" value
    assert got["epa2025ghghub"]["entry_type"] == "misc" and got["epa2025ghghub"]["year"] == 2025
    assert got["sharealike2019"]["licence"] == "CC-BY-SA-4.0" and got["sharealike2019"]["publisher"] == "Open Press"
    assert isinstance(got["doe2020"]["year"], int)


@pytest.mark.req("FR-008-03")
@pytest.mark.oracle("hand-calculation", "case-insensitive names, nested braces, accents, comments and blank lines")
def test_fr_008_03_syntax_variants(tmp_path: Path) -> None:
    bib = """\
% leading comment

@ARTICLE{mixed2021:a-b,
  AUTHOR = {M{\\"u}ller, Hans and Garc{\\'\\i}a, Mar{\\'\\i}a},
  Title = {Energía y {Comminution}: a {nested {brace}} study of µm sizes},
  JOURNAL = "Revista Chilena de Minería",
  year = {2021},
  DOI = {10.1234/abc.def-1},
  Access = {paywalled},
  pages = {12--34}
}

% a comment between entries
@Book{lower-key_1,
  organization = {Instituto de Ingeniería},
  title = {Libro},
  year=1999,
  url = {http://example.org/libro},
  access = {bibliographic-only}
}
"""
    base = fx.write_package_tree(
        tmp_path / "pkg",
        bib=bib,
        tables={"haulage": _only_haulage_with("mixed2021:a-b")},
        equations=None,
        glossary=None,
    )
    got = fx.run_api(
        base,
        """
import dataclasses
print(json.dumps({r.key: {k: v for k, v in dataclasses.asdict(r).items() if v is not None} for r in K.bibliography()}))
""",
    )
    assert set(got) == {"mixed2021:a-b", "lower-key_1"}
    a = got["mixed2021:a-b"]
    assert a["entry_type"] == "article" and a["year"] == 2021 and a["pages"] == "12--34" and a["access"] == "paywalled"
    strip = lambda s: s.replace("{", "").replace("}", "")  # noqa: E731  the brace policy is not fixed by the spec
    assert strip(a["title"]) == "Energía y Comminution: a nested brace study of µm sizes"
    assert "ía" in a["title"] and "µ" in a["title"]  # UTF-8 text is preserved
    assert a["journal"] == "Revista Chilena de Minería"
    assert "Hans" in a["author"] and "Mar" in a["author"] and " and " in a["author"]
    assert got["lower-key_1"]["entry_type"] == "book" and got["lower-key_1"]["year"] == 1999


def _only_haulage_with(citation: str):
    table = fx.good_tables()["haulage"]
    for row in table["rows"]:
        row["citation"] = citation
    return table


# (name, entry appended to the good bibliography, accepted `field` values of the error or None)
MUTATIONS = [
    (
        "bad-key",
        "@article{Doe 2020,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        None,
    ),
    (
        "uppercase-key",
        "@article{Doe2020,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "key",
    ),
    (
        "no-author-no-organization",
        "@article{x1,\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        ("author", "organization"),
    ),
    (
        "no-title",
        "@article{x1,\n  author = {D, J},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "title",
    ),
    (
        "no-year",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "year",
    ),
    (
        "year-too-early",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {1799},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "year",
    ),
    (
        "year-too-late",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2101},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "year",
    ),
    (
        "year-not-a-number",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {twenty},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "year",
    ),
    (
        "no-doi-no-url",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  access = {open}\n}\n",
        ("doi", "url"),
    ),
    (
        "bad-doi",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {11.1000/x1},\n  access = {open}\n}\n",
        ("doi", "url"),
    ),
    (
        "short-doi-registrant",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.12/x1},\n  access = {open}\n}\n",
        ("doi", "url"),
    ),
    (
        "bad-url-scheme",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  url = {ftp://example.org/x},\n  access = {open}\n}\n",
        "url",
    ),
    (
        "url-with-credentials",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  url = {https://user:pw@example.org/x},\n  access = {open}\n}\n",
        "url",
    ),
    (
        "no-access",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1}\n}\n",
        "access",
    ),
    (
        "bad-access",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {secret}\n}\n",
        "access",
    ),
    (
        "bad-licence",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open},\n  licence = {GPL-3.0}\n}\n",
        "licence",
    ),
    (
        "unknown-field",
        "@article{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open},\n  pubdate = {2020}\n}\n",
        "pubdate",
    ),
    (
        "typo-field",
        "@article{x1,\n  autor = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        "autor",
    ),
    (
        "unknown-entry-type",
        "@phdthesis{x1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
        None,
    ),
]


@pytest.mark.req("FR-008-03")
@pytest.mark.oracle("hand-calculation", "one DC-000-03 rule broken per entry")
@pytest.mark.parametrize(("name", "entry", "field"), MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_fr_008_03_rule_violations_are_reported(tmp_path: Path, name: str, entry: str, field: object) -> None:
    errors = _bib_errors(tmp_path, fx.GOOD_BIB + "\n" + entry)
    on_bib = _on_bib(errors)
    assert on_bib, f"{name}: the invalid entry was accepted"
    if field is not None:
        accepted = field if isinstance(field, tuple) else (field,)
        assert any(e.field is not None and any(a in e.field for a in accepted) for e in on_bib), [
            (str(e.file), e.index, e.field) for e in on_bib
        ]


@pytest.mark.req("FR-008-03")
@pytest.mark.oracle("hand-calculation", "optional fields from the allowed list are accepted")
def test_fr_008_03_every_allowed_optional_field_is_accepted(tmp_path: Path) -> None:
    entry = """\
@inproceedings{full1,
  author = {D, J},
  title = {T},
  year = {2020},
  doi = {10.1000/x1},
  url = {https://example.org/x},
  access = {paywalled},
  licence = {CC-BY-NC-4.0},
  journal = {J},
  booktitle = {B},
  volume = {3},
  number = {4},
  pages = {5-6},
  publisher = {P},
  edition = {7th},
  note = {a note}
}
@manual{man1,
  organization = {O},
  title = {T},
  year = {2000},
  url = {http://example.org/m},
  access = {regulation}
}
@inbook{inb1, author = {A}, title = {T}, year = {1800}, doi = {10.1000/abc}, access = {open}}
@misc{mis1, author = {A}, title = {T}, year = {2100}, doi = {10.123456789/abc}, access = {open}}
"""
    assert _on_bib(_bib_errors(tmp_path, fx.GOOD_BIB + "\n" + entry)) == []
