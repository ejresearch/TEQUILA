"""PHASE 0: Research & Planning Module

This module implements the 12-step research cascade that runs BEFORE week generation.
Each function is a separate LLM call that gathers data to inform pedagogically-sound content.

Flow:
  CALL #0.1-0.10: Research & Planning
  CALL #0.11-0.12: Curriculum Alignment with Gold Standard

Cost: ~$0.45-0.57 per week
Time: ~3-5 minutes per week
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


# ============================================================================
# PHASE 0: RESEARCH & PLANNING (Calls #0.1 - #0.10)
# ============================================================================

def task_locate_week_entry(week_number: int) -> dict:
    """
    CALL #0.1: Locate and extract week entry from curriculum outline.

    Model: GPT-4o-mini (simple extraction)
    Temperature: 0.1
    Cost: ~$0.002

    Args:
        week_number: Week to extract (1-35)

    Returns:
        Week entry with all fields
    """
    outline_path = Path("curriculum/curriculum_outline.json")

    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    week_key = f"week_{week_number:02d}"

    if week_key not in outline:
        raise ValueError(f"Week {week_number} not found in curriculum_outline.json")

    week_entry = outline[week_key]

    # Add extraction metadata
    week_entry['_metadata'] = {
        'extracted_at': datetime.now().isoformat(),
        'source': 'curriculum/curriculum_outline.json',
        'extraction_method': 'direct_read'
    }

    return week_entry


def task_backward_analysis(week_number: int, llm_client) -> dict:
    """
    CALL #0.2: Analyze all prior weeks to understand cumulative knowledge.

    Model: GPT-4o
    Temperature: 0.2
    Cost: ~$0.03

    Args:
        week_number: Current week
        llm_client: OpenAI client

    Returns:
        Backward analysis with cumulative vocabulary, grammar, student state
    """
    outline_path = Path("curriculum/curriculum_outline.json")

    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    # Read all prior weeks
    prior_weeks = []
    for i in range(1, week_number):
        week_key = f"week_{i:02d}"
        if week_key in outline:
            prior_weeks.append(outline[week_key])

    # Build prompt
    sys = """You are Steel, curriculum analyst for Classical Latin.

Analyze all prior weeks to determine what students know entering this new week.

Return JSON with:
{
  "prior_weeks_reviewed": [list of week numbers],
  "cumulative_latin_vocabulary": [
    {"word": "salve", "week_introduced": 1, "part_of_speech": "interjection", "mastery_expected": true}
  ],
  "cumulative_grammar_concepts": [
    {"concept": "Latin alphabet", "week_introduced": 1, "mastery_level": "recognition"}
  ],
  "student_knowledge_state": "summary of what students know",
  "common_mistakes_by_now": ["mistake 1", "mistake 2"],
  "spiral_review_target_percentage": 0.25
}"""

    usr = f"""Analyze prior weeks for Week {week_number}.

PRIOR WEEKS DATA:
{json.dumps(prior_weeks, indent=2)}

Provide complete backward analysis."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.2
    }

    return result


def task_forward_analysis(week_number: int, llm_client) -> dict:
    """
    CALL #0.3: Preview future weeks to identify dependencies.

    Model: GPT-4o
    Temperature: 0.2
    Cost: ~$0.03

    Args:
        week_number: Current week
        llm_client: OpenAI client

    Returns:
        Forward analysis with future dependencies
    """
    outline_path = Path("curriculum/curriculum_outline.json")

    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    # Read next 5 weeks
    future_weeks = []
    for i in range(week_number + 1, min(week_number + 6, 36)):
        week_key = f"week_{i:02d}"
        if week_key in outline:
            future_weeks.append(outline[week_key])

    sys = """You are Steel, curriculum forward planner for Classical Latin.

Analyze future weeks to identify what THIS week must prepare for.

Return JSON with:
{
  "future_weeks_previewed": [list of week numbers],
  "upcoming_topics": [
    {"week": 3, "title": "...", "dependency_on_current_week": "..."}
  ],
  "prerequisites_this_week_must_establish": [
    "Mastery of X for Week Y",
    "Understanding of Z for Week W"
  ],
  "vocabulary_seeds_for_future": [
    {"word": "puella", "future_use": "Used in Week 3 plural exercises"}
  ]
}"""

    usr = f"""Analyze future weeks after Week {week_number}.

FUTURE WEEKS DATA:
{json.dumps(future_weeks, indent=2)}

Provide complete forward analysis."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.2
    }

    return result


def task_pedagogical_benchmarking(week_entry: dict, llm_client) -> dict:
    """
    CALL #0.4: Research how classical Latin curricula teach this topic.

    Model: o1-mini (REASONING MODEL)
    Temperature: N/A (o1 doesn't use temperature)
    Cost: ~$0.06

    Args:
        week_entry: Week data from #0.1
        llm_client: OpenAI client (must support o1-mini)

    Returns:
        Pedagogical research findings
    """
    topic = week_entry['title']
    grammar = ', '.join(week_entry.get('grammar_topics', []))

    # o1-mini uses different API - no system prompt, just user prompt
    usr = f"""RESEARCH TASK: How do classical Latin curricula teach '{topic}' to Grade 3 students (ages 8-9)?

WEEK CONTEXT:
- Title: {topic}
- Grammar Topics: {grammar}
- Grade Level: 3-5 (ages 8-10)

RESEARCH PROTOCOL:
1. Analyze Logos Latin approach
2. Analyze Latin for Children (Classical Academic Press) approach
3. Analyze Traditional Catholic school methods
4. Identify standard vocabulary for this grammar topic
5. Identify time-tested chants/paradigms
6. List common misconceptions students have

Return JSON with:
{{
  "research_question": "How do classical Latin curricula teach '{topic}' to Grade 3?",
  "logos_latin_approach": "detailed description",
  "latin_for_children_approach": "detailed description",
  "traditional_catholic_school_approach": "detailed description",
  "standard_vocabulary_for_this_topic": ["word1", "word2"],
  "time_tested_chants": ["chant pattern"],
  "common_misconceptions": ["misconception with correction"],
  "reasoning_trace": "explain your analysis process"
}}

CRITICAL: This is CLASSICAL LATIN curriculum. Research should focus on Latin declensions, conjugations, cases - NOT modern languages."""

    try:
        response = llm_client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": usr}
            ]
        )

        result = json.loads(response.choices[0].message.content)
    except Exception as e:
        # Fallback to GPT-4o if o1-mini not available
        print(f"  ⚠ o1-mini not available, falling back to GPT-4o: {e}")
        response = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a classical Latin pedagogy researcher."},
                {"role": "user", "content": usr}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'o1-mini (or gpt-4o fallback)'
    }

    return result


def task_vocabulary_determination(
    week_entry: dict,
    backward: dict,
    forward: dict,
    pedagogy: dict,
    llm_client
) -> dict:
    """
    CALL #0.5: Determine final vocabulary list with reasoning.

    Model: o1-mini (REASONING MODEL)
    Temperature: N/A
    Cost: ~$0.06

    Args:
        week_entry: Week data
        backward: Backward analysis
        forward: Forward analysis
        pedagogy: Pedagogical research
        llm_client: OpenAI client

    Returns:
        Vocabulary plan with rationale for each word
    """
    usr = f"""VOCABULARY DETERMINATION TASK for Week {week_entry['week']}: {week_entry['title']}

CONTEXT:
Grammar Topics: {', '.join(week_entry.get('grammar_topics', []))}
Suggested Vocab (from outline): {week_entry.get('new_vocab', [])}

PRIOR KNOWLEDGE (from backward analysis):
Students already know: {[v['word'] for v in backward.get('cumulative_latin_vocabulary', [])]}

FUTURE NEEDS (from forward analysis):
{json.dumps(forward.get('vocabulary_seeds_for_future', []), indent=2)}

PEDAGOGICAL RESEARCH:
Standard vocabulary for this topic: {pedagogy.get('standard_vocabulary_for_this_topic', [])}

REASONING TASK:
1. Evaluate whether suggested vocabulary matches the grammar topic
2. Check if words are Classical Latin (NOT Spanish, French, Italian)
3. Ensure words are age-appropriate for Grade 3
4. Determine if words align with classical pedagogy standards
5. Calculate spiral review percentage (should be 20-40%)

Return JSON with:
{{
  "vocabulary_reasoning": "explain your decision process",
  "new_latin_words": [
    {{
      "word": "puella",
      "english": "girl",
      "part_of_speech": "noun",
      "declension": "1st",
      "gender": "feminine",
      "rationale": "why this word for this topic",
      "difficulty": "easy|medium|hard",
      "future_dependency": "which future weeks need this"
    }}
  ],
  "recycled_latin_words": [
    {{
      "word": "salve",
      "originally_taught_week": 1,
      "spiral_purpose": "why reviewing this"
    }}
  ],
  "alignment_check": {{
    "matches_grammar_topic": true,
    "supports_faith_integration": true,
    "age_appropriate": true,
    "classical_pedagogy_aligned": true,
    "NO_SPANISH_WORDS": true
  }}
}}

CRITICAL CHECKS:
- Are ALL words Classical Latin? (YES: puella, amo, pax | NO: levantarse, ducharse)
- Do words match the grammar topic? (1st declension week needs -a nouns, NOT verbs)
- Are there ANY Spanish words? If YES, REJECT them immediately."""

    try:
        response = llm_client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": usr}
            ]
        )
        result = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠ o1-mini not available, falling back to GPT-4o: {e}")
        response = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Classical Latin curriculum vocabulary expert."},
                {"role": "user", "content": usr}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'o1-mini (or gpt-4o fallback)'
    }

    return result


def task_session_duration_calculation(week_number: int) -> dict:
    """
    CALL #0.6: Calculate appropriate session duration based on week.

    Model: None (rule-based)
    Cost: $0.00

    Args:
        week_number: Current week

    Returns:
        Session duration plan
    """
    if week_number <= 8:
        duration = 13  # 12-15 minutes for novice weeks
        rationale = "Weeks 1-8: Novice attention span, building stamina"
    elif week_number <= 20:
        duration = 18  # 15-20 minutes for intermediate weeks
        rationale = "Weeks 9-20: Building stamina, more content"
    else:
        duration = 23  # 20-25 minutes for advanced weeks
        rationale = "Weeks 21-35: Established routine, complex topics"

    return {
        "week_number": week_number,
        "recommended_duration_minutes": duration,
        "rationale": rationale,
        "time_breakdown": {
            "greeting_and_spiral": 3,
            "chant_practice": 3,
            "grammar_instruction": duration - 10,
            "guided_practice": 3,
            "virtue_closure": 1
        },
        "_metadata": {
            "generated_at": datetime.now().isoformat(),
            "method": "rule_based"
        }
    }


def task_virtue_faith_integration(week_entry: dict, llm_client) -> dict:
    """
    CALL #0.7: Plan virtue and faith integration strategy.

    Model: GPT-4o
    Temperature: 0.3
    Cost: ~$0.03

    Args:
        week_entry: Week data
        llm_client: OpenAI client

    Returns:
        Virtue/faith integration plan
    """
    virtue = week_entry.get('virtue_focus', '')
    faith_phrase = week_entry.get('faith_phrase', '')

    sys = """You are Steel, integrating Catholic virtue formation with Latin study.

Return JSON with:
{
  "virtue_focus": "virtue name",
  "virtue_connection_to_language_learning": "how this virtue relates to learning Latin",
  "scripture_reference": {
    "passage": "Book Chapter:Verse",
    "text": "quoted text",
    "application": "how it applies to this week"
  },
  "faith_phrase": "Latin phrase",
  "faith_phrase_explanation": "meaning and usage",
  "liturgical_connection": "connection to Mass/prayer",
  "virtue_practice_in_lesson": ["specific practice 1", "practice 2"]
}"""

    usr = f"""Plan virtue and faith integration for:
Virtue: {virtue}
Faith Phrase: {faith_phrase}
Week Topic: {week_entry.get('title', '')}

Provide complete integration strategy."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.3
    }

    return result


def task_assessment_design(week_entry: dict, vocab_plan: dict, llm_client) -> dict:
    """
    CALL #0.8: Design Day 4 quiz and assessment strategy.

    Model: GPT-4o
    Temperature: 0.25
    Cost: ~$0.03

    Args:
        week_entry: Week data
        vocab_plan: Vocabulary plan from #0.5
        llm_client: OpenAI client

    Returns:
        Assessment plan
    """
    sys = """You are Steel, designing Grade 3 Latin assessments.

Return JSON with:
{
  "day_4_quiz_components": [
    {
      "component": "Vocabulary Recall",
      "format": "description",
      "words_tested": ["word1", "word2"],
      "mastery_target": "percentage or description"
    }
  ],
  "success_indicators": ["indicator 1", "indicator 2"],
  "preparation_for_next_week": "how this assessment prepares for Week N+1"
}"""

    usr = f"""Design assessment for Week {week_entry['week']}: {week_entry['title']}

Vocabulary to assess: {[w['word'] for w in vocab_plan.get('new_latin_words', [])]}
Grammar Topics: {week_entry.get('grammar_topics', [])}

Provide complete assessment plan."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.25,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.25
    }

    return result


def task_differentiation_planning(week_entry: dict, vocab_plan: dict, llm_client) -> dict:
    """
    CALL #0.9: Plan differentiation for struggling/advanced students.

    Model: GPT-4o
    Temperature: 0.3
    Cost: ~$0.03

    Args:
        week_entry: Week data
        vocab_plan: Vocabulary plan
        llm_client: OpenAI client

    Returns:
        Differentiation plan
    """
    sys = """You are Steel, planning differentiated instruction for Grade 3 Latin.

Return JSON with:
{
  "struggling_students": {
    "scaffolds": ["scaffold 1", "scaffold 2"],
    "modified_success_criteria": "adjusted expectations"
  },
  "advanced_students": {
    "extensions": ["extension 1", "extension 2"],
    "advanced_practice": "description"
  },
  "english_language_learners": {
    "pronunciation_support": ["support 1", "support 2"],
    "vocabulary_support": "description"
  }
}"""

    usr = f"""Plan differentiation for Week {week_entry['week']}: {week_entry['title']}

Vocabulary: {[w['word'] for w in vocab_plan.get('new_latin_words', [])]}
Grammar: {week_entry.get('grammar_topics', [])}

Provide complete differentiation plan."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.3
    }

    return result


def task_materials_planning(vocab_plan: dict, assessment: dict) -> dict:
    """
    CALL #0.10: Plan physical/digital materials needed.

    Model: None (rule-based from vocab + assessment)
    Cost: $0.00

    Args:
        vocab_plan: Vocabulary plan
        assessment: Assessment plan

    Returns:
        Materials list
    """
    new_words = [w['word'] for w in vocab_plan.get('new_latin_words', [])]
    recycled_words = [w['word'] for w in vocab_plan.get('recycled_latin_words', [])]

    return {
        "chant_charts": [
            {
                "title": "Week Paradigm Chart",
                "content": "To be determined from grammar topic",
                "format": "Large poster, laminated"
            }
        ],
        "flashcard_sets": [
            {
                "set_name": "New Vocabulary",
                "cards": new_words,
                "format": "3x5 index cards, Latin front / English + pronunciation back"
            },
            {
                "set_name": "Review Vocabulary",
                "cards": recycled_words,
                "format": "Same style, marked 'REVIEW'"
            }
        ],
        "worksheets": [
            {
                "title": "Practice Sheet",
                "exercises": ["Fill in the blank", "Translation", "Parsing"]
            }
        ],
        "visual_aids": [
            "Picture cards for concrete nouns",
            "Grammar charts"
        ],
        "_metadata": {
            "generated_at": datetime.now().isoformat(),
            "method": "rule_based"
        }
    }


# ============================================================================
# PHASE 0.5: CURRICULUM ALIGNMENT (Calls #0.11 - #0.12)
# ============================================================================

def task_analyze_master_weeks(llm_client) -> dict:
    """
    CALL #0.11: Analyze gold standard Week 1 and Week 11.

    Model: GPT-4o
    Temperature: 0.2
    Cost: ~$0.04

    Args:
        llm_client: OpenAI client

    Returns:
        Master analysis with style patterns
    """
    # Read master week files
    master_path_1 = Path("/Users/elle_jansick/Desktop/Latin A/A Tier/Week 1")
    master_path_11 = Path("/Users/elle_jansick/Desktop/Latin A/A Tier/Week 11")

    # Read sample files from each week
    week1_samples = {}
    week11_samples = {}

    if master_path_1.exists():
        # Read Day 1 files from Week 1
        day1_path = master_path_1 / "1.1"
        if day1_path.exists():
            for file in ["01_class_name.txt", "02_summary.md", "06_document_for_sparky_vocabulary_key_document.txt"]:
                file_path = day1_path / file
                if file_path.exists():
                    week1_samples[file] = file_path.read_text(encoding='utf-8')

    if master_path_11.exists():
        # Read Day 1 files from Week 11
        day1_path = master_path_11 / "11.1"
        if day1_path.exists():
            for file in ["01_class_name.txt", "02_summary.md", "05_guidelines_for_sparky.json", "06_document_for_sparky_vocabulary_key_document.txt"]:
                file_path = day1_path / file
                if file_path.exists():
                    week11_samples[file] = file_path.read_text(encoding='utf-8')

    sys = """You are Steel, analyzing GOLD STANDARD curriculum examples.

Extract patterns from these perfect examples for STYLE, FORMAT, TONE, STRUCTURE.

Return JSON with:
{
  "class_name_pattern": "format explanation",
  "summary_style_guide": {
    "tone": "description",
    "structure": "pattern",
    "opening_pattern": "how summaries start",
    "closing_pattern": "how summaries end"
  },
  "vocabulary_format": {
    "simple_style": "format for early weeks",
    "advanced_style": "format with derivatives",
    "typography_rules": "macron usage, italics"
  },
  "sparky_voice_characteristics": ["trait 1", "trait 2"],
  "quality_markers": ["marker 1", "marker 2"]
}"""

    usr = f"""MASTER WEEK 1 SAMPLES:
{json.dumps(week1_samples, indent=2)}

MASTER WEEK 11 SAMPLES:
{json.dumps(week11_samples, indent=2)}

Analyze and extract the patterns."""

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gpt-4o',
        'temperature': 0.2
    }

    return result


def task_align_research_to_masters(
    research_plan: dict,
    master_analysis: dict,
    week_number: int,
    llm_client
) -> dict:
    """
    CALL #0.12: Align research findings to gold standard style.

    Model: o1-mini (REASONING)
    Temperature: N/A
    Cost: ~$0.08

    Args:
        research_plan: All research from #0.1-#0.10
        master_analysis: Style guide from #0.11
        week_number: Current week
        llm_client: OpenAI client

    Returns:
        Alignment guide for generation
    """
    usr = f"""ALIGNMENT TASK: Combine research content with gold standard style.

WEEK NUMBER: {week_number}

RESEARCH FINDINGS (what to teach):
{json.dumps(research_plan, indent=2, default=str)}

MASTER STYLE GUIDE (how to present):
{json.dumps(master_analysis, indent=2)}

TASK: Create aligned generation instructions combining:
1. Content from research (vocabulary, pedagogy)
2. Style from masters (format, tone, voice)

Return JSON with:
{{
  "aligned_class_names": {{
    "day_1": "Latin A – Week {week_number} Day 1 : [Theme] — [Faith]",
    "day_2": "...",
    "day_3": "...",
    "day_4": "..."
  }},
  "aligned_summaries": {{
    "day_1": "Sparky begins Week {week_number}...",
    "day_2": "...",
    "day_3": "...",
    "day_4": "..."
  }},
  "aligned_vocabulary_format": ["word – translation", "..."],
  "sparky_voice_samples": {{
    "greeting": "Salve! Welcome to...",
    "transition": "Excellent! Now we...",
    "encouragement": "Good work! [Virtue] means..."
  }}
}}"""

    try:
        response = llm_client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": usr}
            ]
        )
        result = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠ o1-mini not available, falling back to GPT-4o: {e}")
        response = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Steel, aligning research with style guides."},
                {"role": "user", "content": usr}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

    result['_metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'model': 'o1-mini (or gpt-4o fallback)'
    }

    return result


# ============================================================================
# PHASE 0 ORCHESTRATOR
# ============================================================================

def execute_phase0_research(week_number: int, llm_client) -> dict:
    """
    Execute complete PHASE 0 research cascade.

    Args:
        week_number: Week to research
        llm_client: OpenAI client

    Returns:
        Complete research plan with all 12 outputs
    """
    print(f"\n  === PHASE 0: Research & Planning ===")

    # CALL #0.1
    print(f"    ⏺ Reading curriculum outline (Week {week_number})...")
    week_entry = task_locate_week_entry(week_number)

    # CALL #0.2
    print(f"    ⏺ Analyzing prior knowledge (Weeks 1-{week_number-1})...")
    backward = task_backward_analysis(week_number, llm_client)

    # CALL #0.3
    print(f"    ⏺ Previewing future dependencies (Weeks {week_number+1}-{week_number+5})...")
    forward = task_forward_analysis(week_number, llm_client)

    # CALL #0.4
    print(f"    ⏺ Researching classical pedagogy (o1-mini)...")
    pedagogy = task_pedagogical_benchmarking(week_entry, llm_client)

    # CALL #0.5
    print(f"    ⏺ Determining vocabulary (o1-mini)...")
    vocab = task_vocabulary_determination(week_entry, backward, forward, pedagogy, llm_client)

    # CALL #0.6
    print(f"    ⏺ Calculating session duration...")
    duration = task_session_duration_calculation(week_number)

    # CALL #0.7
    print(f"    ⏺ Planning virtue/faith integration...")
    virtue = task_virtue_faith_integration(week_entry, llm_client)

    # CALL #0.8
    print(f"    ⏺ Designing assessment strategy...")
    assessment = task_assessment_design(week_entry, vocab, llm_client)

    # CALL #0.9
    print(f"    ⏺ Planning differentiation...")
    differentiation = task_differentiation_planning(week_entry, vocab, llm_client)

    # CALL #0.10
    print(f"    ⏺ Planning materials...")
    materials = task_materials_planning(vocab, assessment)

    print(f"\n  === PHASE 0.5: Curriculum Alignment ===")

    # CALL #0.11
    print(f"    ⏺ Analyzing gold standard weeks...")
    master_analysis = task_analyze_master_weeks(llm_client)

    # Compile research plan
    research_plan = {
        "00_week_entry": week_entry,
        "01_backward_analysis": backward,
        "02_forward_analysis": forward,
        "03_pedagogical_research": pedagogy,
        "04_vocabulary_plan": vocab,
        "05_session_duration": duration,
        "06_virtue_faith_strategy": virtue,
        "07_assessment_plan": assessment,
        "08_differentiation_plan": differentiation,
        "09_materials_list": materials,
        "10_master_analysis": master_analysis
    }

    # CALL #0.12
    print(f"    ⏺ Aligning research to style (o1-mini)...")
    alignment = task_align_research_to_masters(research_plan, master_analysis, week_number, llm_client)
    research_plan["11_alignment_guide"] = alignment

    print(f"    ✓ PHASE 0 complete ({12} API calls)")

    return research_plan
