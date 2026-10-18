# For the expertise-navigator teammate

You do **not** need to install or run `company_match`.

1. Open `latest.md` for a human checklist, or
2. Load `latest.json` in your code, or
3. **Preferred for backend:** load `companies/latest_batch.json` (full company dict + `match.reasoning` + `website_info`).

Use `teammate_queue` in order:
- run navigator search with each `run_first` query
- then `run_later`
- keep `source_ref` / reasons / score_breakdown for traceability

Schema version: 1.1
