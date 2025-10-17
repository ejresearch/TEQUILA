# TEQUILA Frontend

Full-featured management UI for the TEQUILA Latin A Curriculum Generator.

## Features

### Dashboard
- 35-week curriculum overview
- Visual progress tracking
- Status badges (Complete, Partial, Not Generated)
- Quick stats and navigation

### Week Management
- **Weeks List**: Filterable table of all 35 weeks
- **Week Editor**: Tabbed interface with:
  - Overview (objectives, vocabulary, days)
  - Week Spec viewer
  - Days management
  - Internal documents browser
- **Generation**: In-browser week generation with progress tracking

### Day Editor
- Full WYSIWYG editing for all 7 day fields
- 6 teacher support documents:
  - Vocabulary Key
  - Chant Chart
  - Spiral Review
  - Teacher Voice Tips
  - Virtue & Faith
  - Weekly Topics
- Real-time save indicators
- Unsaved changes warnings

### Analytics Dashboard
- Total requests, tokens, and costs
- Provider breakdown (OpenAI/Anthropic)
- Per-week cost analysis
- Cost projections for remaining weeks
- Efficiency metrics

### Export Manager
- Download weeks as ZIP archives
- Bulk export options
- Export status tracking
- File size information
- SHA-256 hash verification

### Validation Viewer
- Comprehensive validation results
- Error/warning/info categorization
- Visual status indicators
- Validation rules reference
- Re-validation on demand

## Tech Stack

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS v4** for styling
- **shadcn/ui** components
- **Turbopack** for fast builds

## Getting Started

### Prerequisites

1. **Backend API**: Ensure the TEQUILA backend is running:
   ```bash
   cd /Users/elle_jansick/steel
   uvicorn src.app:app --reload
   ```
   Backend will be available at http://localhost:8000

2. **Node.js**: v18+ required

### Installation

```bash
# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local to set NEXT_PUBLIC_API_URL (default: http://localhost:8000)
```

### Development

```bash
# Start dev server
npm run dev
```

Open http://localhost:3000

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── page.tsx              # Dashboard (/)
│   │   ├── weeks/
│   │   │   ├── page.tsx          # Weeks list (/weeks)
│   │   │   └── [id]/
│   │   │       ├── page.tsx      # Week editor (/weeks/1)
│   │   │       ├── validate/     # Validation viewer
│   │   │       └── days/[day]/   # Day editor (/weeks/1/days/1)
│   │   ├── analytics/            # Analytics dashboard
│   │   └── exports/              # Export manager
│   ├── components/
│   │   ├── layout/
│   │   │   └── nav.tsx           # Navigation bar
│   │   └── ui/                   # shadcn components
│   └── lib/
│       ├── api/
│       │   ├── client.ts         # API client
│       │   └── types.ts          # TypeScript types
│       └── utils.ts
├── .env.local                    # Environment config
└── package.json
```

## API Integration

The frontend connects to the TEQUILA backend API:

**Base URL**: `http://localhost:8000` (configurable in `.env.local`)

**Endpoints Used**:
- `GET /api/v1/weeks` - List all weeks
- `GET /api/v1/weeks/{id}/spec/compiled` - Get week spec
- `POST /api/v1/weeks/{id}/validate` - Validate week
- `POST /api/v1/weeks/{id}/export` - Export to ZIP
- `GET /api/v1/usage` - Get usage stats
- `WS /ws` - WebSocket for real-time updates

See `src/lib/api/client.ts` for full API documentation.

## Features in Detail

### Mock Data Mode

Currently, all pages use mock data for demonstration. To connect to the real API:

1. Update each page's `useEffect` to call API client methods
2. Replace mock data with actual API responses
3. Handle loading/error states

Example:
```typescript
// Replace this:
const mockWeeks = [/* ... */];
setWeeks(mockWeeks);

// With this:
import { apiClient } from "@/lib/api/client";
const data = await apiClient.getWeeks();
setWeeks(data.weeks);
```

### Real-time Generation

The WebSocket connection (`/ws`) provides real-time updates during week generation:

```typescript
const ws = apiClient.connectWebSocket((message) => {
  if (message.type === "progress") {
    setProgress(message.data.progress_percent);
  }
});
```

### Authentication

API key authentication is optional. Set in `.env.local`:

```
NEXT_PUBLIC_API_KEY=your_api_key_here
```

## Development

### Adding New Pages

1. Create page file in `src/app/[route]/page.tsx`
2. Add route to navigation in `src/components/layout/nav.tsx`
3. Add API methods to `src/lib/api/client.ts` if needed
4. Add types to `src/lib/api/types.ts`

### Adding UI Components

```bash
# Add shadcn component
npx shadcn@latest add [component-name]
```

Available components: button, card, table, badge, progress, dialog, tabs, alert, select, input, textarea

### Styling

Tailwind CSS classes are available throughout. Global styles in `src/app/globals.css`.

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## Contributing

This is part of the TEQUILA project by Elle Jansick and YT Research LLC.

For questions: ellejansickresearch@gmail.com

## License

MIT License - See LICENSE file in root directory

Copyright © 2025 Elle Jansick and YT Research LLC
