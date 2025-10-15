# STEEL Frontend

React/TypeScript frontend for the STEEL Latin A Curriculum Generator.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env to set your API URL and key
```

3. Start development server:
```bash
npm start
```

The app will open at http://localhost:3000 and proxy API requests to http://localhost:8000.

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API client and request handlers
│   │   └── client.ts # Main API client with all endpoints
│   ├── hooks/        # React hooks for data management
│   │   ├── useWeeks.ts      # Weeks data and operations
│   │   ├── useGeneration.ts # Curriculum generation
│   │   ├── useUsage.ts      # Usage tracking
│   │   └── useDayFields.ts  # Day fields management
│   ├── components/   # React components
│   │   └── SteelDashboard.tsx # Main dashboard UI
│   └── types/        # TypeScript type definitions
│       └── index.ts  # API types and interfaces
```

## Features

### Backend Integration

The frontend is fully wired to the STEEL backend API:

- **Curriculum Generation**: Start generation for single or multiple weeks
- **Real-time Stats**: Live usage tracking during generation
- **Validation**: Automatic validation of generated weeks
- **Export**: Download validated weeks as ZIP files
- **Field Viewer**: Browse and view all 7 fields for each day

### API Endpoints Used

- `GET /api/v1/usage` - Usage statistics
- `GET /api/v1/weeks/{week}/spec/compiled` - Get week specification
- `GET /api/v1/weeks/{week}/days/{day}/fields/{field}` - Get day field
- `POST /api/v1/gen/weeks/{week}/hydrate` - Generate complete week
- `POST /api/v1/weeks/{week}/validate` - Validate week
- `POST /api/v1/weeks/{week}/export` - Export week to ZIP
- `GET /api/v1/weeks/{week}/export/download` - Download exported ZIP

### Authentication

If `API_AUTH_KEY` is set in the backend `.env`, you must provide the same key in the frontend `.env` as `REACT_APP_API_KEY`.

## Development

### Running with Backend

1. Start the backend:
```bash
cd ..
python -m src.app
```

2. In another terminal, start the frontend:
```bash
cd frontend
npm start
```

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)
- `REACT_APP_API_KEY`: API authentication key (optional)

## Architecture

The frontend follows a clean architecture pattern:

1. **API Layer** (`api/client.ts`): Handles all HTTP communication
2. **Hooks Layer** (`hooks/`): Manages state and data fetching
3. **Components Layer** (`components/`): UI components that consume hooks
4. **Types Layer** (`types/`): TypeScript definitions for type safety

This separation ensures:
- Easy testing and mocking
- Reusable business logic
- Type-safe API communication
- Clean component code focused on UI

## Production Build

```bash
npm run build
```

Builds the app for production to the `build` folder. The build is minified and optimized for best performance.
