"""Seed all 20 contract articles from exhibit-A-contract.md into the database."""

import re
import sqlite3
import uuid
from pathlib import Path

DB_PATH = Path("/opt/exhibit-a/data/exhibit-a.db")
CONTRACT_PATH = Path(__file__).parent.parent / "docs" / "exhibit-A-contract.md"

ROMAN = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
    "XVII",
    "XVIII",
    "XIX",
    "XX",
]


def parse_articles(text: str) -> list[dict[str, str]]:
    """Split the contract markdown into individual articles."""
    pattern = r"^# (Article [IVXLCDM]+)\s*\n\n## (.+?)\n\n(.*?)(?=\n# Article|\Z)"
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)

    articles: list[dict[str, str]] = []
    for i, (article_num, title, body) in enumerate(matches):
        articles.append(
            {
                "id": str(uuid.uuid4()),
                "article_number": article_num,
                "title": title.strip(),
                "body": body.strip(),
                "section_order": str(i + 1),
            }
        )
    return articles


def main() -> None:
    """Insert contract articles and sync_log entries."""
    text = CONTRACT_PATH.read_text()
    articles = parse_articles(text)

    if len(articles) != 20:
        msg = f"Expected 20 articles, parsed {len(articles)}"
        raise ValueError(msg)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    for art in articles:
        conn.execute(
            "INSERT INTO content "
            "(id, type, title, subtitle, body, article_number, classification, "
            "section_order, requires_signature) "
            "VALUES (?, 'contract', ?, NULL, ?, ?, NULL, ?, 1)",
            (
                art["id"],
                art["title"],
                art["body"],
                art["article_number"],
                art["section_order"],
            ),
        )
        conn.execute(
            "INSERT INTO sync_log (entity_type, entity_id, action) "
            "VALUES ('content', ?, 'create')",
            (art["id"],),
        )

    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM content WHERE type = 'contract'"
    ).fetchone()[0]
    print(f"Seeded {len(articles)} contract articles. Total contracts in DB: {count}")

    conn.close()


if __name__ == "__main__":
    main()
