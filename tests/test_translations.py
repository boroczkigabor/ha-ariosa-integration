import json
from pathlib import Path

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "ariosa"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_keys(data: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()

    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            keys |= _all_keys(value, path)
        else:
            keys.add(path)

    return keys


def test_translations_have_matching_keys() -> None:
    """Every language file must define the same set of translation keys.

    translations/en.json is the single source of truth (Home Assistant's
    runtime translation loader reads translations/<lang>.json directly, so
    there is no separate strings.json to keep in sync with).
    """

    translations_dir = COMPONENT_DIR / "translations"
    reference = _load(translations_dir / "en.json")
    reference_keys = _all_keys(reference)

    for path in sorted(translations_dir.glob("*.json")):
        keys = _all_keys(_load(path))
        assert keys == reference_keys, f"{path.name} keys do not match en.json"
