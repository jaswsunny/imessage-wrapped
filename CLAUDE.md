# CLAUDE.md - Project Instructions for AI Assistants

## CRITICAL: Personal Data Protection

This project processes **personal iMessage data**. Treat all output as sensitive.

### NEVER commit or push:
- `output/` directory or any files within it
- Any file containing contact names, phone numbers, or message content
- Files matching `*_jasmine*`, `*_personal*`, `wrapped_*.html`
- `contacts.json` with real contact mappings
- Any HTML reports generated from real data
- Screenshots containing message content or contact names

### Before ANY git operation (add, commit, push):
1. Run `git status` and review EVERY file being staged
2. If a file might contain personal data, **DO NOT add it** - ask the user first
3. Check `.gitignore` covers the file pattern
4. When in doubt, ask: "This file may contain personal data. Should I exclude it?"

### The "safekeeping" trap:
- "Save for safekeeping" does NOT mean commit to a public repo
- Personal data belongs in local storage, not version control
- If user wants to preserve something personal, suggest local backup, NOT git

### Pre-commit checklist:
```
[ ] No files in output/ being committed
[ ] No *_jasmine* or *_personal* files
[ ] No contacts.json with real names/numbers
[ ] No HTML reports with real message data
[ ] No screenshots showing personal conversations
```

## Project Context

This is an iMessage analytics tool. The code is public but all generated output is private.

- `output/` - Contains personal message analysis (NEVER commit)
- `*.html` reports - Contains personal data (NEVER commit)
- `contacts.json` in output/ - Maps phone numbers to names (NEVER commit)
- Preview images in repo root - Intentionally public, user-approved

## When User Asks to Commit

Always verify: "I'll commit [files]. This excludes any personal data in output/. Correct?"
