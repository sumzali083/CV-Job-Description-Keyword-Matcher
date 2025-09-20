#!/usr/bin/env python3
# match.py

import argparse
import re
from collections import Counter
from pathlib import Path
from html import escape
from typing import Iterable, List, Set, Tuple, Dict

# --- Optional spaCy: use if model is present; fall back otherwise ---
USE_SPACY = False
nlp = None
STOP_WORDS = set()

try:
    import spacy
    from spacy.lang.en import stop_words as spacy_stop

    STOP_WORDS = set(spacy_stop.STOP_WORDS)
    try:
        nlp = spacy.load("en_core_web_sm")
        USE_SPACY = True
    except Exception:
        # Model not downloaded; fall back gracefully
        USE_SPACY = False
except Exception:
    # spaCy not installed (unlikely, since you installed it) — still works without it
    STOP_WORDS = set()

# --- Config ---
VALID_POS = {"NOUN", "PROPN", "VERB", "ADJ"}
MIN_LEN = 3
TOP_DEFAULT = 20

DEFAULT_NICE = [
    "docker",
    "ci/cd",
    "git",
    "kubernetes",
    "linux",
    "sql",
    "pandas",
    "numpy",
    "fastapi",
    "flask",
    "django",
    "pytest",
    "unit testing",
    "rest api",
    "oop",
    "data structures",
    "algorithms",
]

PHRASE_SPLIT_RE = re.compile(r"[^\w\-/+\.]+")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def tokenize_simple(text: str) -> List[str]:
    # Simple tokenizer: letters, digits, common dev symbols; lowercased
    raw = re.findall(r"[A-Za-z][A-Za-z0-9\-/+_.]{2,}", text)
    toks = [t.lower() for t in raw]
    # Strip punctuation-like endings
    cleaned = [t.strip("._-+/") for t in toks]
    # Filter stop words and too-short tokens
    return [t for t in cleaned if len(t) >= MIN_LEN and t not in STOP_WORDS]


def extract_terms(text: str) -> List[str]:
    """Return a list of normalized 'terms' from text."""
    if USE_SPACY and nlp is not None:
        doc = nlp(text)
        terms = []
        for tok in doc:
            if not tok.is_alpha:
                continue
            if tok.is_stop:
                continue
            if len(tok.lemma_) < MIN_LEN:
                continue
            if tok.pos_ not in VALID_POS:
                continue
            terms.append(tok.lemma_.lower())
        return terms
    else:
        return tokenize_simple(text)


def find_phrases(text: str, phrases: Iterable[str]) -> Set[str]:
    """Case-insensitive phrase detector for multi/single-word skills like 'CI/CD'."""
    text_l = text.lower()
    found = set()
    for p in phrases:
        p_norm = p.strip().lower()
        if not p_norm:
            continue
        if p_norm in text_l:
            found.add(p_norm)
    return found


def compute_overlap_and_gaps(cv_terms: Set[str], jd_terms: Set[str]) -> Tuple[Set[str], Set[str]]:
    overlap = cv_terms & jd_terms
    gaps = jd_terms - cv_terms
    return overlap, gaps


def score_terms(
    gaps: Set[str],
    jd_counts: Counter,
    phrase_hits: Set[str],
    phrase_bonus: float = 1.5,
) -> List[Tuple[str, float, int]]:
    """
    Return list of (term, score, freq) for gap terms, sorted by score desc.
    Score = frequency * (1 + bonus if in phrase hits)
    """
    scored = []
    for term in gaps:
        freq = jd_counts.get(term, 1)
        bonus = phrase_bonus if term in phrase_hits else 1.0
        scored.append((term, freq * bonus, freq))
    scored.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return scored


def make_cli_tables(
    overlap_sorted: List[Tuple[str, int]],
    gaps_scored: List[Tuple[str, float, int]],
    total_jd_terms: int,
    total_cv_terms: int,
):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    console.print(Panel.fit(
        f"[bold]CV ↔ JD Keyword Match[/bold]\n"
        f"[green]Overlap terms:[/green] {len(overlap_sorted)}   "
        f"[red]Gaps:[/red] {len(gaps_scored)}   "
        f"JD unique terms: {total_jd_terms}   CV unique terms: {total_cv_terms}",
        title="Summary",
    ))

    # Gaps table
    gaps_tbl = Table(title="Top Missing Terms (Gaps)", show_lines=False)
    gaps_tbl.add_column("#", justify="right")
    gaps_tbl.add_column("Term", style="bold red")
    gaps_tbl.add_column("JD Freq", justify="right")
    gaps_tbl.add_column("Score", justify="right")

    for i, (term, score, freq) in enumerate(gaps_scored, start=1):
        gaps_tbl.add_row(str(i), term, str(freq), f"{score:.2f}")
    console.print(gaps_tbl)

    # Overlap table
    ov_tbl = Table(title="Overlap Terms (present on your CV)", show_lines=False)
    ov_tbl.add_column("#", justify="right")
    ov_tbl.add_column("Term", style="green")
    ov_tbl.add_column("JD Freq", justify="right")

    for i, (term, freq) in enumerate(overlap_sorted, start=1):
        ov_tbl.add_row(str(i), term, str(freq))
    console.print(ov_tbl)


def make_html_report(
    overlap_sorted: List[Tuple[str, int]],
    gaps_scored: List[Tuple[str, float, int]],
    cv_phrases: Set[str],
    jd_phrases: Set[str],
    out_path: Path,
):
    def table_html(headers: List[str], rows: List[List[str]]) -> str:
        thead = "".join(f"<th>{escape(h)}</th>" for h in headers)
        trs = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table border='1' cellpadding='6' cellspacing='0'><thead><tr>{thead}</tr></thead><tbody>{trs}</tbody></table>"

    gaps_rows = [[str(i), term, str(freq), f"{score:.2f}"]
                 for i, (term, score, freq) in enumerate(gaps_scored, start=1)]
    ov_rows = [[str(i), term, str(freq)]
               for i, (term, freq) in enumerate(overlap_sorted, start=1)]

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>CV ↔ JD Keyword Match</title>
<style>
body {{ font-family: Arial, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }}
h1, h2 {{ margin-top: 1.2rem; }}
table {{ border-collapse: collapse; margin: 1rem 0; width: 100%; }}
th {{ background: #f5f5f5; text-align: left; }}
tr:nth-child(even) {{ background: #fafafa; }}
.badge {{ display:inline-block; padding: 4px 8px; margin: 2px; border-radius: 6px; background:#eef; }}
.badge.red {{ background: #fee; }}
.badge.green {{ background: #efe; }}
</style>
</head>
<body>
<h1>CV ↔ JD Keyword Match</h1>

<h2>Detected Phrases</h2>
<p><strong>On CV:</strong> {"".join(f"<span class='badge green'>{escape(p)}</span>" for p in sorted(cv_phrases)) or "—"}</p>
<p><strong>In JD:</strong> {"".join(f"<span class='badge red'>{escape(p)}</span>" for p in sorted(jd_phrases)) or "—"}</p>

<h2>Top Missing Terms (Gaps)</h2>
{table_html(["#", "Term", "JD Freq", "Score"], gaps_rows)}

<h2>Overlap Terms (present on your CV)</h2>
{table_html(["#", "Term", "JD Freq"], ov_rows)}

<p style="margin-top:2rem;color:#666">Generated by match.py</p>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")


def suggest_bullets(missing_terms: List[str], max_bullets: int = 10) -> List[str]:
    templates = [
        "Built a small demo using {term} and documented setup & outcomes.",
        "Practiced {term} by implementing a mini project and writing tests.",
        "Used {term} to solve a real task (data cleaning, API, or CLI) and published code.",
        "Created a short tutorial README explaining how to apply {term}.",
    ]
    bullets = []
    for t in missing_terms[:max_bullets]:
        bullets.append(templates[len(bullets) % len(templates)].format(term=t))
    return bullets


def main():
    parser = argparse.ArgumentParser(
        description="Match CV keywords against a Job Description."
    )
    parser.add_argument("--cv", type=Path, required=True, help="Path to cv.txt")
    parser.add_argument("--job", type=Path, required=True, help="Path to job.txt")
    parser.add_argument("--nice", type=Path, default=None, help="Optional nice-to-have phrases file (one per line)")
    parser.add_argument("--top", type=int, default=TOP_DEFAULT, help="How many items to show in CLI tables")
    parser.add_argument("-o", "--output", type=Path, default=Path("report.html"), help="Output report HTML path")
    args = parser.parse_args()

    cv_text = read_text(args.cv)
    jd_text = read_text(args.job)

    # Term extraction
    cv_terms_list = extract_terms(cv_text)
    jd_terms_list = extract_terms(jd_text)

    cv_counts = Counter(cv_terms_list)
    jd_counts = Counter(jd_terms_list)

    cv_terms = set(cv_counts.keys())
    jd_terms = set(jd_counts.keys())

    # Phrase lists
    phrases = DEFAULT_NICE[:]
    if args.nice and args.nice.exists():
        phrases = [p.strip() for p in read_text(args.nice).splitlines() if p.strip()]

    cv_phrase_hits = find_phrases(cv_text, phrases)
    jd_phrase_hits = find_phrases(jd_text, phrases)

    # Overlap & gaps
    overlap, gaps = compute_overlap_and_gaps(cv_terms, jd_terms)

    # Sort overlap by JD frequency desc
    overlap_sorted = sorted(((t, jd_counts[t]) for t in overlap), key=lambda x: (-x[1], x[0]))

    # Score gaps by JD frequency (+ phrase bonus)
    gaps_scored_all = score_terms(gaps, jd_counts, jd_phrase_hits)
    gaps_scored = gaps_scored_all[: args.top]
    overlap_sorted_top = overlap_sorted[: args.top]

    # CLI output
    make_cli_tables(overlap_sorted_top, gaps_scored, len(jd_terms), len(cv_terms))

    # HTML report
    make_html_report(overlap_sorted, gaps_scored_all, cv_phrase_hits, jd_phrase_hits, args.output)

    # Bullet suggestions
    missing_terms_ranked = [t for (t, _score, _freq) in gaps_scored_all]
    bullets = suggest_bullets(missing_terms_ranked, max_bullets=10)

    if bullets:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown

        console = Console()
        md = "### Suggested CV bullets to address gaps\n" + "\n".join(f"- {b}" for b in bullets)
        console.print(Panel.fit(Markdown(md), title="Suggestions"))

    # Finish line
    print(f"\nSaved HTML report to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
# match.py