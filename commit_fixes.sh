#!/bin/bash
cd /Users/elle_jansick/steel

# Stage the modified files
git add .env
git add src/services/generator_week.py
git add src/services/prompts/kit_tasks.py
git add src/services/generator_day.py

# Create commit
git commit -m "$(cat <<'EOF'
fix: migrate all day prompts to JSON library and resolve generation issues

## API Configuration
- Increase API timeout from 30s to 300s for complex generations
- Increase max_tokens from 3000 to 4000

## Scaffold Overwrite Bug
- Remove redundant scaffold_week() calls that overwrote LLM content
  - Fixed generate_week_spec_from_outline() line 256
  - Fixed generate_role_context() line 366
  - Fixed generate_assets() line 434
- Ensures LLM-generated Week_Spec files preserve real content

## JSON Prompt Library Migration
- Replace missing .txt prompt files with JSON prompt library
- task_day_role_context (lines 1585-1614): Load from day/role_context.json
- task_day_guidelines (lines 1657-1699): Load from day/guidelines.json
- task_day_greeting (lines 1848-1894): Load from day/greeting.json
- Fix JSON schema required array for task_day_role_context
- Fix generator_day.py greeting response handling (lines 262-270)

## Day 4 Assessment
- Add hybrid Markdown+JSON parser for quiz generation (lines 445-488)
- Properly extract quiz_markdown and answer_key_min from response

All day field files now use prompt library architecture with proper
variable interpolation and schema enforcement.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Show status
git status
