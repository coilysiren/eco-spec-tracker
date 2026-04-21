"""Mock data shaped like what the Eco mod will eventually return.

Each player has a set of learned specialties (skill trees with Level > 0).
The tracker aggregates this per-profession to show `active / total`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerSpecialty:
    player: str
    specialty: str
    level: int  # 0 means not learned; we only store learned rows in mock data
    active: bool  # "active" = logged in within the last N days, placeholder for now


# Canonical profession → specialties map, mirroring Eco's skill tree roughly.
# (Final list will come from the mod; this is just for UI iteration.)
PROFESSION_SPECIALTIES: dict[str, list[str]] = {
    "Carpentry": ["Basic Carpentry", "Advanced Carpentry", "Furniture Making", "Lumber"],
    "Masonry": ["Basic Masonry", "Advanced Masonry", "Pottery", "Brick Making"],
    "Smelting": ["Basic Smelting", "Advanced Smelting", "Composites", "Alloys"],
    "Glassworking": ["Glassworking", "Hand-Plane Glass"],
    "Cooking": ["Campfire Cooking", "Baking", "Cutting Edge Cooking", "Advanced Baking"],
    "Farming": ["Farming", "Gardening", "Fertilizers"],
    "Hunting": ["Hunting", "Butchery"],
    "Mining": ["Mining", "Advanced Mining"],
    "Logging": ["Logging", "Advanced Logging"],
    "Engineering": ["Mechanics", "Electronics", "Industry"],
    "Tailoring": ["Tailoring", "Advanced Tailoring"],
    "Paper Milling": ["Paper Milling", "Printing"],
}


_MOCK_ROWS: list[PlayerSpecialty] = [
    PlayerSpecialty("coilysiren", "Basic Carpentry", 5, True),
    PlayerSpecialty("coilysiren", "Advanced Carpentry", 3, True),
    PlayerSpecialty("coilysiren", "Furniture Making", 2, True),
    PlayerSpecialty("ekans", "Basic Carpentry", 4, True),
    PlayerSpecialty("ekans", "Lumber", 1, True),
    PlayerSpecialty("ekans", "Mining", 6, True),
    PlayerSpecialty("redwood", "Glassworking", 5, False),
    PlayerSpecialty("redwood", "Basic Masonry", 2, False),
    PlayerSpecialty("redwood", "Pottery", 3, False),
    PlayerSpecialty("salt", "Campfire Cooking", 4, True),
    PlayerSpecialty("salt", "Baking", 2, True),
    PlayerSpecialty("salt", "Farming", 5, True),
    PlayerSpecialty("salt", "Gardening", 3, True),
    PlayerSpecialty("quill", "Paper Milling", 4, True),
    PlayerSpecialty("quill", "Printing", 2, True),
    PlayerSpecialty("hammerhand", "Basic Masonry", 5, True),
    PlayerSpecialty("hammerhand", "Brick Making", 4, True),
    PlayerSpecialty("hammerhand", "Advanced Masonry", 3, True),
    PlayerSpecialty("voltaic", "Mechanics", 5, False),
    PlayerSpecialty("voltaic", "Electronics", 4, False),
    PlayerSpecialty("voltaic", "Industry", 2, False),
    PlayerSpecialty("fernweh", "Farming", 3, True),
    PlayerSpecialty("fernweh", "Fertilizers", 2, True),
    PlayerSpecialty("fernweh", "Hunting", 4, True),
    PlayerSpecialty("fernweh", "Butchery", 3, True),
    PlayerSpecialty("ore-ge", "Basic Smelting", 5, True),
    PlayerSpecialty("ore-ge", "Advanced Smelting", 3, True),
    PlayerSpecialty("ore-ge", "Alloys", 2, True),
    PlayerSpecialty("tinkerbell", "Tailoring", 4, False),
    PlayerSpecialty("tinkerbell", "Advanced Tailoring", 2, False),
]


def all_rows() -> list[PlayerSpecialty]:
    return list(_MOCK_ROWS)


@dataclass(frozen=True)
class ProfessionStat:
    profession: str
    active: int
    total: int
    players: list[str]


def profession_stats() -> list[ProfessionStat]:
    """Per-profession counts: active (>=1 active learned specialty) / total (any learned)."""
    stats: list[ProfessionStat] = []
    for profession, specialties in PROFESSION_SPECIALTIES.items():
        specialty_set = set(specialties)
        rows = [r for r in _MOCK_ROWS if r.specialty in specialty_set]
        players_all = {r.player for r in rows}
        players_active = {r.player for r in rows if r.active}
        stats.append(
            ProfessionStat(
                profession=profession,
                active=len(players_active),
                total=len(players_all),
                players=sorted(players_all),
            )
        )
    stats.sort(key=lambda s: (-s.total, s.profession))
    return stats


@dataclass(frozen=True)
class PlayerView:
    name: str
    active: bool
    specialties: list[PlayerSpecialty]


def players() -> list[PlayerView]:
    by_player: dict[str, list[PlayerSpecialty]] = {}
    for r in _MOCK_ROWS:
        by_player.setdefault(r.player, []).append(r)
    out: list[PlayerView] = []
    for name, rows in by_player.items():
        out.append(
            PlayerView(
                name=name,
                active=any(r.active for r in rows),
                specialties=sorted(rows, key=lambda r: r.specialty),
            )
        )
    out.sort(key=lambda p: (not p.active, p.name))
    return out


@dataclass(frozen=True)
class SpecialtyHolder:
    player: str
    level: int
    active: bool


@dataclass(frozen=True)
class SpecialtyView:
    name: str
    profession: str
    active: int  # holders flagged active
    total: int
    holders: list[SpecialtyHolder]  # sorted: active first, then level desc


def _specialty_to_profession() -> dict[str, str]:
    return {s: prof for prof, specs in PROFESSION_SPECIALTIES.items() for s in specs}


def specialties() -> list[SpecialtyView]:
    """The inverse of players(): per specialty, who holds it and at what level."""
    prof_of = _specialty_to_profession()
    by_spec: dict[str, list[PlayerSpecialty]] = {}
    for r in _MOCK_ROWS:
        by_spec.setdefault(r.specialty, []).append(r)
    out: list[SpecialtyView] = []
    for spec, rows in by_spec.items():
        holders = sorted(
            (SpecialtyHolder(r.player, r.level, r.active) for r in rows),
            key=lambda h: (not h.active, -h.level, h.player),
        )
        out.append(
            SpecialtyView(
                name=spec,
                profession=prof_of.get(spec, "Other"),
                active=sum(1 for h in holders if h.active),
                total=len(holders),
                holders=holders,
            )
        )
    out.sort(key=lambda s: (s.profession, s.name))
    return out
