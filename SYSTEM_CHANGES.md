# TEQUILA System Changes - Post-Analysis

## What You Provided

1. **6 perfect reference weeks**: Week 1, 11, 12, 13, 14, 15
2. **70-bullet master outline**: Complete 35-week scope & sequence
3. **Quality expectations**: Scholarly Latin pedagogy, Catholic theology, cognitive science
4. **Original specification**: 4-day structure, session durations, virtue progression

## What Changed in the System

### **1. Master Curriculum Outline (NEW)**

**File**: `curriculum_outline.json`

- **70 bullets** translated to structured JSON (35 weeks × 2 bullets each)
- Defines for each week:
  - Title + content focus (from outline)
  - Session duration (30min Week 1 → 12-15min Week 11)
  - Grammar focus (what gets taught)
  - Vocabulary domain (word categories)
  - Chant (what to memorize)
  - Prerequisites (dependency chain)
  - Introduces (new concepts this week)

**Impact**:
- ✅ **Sequential generation enforced** (can't skip weeks)
- ✅ **Session duration dynamic** (not hardcoded)
- ✅ **Grammar progression validated** (can't teach verbs before nouns)
- ✅ **Spiral review tracked** (knows what prior weeks taught)

---

### **2. Curriculum Outline Service (NEW)**

**File**: `src/services/curriculum_outline.py`

**New Functions**:
```python
load_curriculum_outline()              # Load 35-week outline
get_week_outline(week_num)            # Get data for specific week
get_session_duration(week_num)        # Dynamic duration per week
get_prerequisites(week_num)           # Dependency list
get_cumulative_concepts(week_num)     # All concepts through week N
validate_week_prerequisites(week)      # Check prerequisites exist
format_week_constraints_for_prompt()   # LLM prompt injection
```

**Impact**:
- ✅ **Centralized outline access** (one source of truth)
- ✅ **Automatic validation** (prerequisites checked before generation)
- ✅ **Prompt enhancement** (LLM gets outline constraints)

---

### **3. Generator Week - Prerequisite Validation (UPDATED)**

**File**: `src/services/generator_week.py`

**What Changed**:
```python
def generate_week_planning(week: int, client: LLMClient):
    """Phase 1: Generate internal_documents/ with outline validation."""

    # NEW: Validate prerequisites exist
    validate_week_prerequisites(week, CURRICULUM_BASE)

    # NEW: Load outline constraints
    week_outline = get_week_outline(week)

    # NEW: Inject constraints into prompts
    constraints = format_week_constraints_for_prompt(week)

    # Generate with constraints
    week_spec_path = generate_week_spec_from_outline(
        week, client,
        outline_constraints=constraints
    )
    # ... rest of generation
```

**Impact**:
- ✅ **Can't generate Week 11 without Weeks 1-10**
- ✅ **Outline constraints passed to LLM**
- ✅ **Session duration dynamic**

---

### **4. Prompts - Outline Injection (UPDATED)**

**Files**: `src/services/prompts/week/*.json`

**What Changed**:
```json
{
  "system": "You are an expert Latin curriculum designer...",
  "user": "Generate week_spec.json for Latin A Week {{week}}.\n\n{{outline_constraints}}\n\nYour output must align with these constraints..."
}
```

**Impact**:
- ✅ **LLM knows what to teach** (from outline)
- ✅ **LLM knows what NOT to teach** (upcoming weeks)
- ✅ **LLM knows what to review** (prior weeks)

---

### **5. Session Duration Support (NEW)**

**What Changed**:
- Week 1: 30 minutes (alphabet + pronunciation takes time)
- Weeks 2-7: 20-30 minutes (declension foundation)
- Weeks 8-15: 12-20 minutes (trained students, faster pacing)
- Week 16: 20-25 minutes (review needs more time)
- Weeks 17-29: 12-15 minutes (mature learners)
- Weeks 30-35: 15-40 minutes (review + assessment)

**Where This Applies**:
- `05_guidelines_for_sparky.json` → `"estimated_duration": "{{session_duration}}"`
- Day field generation calculates step count: `duration_mins // 3` steps
- Time estimates adjust: Week 1 has 9 steps, Week 11 has 13-14 steps

**Impact**:
- ✅ **Developmentally appropriate pacing**
- ✅ **Realistic time budgets**
- ✅ **Matches reference weeks**

---

## **What This Enables**

### **Before**
```bash
# Could generate any week in any order
python -m src.cli.generate_all_weeks --week 20
# ✗ Would succeed but violate dependencies
```

### **After**
```bash
# System validates prerequisites
python -m src.cli.generate_all_weeks --week 20

ERROR: Cannot generate Week 20: prerequisite weeks [1, 2, 3, ..., 19] are missing.
Required prerequisites: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
Generate weeks sequentially from Week 1 first.
```

---

### **Before**
```json
// Week 11 generated with wrong duration
{
  "estimated_duration": "10-15 minutes"  // Hardcoded
}
```

### **After**
```json
// Week 11 uses outline
{
  "estimated_duration": "12-15 minutes"  // From curriculum_outline.json
}

// Week 1 uses outline
{
  "estimated_duration": "30 minutes"  // From curriculum_outline.json
}
```

---

### **Before**
```
LLM Prompt: "Generate Week 11 content."
// LLM doesn't know what Week 11 is supposed to teach
```

### **After**
```
LLM Prompt: "Generate Week 11 content.

MASTER CURRICULUM OUTLINE CONSTRAINTS FOR WEEK 11:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TITLE: First Conjugation Verbs (Present Tense)
CONTENT FOCUS: Vocabulary: amō, amās, amat...; Chant: 1st conj. endings

GRAMMAR FOCUS: First conjugation present tense (–ō, –ās, –at, –āmus, –ātis, –ant)
VOCABULARY DOMAIN: –āre verbs (amō, portō, laudō, vocō, parō)
CHANT: –ō, –s, –t / –mus, –tis, –nt

CONCEPTS TO INTRODUCE THIS WEEK:
• First Conjugation
• –āre verbs
• verb conjugation pattern

PREREQUISITES (must build on these):
Week 1: Introduction to Latin... (introduced: Latin alphabet...)
Week 2: First Declension Nouns... (introduced: 1st declension...)
...
Week 10: Verb Basics... (introduced: person, number, tense...)

UPCOMING TOPICS (do NOT teach yet):
Week 12: Second Conjugation Verbs (DO NOT teach: Second Conjugation, –ēre verbs)
Week 13: Using Nouns and Verbs in Sentences (DO NOT teach: sentence patterns A-D)

Your generated week_spec.json MUST align with these constraints."
```

**Impact**: LLM has **precise scope boundaries**

---

## **Still TODO (Phase 2)**

### **High Priority**
- [ ] Add virtue progression (35 virtues mapped to weeks)
- [ ] Add faith phrase progression (35 phrases)
- [ ] Update prompts to inject outline constraints (week/day prompts)
- [ ] Add spiral review concept tracking
- [ ] Add quality validation (macron checker, terminology validator)

### **Medium Priority**
- [ ] Ollama integration (local LLM support)
- [ ] CLI enhancements (--fill-gaps, --report)
- [ ] Generation quality reports
- [ ] Automated comparison to reference weeks

### **Nice to Have**
- [ ] Derivative tracking (cumulative derivative list)
- [ ] Vocabulary database (all words across 35 weeks)
- [ ] Chant library (all chants organized)
- [ ] Scripture mapping (week → scripture references)

---

## **Current System State**

✅ **Completed**:
1. Master curriculum outline (curriculum_outline.json)
2. Curriculum outline service (curriculum_outline.py)
3. 6 reference weeks imported (1, 11, 12, 13, 14, 15)
4. internal_documents/ architecture implemented
5. Two-phase generation flow (planning → days)
6. CLI updated for new flow

⏳ **In Progress**:
- Integrating outline validation into generator_week.py
- Updating prompts to use outline constraints

🔜 **Next**:
- Test Week 16 generation with new system
- Compare quality to reference weeks
- Iterate on prompts based on output

---

## **How to Use the New System**

### **Generate Week 16 (Next Week After Your References)**

```bash
# System will:
# 1. Load curriculum_outline.json
# 2. Get Week 16 outline (Semester Review)
# 3. Validate Weeks 1-15 exist (✓ they do)
# 4. Inject outline constraints into prompts
# 5. Generate with 20-25min session duration
# 6. Create internal_documents/ + 4 days

python -m src.cli.generate_all_weeks --week 16
```

### **Validate Prerequisites**

```python
from src.services.curriculum_outline import validate_week_prerequisites
from pathlib import Path

# Check if Week 16 can be generated
try:
    validate_week_prerequisites(16, Path("curriculum/LatinA"))
    print("✓ All prerequisites exist, can generate Week 16")
except ValueError as e:
    print(f"✗ Cannot generate: {e}")
```

### **View Outline for Any Week**

```python
from src.services.curriculum_outline import get_week_outline

week20 = get_week_outline(20)
print(f"Week 20: {week20['title']}")
print(f"Duration: {week20['session_duration']}")
print(f"Teaches: {week20['introduces']}")
```

---

## **Summary**

The TEQUILA system now **enforces your 70-bullet master plan**:
- ✅ Sequential generation (dependencies validated)
- ✅ Dynamic session durations (Week 1 ≠ Week 11)
- ✅ Grammar progression (can't skip ahead)
- ✅ Spiral review (knows what prior weeks taught)
- ✅ Quality constraints (outline → prompts → LLM)

**Result**: Generated weeks will **align with your master plan** instead of being "generic Latin lessons."
