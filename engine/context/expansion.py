"""Create an immutable successor from two compatible Context Packages."""

from typing import Any

from engine.context.package import ContextPackage, ContextPackageError

_SECTIONS = ("project", "knowledge", "coordination")
_KEYS = {
    "conventions": ("id",),
    "components": ("id",),
    "contracts": ("id",),
    "assertions": ("id",),
    "relevant_prs": ("number",),
    "dependencies": ("reference", "relationship"),
    "uncertainties": ("id",),
}


def _merge_items(field: str, existing: Any, additional: Any) -> list[Any]:
    if not isinstance(existing, list) or not isinstance(additional, list):
        raise ContextPackageError(f"Expected an array for {field}")
    key_fields = _KEYS.get(field)
    if key_fields is None:
        merged = list(existing)
        merged.extend(item for item in additional if item not in merged)
        return merged

    indexed = {}
    for item in (*existing, *additional):
        if not isinstance(item, dict) or any(
            type(item.get(key)) not in (str, int) for key in key_fields
        ):
            raise ContextPackageError(f"Missing or invalid identity in {field}")
        key = tuple(item[name] for name in key_fields)
        previous = indexed.setdefault(key, item)
        if field == "assertions":
            previous = {
                name: value for name, value in previous.items() if name != "relevance"
            }
            item = {name: value for name, value in item.items() if name != "relevance"}
        if previous != item:
            raise ContextPackageError(f"Conflicting evidence in {field} for {key}")
    return list(indexed.values())


def _merge_section(
    section: str, parent: dict[str, Any], additional: dict[str, Any]
) -> dict[str, Any]:
    before, more = parent.get(section, {}), additional.get(section, {})
    if not isinstance(before, dict) or not isinstance(more, dict):
        raise ContextPackageError(f"Expected an object for {section}")
    return {
        field: _merge_items(field, before.get(field, []), more.get(field, []))
        for field in dict.fromkeys((*before, *more))
    }


def expand_context(
    parent: ContextPackage, additional: ContextPackage, *, max_bytes: int = 16_384
) -> ContextPackage:
    """Add evidence for the same task, revision, workspace, and snapshot."""
    if max_bytes < 1:
        raise ContextPackageError("Context Package byte budget must be positive")
    before, more = parent.to_dict(), additional.to_dict()
    if before["identity"] != more["identity"]:
        raise ContextPackageError(
            "Expansion requires the same task, repository, revision, workspace, and snapshot"
        )

    content = {key: value for key, value in before.items() if key != "package_id"}
    added = False
    for section in _SECTIONS:
        merged = _merge_section(section, before, more)
        if merged:
            content[section] = merged
        added |= any(
            items != before.get(section, {}).get(field, [])
            for field, items in merged.items()
        )
    uncertainties = _merge_items(
        "uncertainties", before.get("uncertainties", []), more.get("uncertainties", [])
    )
    if uncertainties:
        content["uncertainties"] = uncertainties
    if not added and uncertainties == before.get("uncertainties", []):
        raise ContextPackageError("Expansion adds no new evidence or uncertainty")

    previous_integrity = before["integrity"]
    additional_integrity = more["integrity"]
    freshness = (
        previous_integrity.get("freshness"),
        additional_integrity.get("freshness"),
    )
    depth = {
        previous_integrity.get("discovery_depth", "unknown"),
        additional_integrity.get("discovery_depth", "unknown"),
    } - {"unknown"}
    content["integrity"] = {
        "freshness": "stale"
        if "stale" in freshness
        else "current"
        if freshness == ("current", "current")
        else "unknown",
        "coverage": "unknown"
        if previous_integrity.get("coverage")
        == additional_integrity.get("coverage")
        == "unknown"
        else "partial",
        "limitations": _merge_items(
            "limitations",
            previous_integrity.get("limitations", []),
            additional_integrity.get("limitations", []),
        ),
        "discovery_depth": "mixed" if len(depth) > 1 else next(iter(depth), "unknown"),
    }
    content["parent_package_id"] = before["package_id"]
    package = ContextPackage.create(content)
    if len(package.to_json()) > max_bytes:
        raise ContextPackageError(
            "Expansion cannot preserve all evidence within the byte budget"
        )
    return package
