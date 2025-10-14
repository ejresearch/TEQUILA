TEQUILA: AI-Powered Latin A Curriculum Generator (v1.0 Pilot)

Not the quantum TEQUILA project.
This is an AI curriculum system for Latin A, not related to quantum computing.

⸻

Overview

TEQUILA (or Steel) is a provider-agnostic curriculum engine that auto-generates a full 35-week Latin A course (4 lessons per week, 7 fields per lesson). It enforces pedagogical rules (spiral review, ≥ 25% recall, virtue alignment, single tutor voice) and produces exportable teaching materials with provenance metadata.

This is the v1.0 pilot: focused on Latin A only, using OpenAI GPT-4o as the backend. Human editing tools, dashboards, or multi-subject support are deferred to future versions.

⸻

Architecture & Flow

flowchart TD
  OutlineData --> GeneratorWeek
  GeneratorWeek --> GeneratorDay
  GeneratorDay --> Validator
  Validator -- valid --> Exporter
  Validator -- invalid --> RetryLoop
  RetryLoop --> Validator
  Exporter --> ZIPArchive
  ZIPArchive --> exports/WeekXX.zip

	1.	OutlineData: seed content (Weeks 1–12) + metadata (virtue, vocab, grammar)
	2.	GeneratorWeek: orchestrates 4 lessons/day generation using prompt templates
	3.	GeneratorDay: generates each day’s 7-field files
	4.	Validator: Pydantic schema + pedagogical checks (≥ 25% prior content)
	5.	RetryLoop: up to 10 attempts if validation fails
	6.	Exporter: packages each week into a zip with manifest + metadata

⸻

Directory Layout

TEQUILA/
├── curriculum/
│   └── LatinA/
│       ├── Week01/
│       │   ├── activities/
│       │   │   ├── Day1/
│       │   │   ├── Day2/
│       │   │   ├── Day3/
│       │   │   └── Day4/
│       │   └── assets/
│       └── … up to Week35/
├── exports/
│   ├── Week01.zip
│   ├── Week02.zip
│   └── … Week35.zip
├── logs/
│   ├── generation.log
│   └── validation_failures/
├── src/
│   ├── cli/
│   │   └── generate_all_weeks.py
│   ├── services/
│   │   ├── generator_week.py
│   │   ├── generator_day.py
│   │   ├── validator.py
│   │   ├── exporter.py
│   │   └── llm_client.py  (OpenAI only)
│   └── models/
│       └── schemas_day_week.py
├── .github/
│   └── workflows/ci.yml
├── .env.example
├── README.md
├── ARCHITECTURE.md
└── LICENSE


⸻

Quickstart Guide
	1.	Clone the repository

git clone https://github.com/ejresearch/TEQUILA.git
cd TEQUILA


	2.	Environment setup
Copy .env.example to .env and fill in:

OPENAI_API_KEY=your_openai_key
MODEL_NAME=gpt-4o


	3.	Install dependencies

pip install -r requirements.txt


	4.	Generate curriculum
This will generate Weeks 1–35:

python -m src.cli.generate_all_weeks --from 1 --to 35


	5.	Inspect exports
Each week will be zipped in exports/WeekXX.zip. You can unzip and review the 7-field files per lesson.

⸻

Validation & Retry Behavior
	•	Each lesson must pass the Pydantic schemas in src/models/schemas_day_week.py.
	•	A built-in pedagogical check ensures at least 25% of quiz questions review content from prior weeks.
	•	On failure, the engine will retry up to 10 times. If still invalid, it pauses and awaits user confirmation to proceed.
	•	Successful regeneration appends a version suffix (_v2, _v3, etc.) rather than overwriting previous outputs.

⸻

Export Format & Metadata
	•	Each week’s ZIP archive includes:
	•	The folder structure for 4 days + assets
	•	A manifest.json listing file paths and SHA-256 hashes
	•	Provenance metadata (model used, timestamp, tokens, repository commit)
	•	Logs of failures, retries, and generation status are stored in logs/

⸻

CI / Testing
	•	A GitHub Actions workflow (.github/workflows/ci.yml) runs on each push:
	•	Linting (e.g. ruff / black)
	•	Schema validation tests with a sample week (Week11)
	•	A small pytest suite ensures no regressions in schema definitions or directory structure.

⸻

Future & Roadmap (non-v1.0)
	•	Add human editing overlays with diff / accept-reject UI
	•	Expand to multi-subject curricula (e.g. Greek A, Bible A)
	•	Add dashboards & usage analytics
	•	Reintroduce multi-provider LLM support (Anthropic, Groq, etc.)
	•	Incorporate educational feedback loops (teacher edits → model fine-tuning)

⸻

License & Attribution

This project is licensed under the MIT License.
© 2025 ejresearch
