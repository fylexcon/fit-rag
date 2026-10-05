# Fitness AI Agent

## Monorepo Layout
- `/backend`: Python FastAPI project
- `/frontend`: Next.js React project
- `/infra`: Docker compose and environment configurations

## How to run

1. **Start the Infrastructure:**
   ```bash
   cd infra
   docker compose up -d
   ```
   *Make sure you copy `.env.example` to `.env` if you need custom credentials.*

2. **Start the Backend:**
   ```bash
   cd backend
   uv venv
   uv pip install -e ".[dev]"
   uvicorn main:app --reload
   ```

3. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
