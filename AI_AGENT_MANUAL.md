# AI Agent User Manual

## Overview
This codebase is a template for an AI Web Application using a **FastAPI** backend for agentic workflows and a **Next.js** frontend for the client application. It integrates **Supabase** for Authentication, Database (PostgreSQL), and Storage.

- **Root Directory**: `d:\raufun\fastapi-nextjs-supabase`
- **Backend (Agents)**: `agents/` (FastAPI, Python, Langchain, ChromaDB)
- **Frontend (Client)**: `client/` (Next.js, TypeScript)
- **Database**: Supabase PostgreSQL
- **ORM**: Drizzle (Client/Migrations), SQLAlchemy (Agents)

---

## 1. Backend (Agents)
Located in `agents/`. Designed for AI logic and heavy processing.

### Directory Structure
- `api/`: FastAPI route handlers (endpoints).
- `services/`: Business logic and AI agent implementations.
- `models/`: SQLAlchemy database models (mirror of Drizzle schema).
- `config/`: Configuration (Settings, Database connection, ChromaDB).
- `utils/`: Utilities (Logger, etc.).
- `middlewares/`: Custom middlewares (Auth, Rate Limiting).

### Key Patterns
- **Database Connection**: Uses `SQLAlchemy` (Async).
    - Connection logic: `config/database.py`.
    - Import `get_db` dependency for routes.
    - **Note**: The backend uses SQLAlchemy to *access* data, but Drizzle (Client) manages *migrations*.
    - Chromadb connection logic: `config/chromadb.py`.
    - Import `get_chroma_collection` dependency for routes.
- **Logging**: Use `utils.logger`.
    - `from utils.logger import logger`
    - `logger.info("message")` -> JSON in production, Colored in dev.
- **Configuration**: Uses `pydantic-settings`.
    - Defined in `config/settings.py`.
    - Reads from `.env`.
    - For any new modules, use this pattern: `config/settings.py`.

### How to Add a New Agent
1.  Create a service class in `services/`.
2.  Define request/response models in `schemas/` (create if missing) or inline.
3.  Create a route in `api/` that calls the service.
4.  Register the router in `main.py`.

### IMPORTANT: When updating the database schema, always use the drizzle setup in client, use the agents for usage only.

---

## 2. Frontend (Client)
Located in `client/`. Next.js App Router application.

### Directory Structure
- `src/app/`: App Router pages and layouts.
- `src/components/`: React components.
- `src/db/`: Drizzle ORM configuration and Schema.
- `src/lib/supabase/`: Supabase client and auth helpers.
- `src/lib/`: Shared utilities.

### Key Patterns
- **Supabase Integration**:
    - Client creation: `src/lib/supabase/client.ts` (Browser), `server.ts` (Server Component), admin.ts (Admin Server Client), `middleware.ts` (Edge).
- **Database & ORM**: Uses **Drizzle ORM**.
    - Schema: `src/db/schema.ts`.
    - Migrations: `src/db/migrations/`.
    - **Migration Command**: `npm run db:migrate` (Run this to apply schema changes).
- **Authentication**:
    - Handled by Supabase Auth (Frontend).
    - Middleware (`client/middleware.ts`) refreshes sessions.
    - Middleware redirection logic: `client/src/lib/supabase/middleware.ts`.
- **API Fetching**:
    - Call FastAPI endpoints using `fetch` or server actions.
    - Ensure `Authorization` header includes the Supabase Session Access Token.

---

## 3. Workflows

### Database Schema Updates
1.  **Edit Schema**: Modify `client/src/db/schema.ts` (Drizzle).
2.  **Migrate**: Run `npm run db:migrate` in `client/` directory.
3.  **Sync Backend**: Manually update/create corresponding SQLAlchemy models in `agents/models/` to match the new schema. **Crucial**: Keep them in sync.

### Environment Variables
- **Backend**: `agents/.env`. Needs `DB_URL` (Postgres connection string), `SUPABASE_URL`, etc.
- **Frontend**: `client/.env.local`. Needs `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, etc.

### Starting the Project
- **Backend**:
  ```bash
  cd agents
  uvicorn main:app --reload
  ```
- **Frontend**:
  ```bash
  cd client
  npm run dev
  ```
