"""The README must show the numbers the code produces."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_table_is_the_generated_table() -> None:
    table = (ROOT / "output" / "estimates.md").read_text(encoding="utf-8").strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert table in readme
