#!/bin/bash
# Commit script for data structure mismatch fix

cd /Users/elle_jansick/steel

git add -A

git commit -m "$(cat <<'EOF'
fix: correct week_spec data structure key access across all prompt functions

PROBLEM:
Week_Spec file uses prefixed keys ("01_metadata.json", "03_vocabulary.json")
but code was accessing with flat keys ("metadata", "vocabulary"), causing:
- Empty role_context, guidelines, greeting files
- Silent failures with fallback minimal content
- Incomplete variable interpolation in prompts

ROOT CAUSE:
Week generation creates compiled spec with prefixed keys, but day generation
functions used flat key names, returning {} for all lookups.

SOLUTION:
Updated all week_spec.get() calls in kit_tasks.py to use correct prefixed keys:
- "metadata" → "01_metadata.json"
- "objectives" → "02_objectives.json"
- "vocabulary" → "03_vocabulary.json"
- "chant" → "05_chant.json"
- "spiral_links" → "09_spiral_links.json"
- "misconception_watchlist" → "11_misconception_watchlist.json"

FUNCTIONS FIXED:
1. task_day_role_context (lines 1593)
2. task_day_guidelines (lines 1677)
3. task_day_greeting (lines 1864)
4. task_day_fields (lines 1755-1756)
5. task_day_document (lines 1789-1793)
6. task_day_summary (lines 762-782)
7. task_role_context (lines 583-584)
8. task_assets (lines 619-622)

TESTING:
Run: python -m src.cli.generate_all_weeks --week 1
Verify: Day1/04_role_context.json, 05_guidelines_for_sparky.md, 07_sparkys_greeting.txt have content

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo "✅ Committed data structure fix"
git log -1 --oneline
