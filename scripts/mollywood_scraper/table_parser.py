"""
table_parser.py
Generic parser for Wikipedia award-category tables of the form:

| Year | Actor | Role(s) | Film | Ref |
| 1972 | N.T. Rama Rao (bold=winner) | Raghava Rao | Badi Panthulu | |
|      | Akkineni Nageswara Rao      | Abbi        | Marapurani Manishi | |
...

Handles:
- rowspan on the Year column (year applies to following rows until next year cell)
- bold / <b> markup indicating the winner
- variable column counts (3 cols = Nominee/Producer, Film  |  4 cols = Nominee, Role, Film)
"""

from bs4 import BeautifulSoup, Tag
from common import clean_text


def _cell_text(cell: Tag) -> str:
    return clean_text(cell.get_text(" ", strip=True))


def _is_winner_cell(cell: Tag) -> bool:
    """Winner is usually bolded (<b> or <th>) in these tables."""
    return cell.find("b") is not None or cell.name == "th"


def parse_award_table(table: Tag, has_role_column: bool, winners_only: bool = False):
    """
    Yields dicts: {year, nominee, role, film, is_winner}
    has_role_column: True for acting categories (Nominee, Role, Film),
                      False for single-person categories (Nominee, Film) e.g. Best Film, Director, Music Director
    """
    rows = table.find_all("tr")
    current_year = None
    year_rowspan_remaining = 0

    parsed_items = []

    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue

        # Skip header rows (all <th> with no data look like a header)
        if all(c.name == "th" for c in cells) and len(cells) <= 5:
            header_text = " ".join(_cell_text(c) for c in cells).lower()
            if "year" in header_text or "actor" in header_text or "film" in header_text:
                continue

        idx = 0
        # Detect a year cell: first cell, has rowspan or matches year pattern
        first_cell_text = _cell_text(cells[0])
        looks_like_year = bool(
            __import__("re").match(r"^\d{4}(?:\D|$)", first_cell_text)
        )

        if looks_like_year:
            current_year = first_cell_text
            rowspan = cells[0].get("rowspan")
            year_rowspan_remaining = int(rowspan) - 1 if rowspan else 0
            idx = 1
        elif year_rowspan_remaining > 0:
            year_rowspan_remaining -= 1
            # idx stays 0, this row has no year cell of its own
        else:
            # No year info available for this row; skip (likely a stray note row)
            continue

        remaining = cells[idx:]
        if not remaining:
            continue

        is_winner = any(_is_winner_cell(c) for c in remaining)

        if has_role_column and len(remaining) >= 3:
            nominee = _cell_text(remaining[0])
            role = _cell_text(remaining[1])
            film = _cell_text(remaining[2])
        elif len(remaining) >= 2:
            nominee = _cell_text(remaining[0])
            role = ""
            film = _cell_text(remaining[1])
        elif len(remaining) == 1:
            # Sometimes film-only or nominee-only row; treat as nominee with blank film
            nominee = _cell_text(remaining[0])
            role = ""
            film = ""
        else:
            continue

        if not nominee and not film:
            continue

        parsed_items.append({
            "year": current_year,
            "nominee": nominee,
            "role": role,
            "film": film,
            "is_winner": is_winner,
        })

    # Group by year to check count per year
    year_counts = {}
    for item in parsed_items:
        yr = item["year"]
        year_counts[yr] = year_counts.get(yr, 0) + 1

    for item in parsed_items:
        yr = item["year"]
        if winners_only or year_counts.get(yr, 0) == 1:
            item["is_winner"] = True
        yield item
