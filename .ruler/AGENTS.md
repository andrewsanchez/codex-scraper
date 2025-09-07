# Project overview
- scripts for a variety of web scraping tasks.
- utilizes playwright, beautifulsoup, and httpx for scraping
- each scraping job is isolated in its own directory

## Implementation details
- create a new directory for each distinct scraping job
- ensure scripts are designed to be executed from the repo root
- Implement a function called `scrape()`
  - use Playwright first to understand the structure of the site
  - pages might load through JS or frames, so use Playwright to inspect the structure.
  - pages may load content dynamically through a script so inspect HTML to check links.
  - be sure to consider pagination and check for "Next" or similar buttons to ensure you find all links
  - use context=browser.new_context(ignore_https_errors=True)
- for static pages, fetch with `httpx` and parse with `BeautifulSoup`.
  - use verify=False with httpx
- use tqdm and print statements to log progress to stdout
- be sure to scrape respectfully and avoid getting rate limited
- Persist: write results to the output file requested by the user. Default to JSON AND a sqlite database.
- Execute: `uv run python <scraping-job-dir>/main.py`

## Output Schema & JSON
- Define a Pydantic model for scraped item before coding selectors. This makes the schema explicit and validated.
  - Where: `models.py` in the scraping job directory
- Example schema (adapt fields to the task):
  - Python
    from pydantic import BaseModel, HttpUrl
    class Item(BaseModel):
        title: str
        url: HttpUrl
        price: float | None = None  # normalized number
- Normalization tips:
  - Strip whitespace, decode entities, parse currency to numbers, format dates as ISO 8601, and ensure absolute URLs.
  - Use Optional for genuinely missing fields; avoid empty strings.
- Building outputs:
  - Create `items: list[Item]` and append validated instances as you extract.
  - For a single final JSON file: `json.dump([i.model_dump(mode="json") for i in items], f, ensure_ascii=False, indent=2)`.
  - For streaming/large jobs, prefer JSONL: write `i.model_dump_json()` per line.
- Quality checks:
  - Deduplicate by a stable key (e.g., URL) before writing.
  - Keep field names stable and lowercase_snake_case.
  - Fail loudly on schema errors during development; handle gracefully once stable.

## Project Structure & Module Organization
- Root contains Python code (`main.py`) and project metadata (`pyproject.toml`, `uv.lock`).

## Coding Style
- Use type hints and concise docstrings for public functions.
- Separate concerns: network calls via `httpx` (always set timeouts), parsing in pure functions (`bs4`), and orchestration in lightweight CLI/runner.
- write idiomatic, pythonic code that follows PEP 8 conventions
- always prefer a functional programming style
- write pure functions without side effects when appropriate
- include type hints for all function signatures
- use immutable data structures when appropriate
- use comprehensions and higher-order functions (map, filter, functools.reduce)
- avoid lambda functions
- do not write docstrings, comments, or print statements unless specifically requested.
- prefer pathlib.Path instead of os
- avoid handling errors try/except as this often leads to anti patterns
  - Easier to Ask Forgiveness than Permission
- always write comprehensive tests using pytest
  - check results by selecting and running specific tests with pytest -k

## Testing Guidelines
- Framework: `pytest` (add via `uv add pytest`).
- Location: `tests/` with files named `test_*.py`; mirror package structure.
- Run: `uv run pytest` (optionally add `-k <pattern>` to scope).
- Aim for meaningful coverage of parsing functions and HTTP edge cases; prefer fixture HTML over live network calls.
- Run `uv run mypy .` for type checking
