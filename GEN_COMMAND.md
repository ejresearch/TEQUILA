# `gen` Command - Flexible Week Generator

The `gen` command provides a clean, flexible way to generate curriculum weeks.

## Usage

### Via Make (Recommended)
```bash
make gen WEEKS=3              # Generate Week 3
make gen WEEKS=3,5,7          # Generate Weeks 3, 5, and 7
make gen WEEKS=3-10           # Generate Weeks 3 through 10
make gen WEEKS=1-5,11-15      # Generate Weeks 1-5 and 11-15
```

### Direct Python Call
```bash
python -m src.cli.gen 3              # Generate Week 3
python -m src.cli.gen 3,5,7          # Generate Weeks 3, 5, and 7
python -m src.cli.gen 3-10           # Generate Weeks 3 through 10
python -m src.cli.gen 1-5,11-15      # Generate Weeks 1-5 and 11-15
```

### Via Shell Wrapper (optional)
```bash
# Add to your PATH:
export PATH="$PATH:/Users/elle_jansick/steel/bin"

# Then use directly:
gen 3              # Generate Week 3
gen 3,5,7          # Generate Weeks 3, 5, and 7
gen 3-10           # Generate Weeks 3 through 10
gen 1-5,11-15      # Generate Weeks 1-5 and 11-15
```

## Examples

### Generate a single week
```bash
make gen WEEKS=4
# Output: Generates Week 4 only
```

### Generate specific weeks
```bash
make gen WEEKS=2,4,6,8
# Output: Generates Weeks 2, 4, 6, and 8
```

### Generate a range
```bash
make gen WEEKS=10-15
# Output: Generates Weeks 10, 11, 12, 13, 14, 15
```

### Mix ranges and specific weeks
```bash
make gen WEEKS=1-3,5,7-9,11
# Output: Generates Weeks 1, 2, 3, 5, 7, 8, 9, 11
```

### Generate all gold standard weeks
```bash
make gen WEEKS=1,11-15
# Output: Generates Weeks 1, 11, 12, 13, 14, 15
```

## Output

For each week, the command will:
1. Run PHASE 0: Research & Planning (12 API calls)
2. Generate internal_documents/ (week_spec.json, week_summary.md, role_context.json)
3. Run PHASE 2: Day Generation (4 days × 7 fields = 28 files)
4. Validate structure
5. Export to curriculum/LatinA/exports/WeekXX.zip

## Old Commands (Still Available)

These commands still work but are less flexible:

```bash
make gen-week WEEK=11        # Generate single week (old way)
make gen-range FROM=1 TO=5   # Generate range (old way)
make gen-all                 # Generate all 35 weeks (EXPENSIVE!)
```

## Error Handling

Invalid specifications will show helpful error messages:

```bash
$ make gen WEEKS=50
Error: Week number must be between 1 and 35, got 50
```

```bash
$ make gen WEEKS=10-5
Error: Invalid range: 10-5 (start > end)
```

## Notes

- Week numbers must be between 1 and 35
- Weeks are generated sequentially in the order specified
- Each week costs approximately $1-2 in API calls
- Generated content is saved to `curriculum/LatinA/WeekXX/`
- Exports are saved to `curriculum/LatinA/exports/WeekXX.zip`
- Logs are saved to `logs/`
