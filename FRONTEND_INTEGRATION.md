# Frontend-Backend Integration Guide

This document describes how the STEEL React frontend is wired to the FastAPI backend.

## Architecture Overview

```
┌─────────────────────┐         ┌─────────────────────┐
│                     │         │                     │
│  React Frontend     │◄───────►│  FastAPI Backend    │
│  (Port 3000)        │  HTTP   │  (Port 8000)        │
│                     │  + WS   │                     │
└─────────────────────┘         └─────────────────────┘
         │                               │
         │                               │
    Components                      Services
    - Dashboard                     - generator_week
    - Generator                     - generator_day
    - WeekDetails                   - validator
         │                          - exporter
         ▼                               │
       Hooks                             ▼
    - useWeeks                     Storage Layer
    - useGeneration                - curriculum/
    - useUsage                     - exports/
    - useDayFields                 - logs/
         │
         ▼
     API Client
    - client.ts
```

## Directory Structure

```
steel/
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── api/                  # API communication layer
│   │   │   └── client.ts         # HTTP client + all endpoints
│   │   ├── hooks/                # React hooks for state management
│   │   │   ├── useWeeks.ts       # Weeks CRUD operations
│   │   │   ├── useGeneration.ts  # Generation workflow
│   │   │   ├── useUsage.ts       # Usage tracking
│   │   │   └── useDayFields.ts   # Day fields viewer
│   │   ├── components/           # UI components
│   │   │   └── SteelDashboard.tsx # Main dashboard
│   │   └── types/                # TypeScript types
│   │       └── index.ts          # API response types
│   ├── .env.example              # Environment template
│   ├── package.json              # Dependencies
│   └── README.md                 # Frontend docs
├── src/                          # Python backend
│   ├── app.py                    # FastAPI app + CORS + WebSocket
│   ├── services/
│   │   ├── generator_week.py     # Week generation logic
│   │   ├── generator_day.py      # Day generation logic
│   │   ├── validator.py          # Validation logic
│   │   ├── exporter.py           # ZIP export logic
│   │   ├── usage_tracker.py      # Cost tracking
│   │   └── websocket.py          # WebSocket manager (NEW)
│   └── config.py                 # Settings + LLM client
└── curriculum/                   # Generated content storage
    └── LatinA/
        ├── Week01/
        ├── Week02/
        └── ...
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Purpose | Frontend Hook |
|--------|----------|---------|---------------|
| `GET` | `/api/v1/usage` | Get usage stats | `useUsage` |
| `POST` | `/api/v1/usage/reset` | Reset usage stats | `useUsage` |
| `GET` | `/api/v1/weeks/{week}/spec/compiled` | Get week spec | `useWeeks` |
| `GET` | `/api/v1/weeks/{week}/days/{day}/fields/{field}` | Get day field | `useDayFields` |
| `POST` | `/api/v1/weeks/{week}/validate` | Validate week | `useWeeks` |
| `POST` | `/api/v1/weeks/{week}/export` | Export week | `useWeeks` |
| `GET` | `/api/v1/weeks/{week}/export/download` | Download ZIP | `api.downloadWeek()` |

### Generation Endpoints (Require API Key)

| Method | Endpoint | Purpose | Frontend Hook |
|--------|----------|---------|---------------|
| `POST` | `/api/v1/gen/weeks/{week}/hydrate` | Generate complete week | `useGeneration` |
| `POST` | `/api/v1/gen/weeks/{week}/spec` | Generate week spec only | - |
| `POST` | `/api/v1/gen/weeks/{week}/days/{day}/fields` | Generate day fields | - |

### WebSocket

| Endpoint | Purpose | Frontend Hook |
|----------|---------|---------------|
| `WS /ws` | Real-time generation progress | *(Future)* `useWebSocket` |

## Data Flow Examples

### 1. Loading Weeks on Dashboard

```typescript
// frontend/src/hooks/useWeeks.ts
const { weeks, loading, error } = useWeeks()

// Behind the scenes:
// 1. Hook initializes and calls loadWeeks()
// 2. For each week 1-35:
//    - Try GET /api/v1/weeks/{week}/spec/compiled
//    - If exists, set status='completed'
//    - Try POST /api/v1/weeks/{week}/validate
//    - If valid, set validated=true
// 3. Returns array of Week objects
```

### 2. Generating a Week

```typescript
// frontend/src/hooks/useGeneration.ts
const { generateWeek, progress, generating } = useGeneration()

await generateWeek(13)

// Behind the scenes:
// 1. POST /api/v1/gen/weeks/13/hydrate
// 2. Backend (src/app.py:hydrate_week_endpoint):
//    a. Generate week spec
//    b. Generate role context
//    c. Generate assets
//    d. Generate Days 1-4 (fields + documents)
//    e. Validate week
// 3. Returns WeekHydrationResult
// 4. Frontend updates progress state
// 5. Auto-refreshes usage stats during generation
```

### 3. Viewing Day Fields

```typescript
// frontend/src/hooks/useDayFields.ts
const { day, loading } = useDayFields(weekNumber, dayNumber)

// Behind the scenes:
// 1. For each of 7 fields:
//    - GET /api/v1/weeks/{week}/days/{day}/fields/{field}
// 2. Compiles into Day object with:
//    - fields: Record<string, any>
//    - validated: boolean
//    - fieldsComplete: number
```

### 4. Exporting a Week

```typescript
// frontend/src/components/SteelDashboard.tsx
await exportWeekAPI(weekNumber)
api.downloadWeek(weekNumber)

// Behind the scenes:
// 1. POST /api/v1/weeks/{week}/export
//    - Validates week first
//    - Creates ZIP file
//    - Returns path and size
// 2. GET /api/v1/weeks/{week}/export/download
//    - Opens download in new tab
//    - Returns FileResponse (ZIP)
```

## Authentication

The backend supports optional API key authentication:

**Backend (.env):**
```bash
API_AUTH_KEY=your-secret-key-here
```

**Frontend (.env):**
```bash
REACT_APP_API_KEY=your-secret-key-here
```

If `API_AUTH_KEY` is set in backend, all generation endpoints (`/api/v1/gen/*`) require the `X-API-Key` header.

The frontend `api/client.ts` automatically includes this header if `REACT_APP_API_KEY` is set.

## CORS Configuration

The backend (src/app.py:50-56) is configured to accept requests from:
- `http://localhost:3000` (React dev server)
- `http://127.0.0.1:3000`

To add additional origins, update the `allow_origins` list in `app.py`.

## WebSocket Support

The backend includes a WebSocket endpoint at `WS /ws` for real-time progress updates:

**Backend (src/services/websocket.py):**
- `ConnectionManager` class handles connections
- Broadcasts progress updates during generation
- Sends validation results and errors

**Frontend (Future Enhancement):**
```typescript
// Create useWebSocket hook to:
// 1. Connect to ws://localhost:8000/ws
// 2. Listen for progress events
// 3. Update UI in real-time during generation
// 4. Show live field-by-field progress
```

## Type Safety

The frontend uses TypeScript with strict type checking:

**Backend Response:**
```python
# src/app.py
return {
    "week": week,
    "components": {
        "spec": str(spec_path),
        "days": [...]
    },
    "validation": {...}
}
```

**Frontend Type:**
```typescript
// frontend/src/types/index.ts
interface WeekHydrationResult {
  week: number
  components: {
    spec: string
    days: Array<{...}>
  }
  validation: {...}
}
```

This ensures compile-time safety and prevents runtime type errors.

## Error Handling

**Backend:**
- Returns HTTP 400/500 with `detail` field
- Logs errors to `logs/` directory
- Saves invalid LLM responses for debugging

**Frontend:**
- API client throws `APIError` with status and detail
- Hooks catch errors and set `error` state
- UI displays error messages to user

## Development Workflow

### 1. Start Backend
```bash
cd /Users/elle_jansick/steel
python -m src.app
# Runs on http://localhost:8000
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm start
# Runs on http://localhost:3000
# Proxies API requests to :8000
```

### 3. Test Integration
1. Open http://localhost:3000
2. Click "Generate Curriculum"
3. Select week range (e.g., 1 to 1)
4. Click "Start Generation"
5. Watch real-time progress
6. View generated week in dashboard
7. Export to ZIP

## Production Deployment

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=...
export API_AUTH_KEY=...

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.app:app
```

### Frontend
```bash
# Build production bundle
cd frontend
npm run build

# Serve static files (e.g., with nginx)
# Or deploy to Vercel/Netlify
```

Update `REACT_APP_API_URL` in frontend `.env` to point to production backend URL.

## Testing

### Backend Tests
```bash
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
Use tools like Postman or curl to test API endpoints:

```bash
# Test generation (requires API key)
curl -X POST http://localhost:8000/api/v1/gen/weeks/1/hydrate \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json"

# Test export
curl -X POST http://localhost:8000/api/v1/weeks/1/export

# Download ZIP
curl -O http://localhost:8000/api/v1/weeks/1/export/download
```

## Troubleshooting

### CORS Errors
- Ensure backend CORS middleware includes frontend origin
- Check browser console for preflight (OPTIONS) request failures

### API Key Errors (401/403)
- Verify `REACT_APP_API_KEY` matches backend `API_AUTH_KEY`
- Check that key is included in request headers (Network tab)

### Generation Timeouts
- Backend has 2-minute default timeout per Bash command
- Increase timeout in `src/services/generator_day.py` if needed

### WebSocket Connection Failed
- Ensure WebSocket endpoint is enabled in `src/app.py`
- Check that frontend is connecting to correct URL
- Verify no proxy/firewall blocking WebSocket protocol

## Next Steps

1. **Implement WebSocket Hook**: Create `useWebSocket` hook for real-time progress
2. **Add Polling Fallback**: Poll `/api/v1/gen/weeks/{week}/status` if WebSocket unavailable
3. **Enhance Error UI**: Show detailed error logs and retry buttons
4. **Add Week List Endpoint**: Create `GET /api/v1/weeks` to efficiently list all weeks
5. **Implement Caching**: Cache week specs in frontend to reduce API calls

## Contributing

When adding new API endpoints:

1. Add endpoint to `src/app.py`
2. Add TypeScript types to `frontend/src/types/index.ts`
3. Add API method to `frontend/src/api/client.ts`
4. Create/update hook in `frontend/src/hooks/`
5. Update this documentation

## License

MIT License - See LICENSE file for details.
