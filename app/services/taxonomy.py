"""
Festival/occasion taxonomy, scoped by region.

Kept as data (not hardcoded into the app) so each region's list reflects
that region's actual demographic makeup rather than one assumed "default"
culture with everyone else added as an afterthought. All entries within a
region are treated as equal-weight tags — no "major/minor" tiering — since
that's what makes the filter genuinely inclusive rather than a majority
list with token additions.

Sourced from Statistics Canada 2021 Census religious/ethnocultural data for
the CA list. Update/extend per-region lists as you add new regions (US,
then others) — each region should be researched on its own terms, not
derived from another region's list.
"""

FESTIVALS_BY_REGION: dict[str, list[str]] = {
    "CA": [
        # Secular / universal occasions
        "Birthday",
        "Baby shower registry",
        "Back-to-school",
        "Graduation",
        # Cultural & religious observances — flat, unordered by size
        "Christmas",
        "Easter",
        "Halloween",
        "Diwali",
        "Vaisakhi",
        "Eid al-Fitr",
        "Eid al-Adha",
        "Hanukkah",
        "Lunar New Year",
    ],
}


def get_festivals_for_region(region: str) -> list[str]:
    """Returns the festival tag list for a region, or [] if not configured yet."""
    return FESTIVALS_BY_REGION.get(region.upper(), [])
