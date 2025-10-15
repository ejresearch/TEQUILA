# STEEL Quick Start Guide

Get the STEEL Latin A Curriculum Generator up and running in 5 minutes.

## Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- OpenAI API key

## Backend Setup (2 minutes)

1. **Clone and navigate:**
```bash
cd /Users/elle_jansick/steel
```

2. **Install Python dependencies:**
```bash
make install
# or: pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and set:
# OPENAI_API_KEY=your-key-here
```

4. **Start the backend:**
```bash
python -m src.app
# Backend runs on http://localhost:8000
```

## Frontend Setup (3 minutes)

1. **Run setup script:**
```bash
./setup_frontend.sh
```

2. **Configure environment (if needed):**
```bash
# Edit frontend/.env
# REACT_APP_API_URL=http://localhost:8000
# REACT_APP_API_KEY=  (leave empty for dev mode)
```

3. **Start the frontend:**
```bash
cd frontend
npm start
# Frontend opens at http://localhost:3000
```

## Usage

### Via Web UI (Recommended)

1. Open http://localhost:3000
2. Click **"Generate Curriculum"**
3. Select week range (e.g., 1 to 1)
4. Choose AI model (GPT-4o recommended)
5. Click **"Start Generation"**
6. Watch real-time progress
7. Export validated weeks as ZIP files

### Via CLI

Generate a single week:
```bash
make gen-week WEEK=1
```

Generate a range:
```bash
python -m src.cli.generate_all_weeks --from 1 --to 5
```

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  React Dashboard    │◄───────►│  FastAPI Backend    │
│  localhost:3000     │  HTTP   │  localhost:8000     │
└─────────────────────┘         └─────────────────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  OpenAI GPT-4o  │
                                 └─────────────────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  curriculum/    │
                                 │  ├─ Week01/     │
                                 │  ├─ Week02/     │
                                 │  └─ ...         │
                                 └─────────────────┘
```

## Key Features

### 7-Field Day Architecture
Each lesson day contains 7 prescribed fields:
1. `01_class_name.txt` - Lesson identifier
2. `02_summary.md` - Lesson summary
3. `03_grade_level.txt` - Target grade level
4. `04_role_context.json` - Sparky's role configuration
5. `05_guidelines_for_sparky.md` - Teaching guidelines
6. `06_document_for_sparky.json` - Complete lesson plan
7. `07_sparkys_greeting.txt` - Opening greeting

### Pedagogical Enforcement
- ✅ Day 4 spiral review (≥25% prior content)
- ✅ Single tutor voice (Sparky)
- ✅ Virtue integration (7 cardinal virtues)
- ✅ Gradual complexity progression

### Validation & Quality
- 10-retry generation with validation
- Schema validation (Pydantic)
- Comprehensive logging
- SHA256-verified exports

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/gen/weeks/{week}/hydrate` | POST | Generate complete week |
| `/api/v1/weeks/{week}/validate` | POST | Validate week structure |
| `/api/v1/weeks/{week}/export` | POST | Export week to ZIP |
| `/api/v1/usage` | GET | Usage stats & cost |
| `/ws` | WebSocket | Real-time progress |

Full API docs: http://localhost:8000/docs

## Project Structure

```
steel/
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── api/client.ts         # API client
│   │   ├── hooks/                # React hooks
│   │   └── components/           # UI components
│   └── package.json
├── src/                          # Python backend
│   ├── app.py                    # FastAPI app
│   ├── services/                 # Business logic
│   │   ├── generator_week.py
│   │   ├── generator_day.py
│   │   └── websocket.py
│   └── config.py
├── curriculum/                   # Generated content
│   └── LatinA/
│       └── Week01..35/
├── tests/                        # Test suite
└── Makefile                      # Common commands
```

## Common Commands

```bash
# Backend
make install        # Install dependencies
make gen-week WEEK=1  # Generate week 1
make test          # Run tests
make lint          # Run linter

# Frontend
cd frontend
npm start          # Dev server
npm run build      # Production build
npm test           # Run tests

# Validation
python -m src.cli.validate_week --week 1

# Export
python -m src.cli.export_week --week 1
```

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 16+

# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS errors
- Ensure backend is running on port 8000
- Check frontend `.env` has correct API URL
- Verify CORS middleware in `src/app.py`

### Generation timeouts
- Increase timeout in `src/config.py`
- Check OpenAI API key is valid
- Monitor `logs/` directory for errors

## Documentation

- **Frontend Integration:** [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Compliance:** [COMPLIANCE_AUDIT.md](./COMPLIANCE_AUDIT.md)
- **Frontend README:** [frontend/README.md](./frontend/README.md)

## Cost Estimates

- **Per Week:** ~$12-15 in OpenAI API usage
- **Full 35 Weeks:** ~$420-525
- **Per Field:** ~$0.50-0.70

Monitor costs in real-time at http://localhost:3000 (Usage Stats card)

## Next Steps

1. ✅ Generate Week 1
2. ✅ Validate output
3. ✅ Export to ZIP
4. ✅ Generate Weeks 1-35
5. 📦 Deploy to production

## Support

- **Issues:** https://github.com/ejresearch/TEQUILA/issues
- **Docs:** http://localhost:8000/docs
- **Logs:** `logs/` directory

## License

MIT License - See [LICENSE](./LICENSE) for details.

---

**STEEL** - Latin A Curriculum Generator v1.0.0
🤖 Powered by OpenAI GPT-4o
📚 7-Field Architecture • 35 Weeks • 140 Lessons • 980 Fields
