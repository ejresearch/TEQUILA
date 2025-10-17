# `view` Command - Curriculum Content Viewer

The `view` command lets you inspect generated curriculum content without regenerating it.

## Usage

### Via Make (Recommended)
```bash
make view WEEK=1                         # View all Week 1 content
make view WEEK=7.2                       # View Week 7 Day 2 only
make view WEEK=7 SCOPE=internal          # View Week 7 internal docs
make view WEEK=8 SCOPE=assets            # View Week 8 assets
make view WEEK=19 SCOPE=class            # View Week 19 class material (all days)
make view WEEK=22.2 SCOPE=class          # View Week 22 Day 2 class material
```

### Direct Python Call
```bash
python -m src.cli.view 1                 # View all Week 1 content
python -m src.cli.view 7.2               # View Week 7 Day 2
python -m src.cli.view 7 internal        # View Week 7 internal docs
python -m src.cli.view 8 assets          # View Week 8 assets
python -m src.cli.view 19 class          # View Week 19 class material
python -m src.cli.view 22.2 class        # View Week 22 Day 2 class material
```

### Via Shell Wrapper (optional)
```bash
# Add to your PATH:
export PATH="$PATH:/Users/elle_jansick/steel/bin"

# Then use directly:
view 1                 # View all Week 1 content
view 7.2               # View Week 7 Day 2
view 7 internal        # View Week 7 internal docs
view 19 class          # View Week 19 class material
```

## Scopes

### Full Week (no scope)
Shows everything for a week:
```bash
view 1
```
Output includes:
- Internal documents (week_spec.json, week_summary.md, role_context.json)
- All 4 days (class names, summaries, grade levels, Sparky's greetings, teacher support docs)
- Assets (QuizPacket, TeacherKey)

### Specific Day
Shows all content for a single day:
```bash
view 7.2
```
Output includes:
- Class name
- Summary
- Grade level
- Sparky's greeting
- All 6 teacher support documents

### Internal Documents Only
Shows week planning documents:
```bash
view 7 internal
```
Output includes:
- week_spec.json
- week_summary.md
- role_context.json
- phase0_research.json (if available)
- generation_log.json

### Assets Only
Shows week assets:
```bash
view 8 assets
```
Output includes:
- QuizPacket.txt
- TeacherKey.txt
- Any other asset files

### Class Material (All Days)
Shows classroom teaching content for all 4 days:
```bash
view 19 class
```
Output includes for each day:
- Class name
- Summary
- Grade level
- Sparky's greeting
- All 6 teacher support documents

### Class Material (Single Day)
Shows classroom teaching content for one day:
```bash
view 22.2 class
```
Output includes:
- Class name
- Summary
- Grade level
- Sparky's greeting
- All 6 teacher support documents

## Examples

### Quick inspection of a week
```bash
make view WEEK=3
# Shows everything - useful for QA review
```

### Compare two days
```bash
make view WEEK=5.1 SCOPE=class > day1.txt
make view WEEK=5.2 SCOPE=class > day2.txt
diff day1.txt day2.txt
```

### Review internal planning for consistency
```bash
for i in 1 11 12 13 14 15; do
  echo "=== Week $i ==="
  make view WEEK=$i SCOPE=internal | grep "grammar_focus"
done
```

### Extract vocabulary from a week
```bash
make view WEEK=3 | grep -A 20 "vocabulary_key_document"
```

### Review all quiz packets
```bash
for i in 1 11 12 13 14 15; do
  make view WEEK=$i SCOPE=assets | grep -A 50 "QuizPacket"
done
```

## Output Format

All output is formatted for readability:
- **Headers**: `================================================================================`
- **File labels**: `📄 filename.txt`
- **Section labels**: `📚 Week X - Internal Documents`
- **JSON**: Pretty-printed with indentation
- **Text/Markdown**: Raw content preserved

## Error Handling

If a week hasn't been generated:
```bash
$ make view WEEK=25
❌ Week 25 not found at curriculum/LatinA/Week25
   Generate it first with: make gen WEEKS=25
```

If an invalid scope is specified:
```bash
$ make view WEEK=7 SCOPE=invalid
❌ Unknown scope: invalid
   Valid scopes: internal, assets, class
```

## Notes

- Week numbers must be between 1 and 35
- Day numbers must be between 1 and 4
- Week must exist in `curriculum/LatinA/WeekXX/` before viewing
- JSON files are automatically pretty-printed
- Binary files show a warning instead of content
- The command is read-only and never modifies files

## Integration with `gen`

Typical workflow:
```bash
# Generate a week
make gen WEEKS=4

# View the results
make view WEEK=4

# View specific day for detailed inspection
make view WEEK=4.2 SCOPE=class

# Check internal planning
make view WEEK=4 SCOPE=internal
```
