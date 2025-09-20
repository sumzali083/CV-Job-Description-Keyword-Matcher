import re
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def tokenize(text):
    # lowercase, remove non-letters, split, drop short words
    words = re.findall(r"\\b[a-zA-Z]{4,}\\b", text.lower())
    return set(words)

def main():
    # Load CV and Job text
    base = Path(__file__).parent
    cv_text = (base / "cv.txt").read_text(encoding="utf-8")
    job_text = (base / "job.txt").read_text(encoding="utf-8")

    cv_terms = tokenize(cv_text)
    job_terms = tokenize(job_text)

    overlap = cv_terms & job_terms
    missing = job_terms - cv_terms

    console.print("[bold green]Keyword Match Report[/bold green]\n")

    table = Table(title="Match Results")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Terms", style="white")

    table.add_row("Matched (in CV)", ", ".join(sorted(overlap)) or "None")
    table.add_row("Missing (in JD but not CV)", ", ".join(sorted(missing)) or "None")

    console.print(table)

    # Save to report.txt for record
    with open(base / "report.txt", "w", encoding="utf-8") as f:
        f.write("Matched terms:\n")
        f.write(", ".join(sorted(overlap)) + "\n\n")
        f.write("Missing terms:\n")
        f.write(", ".join(sorted(missing)) + "\n")

if __name__ == "__main__":
    main()
