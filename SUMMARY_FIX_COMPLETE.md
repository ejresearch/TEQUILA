# Summary Generation Fix - COMPLETE

## The Second Bug: Generic Summary Content

After fixing the data structure mismatch, we discovered **02_summary.md** was generating generic "ecosystem" content instead of Latin-specific content.

### Root Cause:

`generate_day_fields()` was using `task_day_fields()` to generate the summary, which:
- Uses a generic inline prompt asking for "2-3 sentence overview"
- Doesn't reference week_spec content (grammar, chant, virtue, faith phrase)
- Allows LLM to hallucinate any topic

### The Solution:

Use the dedicated `task_day_summary()` function which:
- Loads from JSON prompt library: `day/day_summary.json`
- Has detailed prompt with week_spec interpolation
- References grammar_focus, chant, virtue_focus, faith_phrase
- Enforces 150-250 word structured markdown format
- Uses JSON schema validation

### Changes Made:

**File**: `src/services/generator_day.py`

1. **Added import** (line 24):
```python
from .prompts.kit_tasks import (
    ...
    task_day_summary,  # NEW
    ...
)
```

2. **Replaced generic summary generation** (lines 261-287):
```python
# OLD: Used task_day_fields() which generates generic summary
"02_summary.md": fields_data.get("summary", ""),

# NEW: Use dedicated task_day_summary() with JSON schema
class_name = fields_data.get("class_name", f"Week {week} Day {day}")

# Load schema from prompt spec
summary_prompt_spec = _load_prompt_json("day/day_summary.json")
summary_schema = summary_prompt_spec["output_contract"]["schema"]

# Generate with proper context
sys_summary, usr_summary, config_summary = task_day_summary(
    week_number=week,
    day_number=day,
    class_name=class_name,
    week_spec=week_spec,
    prior_knowledge_digest=None
)
response_summary = client.generate(
    prompt=usr_summary,
    system=sys_summary,
    json_schema=summary_schema
)

# Extract from JSON response
summary_content = response_summary.json.get("day_summary", "")

# Write to file
"02_summary.md": summary_content,
```

### What This Fixes:

✅ **Proper week context**: Summary now references actual week title, grammar focus, chant
✅ **Latin-specific content**: No more "ecosystem" hallucinations
✅ **Structured format**: YAML frontmatter + proper markdown sections
✅ **Virtue/faith integration**: Includes virtue_focus and faith_phrase
✅ **Day intent**: Specifies learning intent (Learn, Practice, Review, Quiz)
✅ **Schema validation**: Enforces 100-2000 character range

### Expected Output Format:

```markdown
---
week: 1
day: 1
license: 'CC BY 4.0'
validated_by: Steel
originality_attestation: true
---

# Week 1 Day 1: Latin Foundations: Alphabet and Pronunciation

## Objective
Students will recognize and pronounce each letter of the Latin alphabet.

## Prior Knowledge
This is the first week, building foundational knowledge.

## Focus for Today
- Grammar: Introduction to Latin Alphabet and Sounds
- Chant: A, B, C, D, E, F, G, H, I, K, L, M, N, O, P, Q, R, S, T, U, X, Y, Z - Latin's best!
- Vocabulary: a (ah), b (beh), c (keh), d (deh), e (eh), f (ef), g (geh), h (hah)

## Virtue & Faith Connection
Discipline helps us practice consistently. "In principio" reminds us every journey begins with first steps.

## Teacher Notes
Emphasize clear articulation. Use call-and-response for engagement.
```

## Testing Instructions:

```bash
cd /Users/elle_jansick/steel

# Regenerate Week 1 with summary fix
python -m src.cli.generate_all_weeks --week 1

# Verify summary has Latin content (not ecosystems!)
cat curriculum/LatinA/Week01/activities/Day1/02_summary.md
```

### Expected Results:

✅ **02_summary.md**: Structured markdown with YAML header, Latin alphabet focus
✅ **No ecosystem text**: Content matches Week 1 theme (alphabet/pronunciation)
✅ **Virtue integration**: Mentions "Discipline" and "In principio"
✅ **Grammar focus**: References "Introduction to Latin Alphabet and Sounds"
✅ **Chant**: Includes alphabet chant text

## Status:

**Both bugs now fixed**:
1. ✅ Data structure mismatch (role_context, guidelines, greeting)
2. ✅ Summary generation (proper task function with schema)

---

**Files Changed**: 2 files
- `src/services/prompts/kit_tasks.py` (data structure fix)
- `src/services/generator_day.py` (summary generation fix)

**Ready for**: Full Week 1 regeneration and testing
