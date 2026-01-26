# CLAUDE.md - Project Instructions for AI Assistants

## CRITICAL: Personal Data Protection

### General Rule: NEVER commit personal data to git

Personal data includes:
- **Contact information**: names, phone numbers, emails, addresses
- **Message content**: texts, DMs, emails, chat logs
- **Usage data**: who someone talks to, when, how often
- **Personal identifiers**: usernames tied to real identity, account IDs
- **Sensitive content**: health, finances, relationships, location history
- **Generated reports/analysis** containing any of the above

### Before ANY git operation (add, commit, push):
1. Run `git status` and review EVERY file being staged
2. Ask: "Could this file contain personal data about the user or anyone else?"
3. If yes or uncertain: **DO NOT add it** - ask the user first
4. Check `.gitignore` covers sensitive file patterns
5. When in doubt: "This file may contain personal data. Should I exclude it?"

### The "safekeeping" trap:
- "Save for safekeeping" does NOT mean commit to a public repo
- Personal data belongs in local storage, not version control
- Git history is permanent - force-push doesn't fully delete
- If user wants to preserve something personal, suggest local backup, NOT git

### Red flags - always ask before committing:
- Files with user's name in filename (e.g., `*_jasmine*`, `*_personal*`)
- Output/generated files from data processing scripts
- JSON/CSV files that might contain contact lists or logs
- HTML reports generated from personal data
- Screenshots that might show private content
- Any file in `output/`, `data/`, `results/`, `exports/` directories
- Config files with API keys, tokens, or credentials

---

## Project-Specific: iMessage Wrapped

This project processes **personal iMessage data**. ALL output is sensitive.

### NEVER commit:
- `output/` directory or anything in it
- `wrapped_*.html` reports
- `*_jasmine*` or `*_personal*` files
- `contacts.json` with real contact mappings
- `response_reminder.py` contact lists (contains phone numbers)
- `dismissed_messages.json`

### Safe to commit:
- Source code (`.py` files without hardcoded personal data)
- `CLAUDE.md`, `README.md`, `requirements.txt`
- Preview images (already approved by user)
- `.gitignore`

### Pre-commit checklist for this project:
```
[ ] No files in output/ being committed
[ ] No *_jasmine* or *_personal* files
[ ] No contacts.json with real names/numbers
[ ] No HTML reports with real message data
[ ] No phone numbers or contact names in code
[ ] Checked git diff for any personal data in changes
```

## When User Asks to Commit

Always verify: "I'll commit [specific files]. This excludes personal data. Correct?"

---

## Package Management

If available, use `uv` for all Python package management:

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run scripts
uv run python main.py
uv run python -c "import nltk; nltk.download('punkt')"
```

Always prefer `uv run` over activating the virtual environment manually.

## Development Notes

### Avoiding Expensive LLM Regeneration

The LLM insights feature uses ~250k tokens per run. During development:

- **LLM is disabled by default** - use `--llm` flag only when needed
- **Don't use `--regenerate-llm`** unless you need fresh LLM output
- Only generate or regenerate when changing prompts or message extraction logic
