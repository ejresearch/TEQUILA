Background & R&D — Latin A Split-File Curriculum System

1. Origins & Motivation
	•	We began with a desire to transform a monolithic “week JSON blob” into a highly modular system — where each field (title, summary, guidelines, greeting, full script) is its own file.
	•	The aim: teachers can drag & drop single fields (greeting, summary, daily script) into other systems (Flint, LMS) without editing massive JSONs.
	•	Also: to support automated AI generation, validation, and spiral enforcement, in a deterministic, schema-driven way.

2. Core Design Pillars
	1.	Atomic Field Files
	•	Six files per day map exactly to Flint’s “Build Manually” fields.
	•	This ensures the user-facing (or content-facing) interface is intuitive and granular.
	2.	Split Week Spec & Role Context
	•	Weekly metadata, chant, vocabulary, spiral links, assets, preview are broken into parts (metadata, objectives, vocabulary, chant, etc.).
	•	Sparky’s persona — identity, feedback style, knowledge recycling, etc. — is stored separately under Role_Context, yet tied together via compile logic.
	3.	Day-Level Script JSON
	•	The “05_document_for_sparky.json” file for each day holds the full timed lesson flow: “00:00–00:01 greeting”, “00:01–00:03 review”, checks, prompts, closure.
	•	It references prior knowledge, spiral links, misconception watchlist.
	4.	Spiral & Memory Enforcement
	•	Week-level: spiral_links instruct reuse of prior vocabulary, grammar, faith phrases.
	•	Day-level: Each day links to recycled vocab/grammar.
	•	Assessment rule: Day 4’s quiz must include at least 25 % items from prior weeks.
	•	Validators ensure no orphan references (e.g. if a day references vocabulary not in week spec or previous spiral).
	5.	Template & Scaffold System
	•	templates/week_kit/fields/ for the six daily fields (txt, md, json).
	•	templates/week_kit/spec_parts/ for week spec parts.
	•	Scaffolding CLI builds empty split structure from these templates.
	6.	Compile / Bundle Logic
	•	Helper functions read atomic files and join them into compiled JSON (e.g. flint-bundle for a day, compiled_week_spec for a week).
	•	The join ensures consumer systems still get a unified representation when needed.
	7.	Validator Layer
	•	Checks atomic files for nonemptiness and expected formatting.
	•	Checks compiled JSON against Pydantic schemas.
	•	Enforces spiral logic and assessment rules (e.g. Day 4 prior-item ratio).
	•	Produces structured errors (file paths + error message) for easy debugging.
	8.	Backward Compatibility & Transition Path
	•	Keep monolithic export/ZIP support for use with existing systems (perhaps via compiled JSON).
	•	Support both split and legacy formats in parallel while migrating.

3. Tradeoffs & Decisions
	•	Granularity vs cognitive overhead: splitting into many files makes editing modular, but raises surface area (e.g. missing file errors).
	•	Directory complexity: adding subfolders (Week_Spec, Role_Context, activities/DayN) is more nested but logical.
	•	Compile cost: reading many small files vs one JSON — minimal overhead relative to readability gains.
	•	Validation boundary decisions: e.g. how strictly enforce “≥ 25% prior items” (based on textual pattern vs structured reference).
	•	Template uniformity: all split parts must have corresponding .tmpl scaffolds to ensure consistency over 36 weeks.
	•	Naming & ordering: prefixing field files (01_… to 06_…) ensures stable sort order, matches Flint’s UI.

4. Evolution from TEQUILA / Prior Systems
	•	TEQUILA provided a starting scaffold (week/day generation, CLI + API).
	•	Our work layered on top: split-file architecture, more rigid spiral enforcement, atomic file editing, improved modularity.
	•	We maintain compatibility with TEQUILA’s existing modules (e.g. generator_week, generator_day, storage, validator) by refactoring them rather than rewriting entirely.

5. Example: How the Week-11 Spec You Pasted is Realized
	•	The large JSON you showed becomes distributed:
	•	Sparky’s role identity, tone, mission, pedagogical mission → files in Role_Context/
	•	Weekly metadata, title, grade, virtue, faith phrase → Week_Spec/01_metadata.json
	•	Objectives, vocab, chant, assessment, preview → split in 02_objectives.json, 03_vocabulary.json, 04_grammar_focus.md, 05_chant.json, 07_assessment.json, etc.
	•	Day scripts (the four session flows) go into activities/Day1–4/05_document_for_sparky.json, each referencing the part weekly spec values.
	•	The sixfield files per day are then simple field-level text + JSON that map exactly to the Flint UI fields.

6. Usage Workflow (Author / Runtime)
	1.	Scaffold a week via CLI → folder + empty split files appear
	2.	Hydrate via AI (or manual) → fill each split file or day script
	3.	Validate → atomic + compiled checks, spiral logic
	4.	Export / ZIP → joins split files, includes assets and compiled forms
	5.	Drag-drop / copy individual fields or compiled bundles into Flint or LMS

7. Why This Level Works (Fidelity & Flexibility)
	•	You retain the full minute-by-minute lesson detail (greeting, chants, translation, reflection) in each 05_document_for_sparky.json.
	•	You preserve Sparky’s persona and teaching strategy via Role_Context and repeated reuse across days.
	•	You enforce spiral memory and reuse, so new material always anchors in previous weeks.
	•	Editors can tweak just one field (say, the day greeting) without touching entire week JSONs.
	•	Content is version-friendly, diffable, and modular.

