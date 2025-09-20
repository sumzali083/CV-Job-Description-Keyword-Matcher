# CV ↔ Job Description Keyword Matcher

A small Python script that compares your **CV** with a **job description** and shows:

- ✅ Keywords that appear in both  
- ⚠️ Keywords from the job description missing in your CV  
- ⭐ Optional “nice-to-have” skills if you provide a list  

It prints a clear report in the terminal and also saves an **HTML report** you can open in your browser.

---

## Example

**Terminal view**
Summary
Overlap terms: 12 Gaps: 8 JD unique terms: 45 CV unique terms: 39

Top Missing Terms (Gaps)

Term JD Freq Score
1 sql 5 5.00
2 ci/cd 3 4.50
...

yaml
Copy code


---

## Features
- Extracts keywords from both files (uses spaCy if installed, or a simple fallback)
- Finds overlaps and gaps
- Ranks missing terms by frequency in the job description
- Lets you define your own “nice-to-have” phrases
- Saves an `report.html` file with tables
- Suggests example CV bullet points for the missing terms

---

## Installation

Clone the repo and install the requirements:

```bash
git clone https://github.com/yourusername/cv-keyword-matcher.git
cd cv-keyword-matcher
pip install -r requirements.txt
For better keyword detection, install the small English spaCy model:

bash
Copy code
python -m spacy download en_core_web_sm
Files
cv.txt → your CV in plain text

job.txt → the job description text

nice.txt (optional) → one skill/phrase per line

match.py → the main script

Usage
Basic example:

bash
Copy code
python match.py --cv cv.txt --job job.txt -o report.html
With a list of nice-to-have skills:

bash
Copy code
python match.py --cv cv.txt --job job.txt --nice nice.txt --top 20 -o report.html
Arguments

--cv : path to CV file (text)

--job : path to job description file (text)

--nice : optional file of extra phrases to check

--top : number of terms to display (default = 20)

-o : output HTML file (default = report.html)

Output
Terminal:

Table of missing keywords

Table of overlapping keywords

Suggested bullet points

Browser:

Open report.html to see the full report

Why I built this
I wanted a quick way to check if my CV matches the keywords in job postings.
This project also gave me practice with:

Text processing in Python

Libraries like spaCy and Rich

Command-line arguments with argparse

Generating a simple HTML report
<img width="1852" height="952" alt="Screenshot 2025-09-20 155726" src="https://github.com/user-attachments/assets/dd3277c5-8b9d-4b07-951a-2ee7ff6eb697" />
