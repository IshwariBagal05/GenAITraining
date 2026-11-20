
# InsureClear
[![CI](https://github.com/IshwariBagal05/GenAITraining/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/IshwariBagal05/GenAITraining/actions/workflows/ci.yml)

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

**Winner:** config A (chunk size 400, top-k 3), 80% overall (12/15), against 73% (11/15)
for config B (chunk size 900, top-k 5). The gap is one question (Q1), so this is weak evidence.

- Both configs said "I don't know" on every unanswerable question (Q6, Q10, Q15) and invented nothing.
- Both refused Q7 and Q8. I searched the chunks: no page states a grace period for a late
  health renewal (the only grace period is for porting), and none mentions parents or
  dependents. So the refusals were correct and my eval rows were too optimistic.
- Q9: [what the retrieval command showed: free-look page missing from the top 3, or answer absent].
- Config B also missed Q1 and Q9 on keywords: with 900-character chunks the ulip page ranked
  above the free-look page for the LIC question.
- Retrieval hit is 100% for both, which is a lenient measure (any chunk from an expected page counts).
- Next: [fix Q7/Q8 labels or re-run, and improve retrieval for phone and online sales].


## Chat UI and rights timeline (Day 10)

![InsureClear UI](docs/ui_screenshot.png)

```bash
uvicorn app.main:app --reload     # terminal 1: API
streamlit run ui/app.py           # terminal 2: UI at http://localhost:8501
```

- **Ask** mode calls `/ask` and shows citations. **Agent** mode calls `/agent`, keeps memory per thread, and asks for approval before the refund calculator runs.
- 👍 / 👎 on each answer is saved to `data/feedback.jsonl`.
- **Your rights timeline** shows five steps for the selected policy type: policy received, free-look ends, claim intimation, insurer reply, escalation to Bima Bharosa / Ombudsman. Each step cites an IRDAI page, and `python -m app.timeline` checks that the quoted wording really appears in the downloaded page. Where the pages give no day count, none is shown.
- [One or two lines in your own words about what the check found, for example whether the 30-day count appears on your pages.]

## Run with Docker

1. Copy `.env.example` to `.env` and add a Groq or Gemini API key for `/ask` and Agent answers.
2. From the project root, run:

   ```bash
   docker compose up --build
   ```

3. Open the UI at <http://localhost:8501>. The API is available at
   <http://localhost:8000> (interactive docs at <http://localhost:8000/docs>).

Use `docker compose down` to stop the services. The UI connects to the API through
the Compose network; no API address change is needed in the sidebar.