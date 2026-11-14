
# InsureClear

## Project Description

InsureClear is an insurance information management project
that helps users understand insurance rules and policyholder
rights using information collected from official IRDAI sources.

## Problem Statement

Insurance information is spread across multiple pages.
Users may find it difficult to locate important rules,
deadlines, and complaint channels.

InsureClear organizes this information in one place and
provides simple search and lookup functionality.

## Features

- Display all insurance records
- Search insurance information by keyword
- Count records by insurance category
- Retrieve a record using its ID
- Access official source links

## Technology Stack

- Python
- JSON
- Git and GitHub
- VS Code

## Project Structure

- data/sample_records.json
- app/records.py
- app/cli.py
- requirements.txt
- .gitignore

## How to Run

1. Create a virtual environment.
2. Activate the environment.
3. Run:

   python -m app.cli

## Data Source

Insurance information is collected from official IRDAI
and Bima Bharosa pages.

## Disclaimer

This project is for educational and informational purposes.
Users should verify current insurance rules with official
IRDAI publications and their insurance company.

## LLM setup (Day 6)

1. Copy `.env.example` to `.env` and add your own Groq or Gemini key.
2. Set `LLM_PROVIDER=groq` or `gemini`.
3. Run `uvicorn app.main:app --reload` and use `POST /chat` at /docs.

Prompts live in `prompts/`; the prompt comparison is in `eval/prompt_compare.md`.

## Semantic search (Day 7)

```bash
pip install -r requirements.txt
python -m app.vectorstore          # builds the Chroma index (chroma_db/)
uvicorn app.main:app --reload      # then GET /search/semantic?q=your question
```

Chunks keep source, page and title. Results for my 10 questions are in `eval/search_results.md`.
