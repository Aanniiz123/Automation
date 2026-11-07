# AGENT Project Guide

This repository has a backend-focused FastAPI application. The active code is under [backend/](./backend/), and the frontend folder currently appears to be empty or not yet implemented.

## Project overview

- Backend framework: FastAPI
- ORM: SQLAlchemy (async)
- Validation: Pydantic
- Auth: JWT + bcrypt
- Database: MySQL via SQLAlchemy async engine
- Email: SMTP support via aiosmtplib
- Server runner: uvicorn

## Main folders

- [backend/](./backend/) — main backend project
- [backend/main.py](./backend/main.py) — app entry point
- [backend/app/](./backend/app/) — application modules
- [backend/app/app.py](./backend/app/app.py) — FastAPI app instance and health endpoints
- [backend/database.py](./backend/database.py) — database engine/session configuration
- [backend/core/](./backend/core/) — shared config and project settings
- [backend/core/config.py](./backend/core/config.py) — environment-based app settings
- [backend/app/auth/](./backend/app/auth/) — authentication features
- [backend/app/auth/models/](./backend/app/auth/models/) — SQLAlchemy models and Pydantic schemas
- [backend/requirements.txt](./backend/requirements.txt) — Python dependencies

## Backend architecture

The project follows a clear layered pattern:

- [backend/app/app.py](./backend/app/app.py)
  - Creates the FastAPI app
  - Exposes simple health endpoints like /health and /db-check

- [backend/database.py](./backend/database.py)
  - Builds the async SQLAlchemy engine
  - Creates the async session factory
  - Exposes get_db() for dependency injection

- [backend/core/config.py](./backend/core/config.py)
  - Loads environment variables
  - Stores app settings such as database URL, JWT secret, token lifetimes, SMTP config

- [backend/app/auth/](./backend/app/auth/)
  - Contains auth-related business logic and routes
  - Includes:
    - auth_services.py — JWT generation, password hashing, email helpers
    - auth_router.py — API route definitions
    - auth_controller.py — auth endpoint logic
    - dependencies.py — auth-related dependencies
    - models/ — SQLAlchemy models + Pydantic schemas

## Auth domain

The auth module is structured around:

- Models in [backend/app/auth/models/model.py](./backend/app/auth/models/model.py)
  - User
  - OAuthAccount
  - RefreshToken

- Schemas in [backend/app/auth/models/scheme.py](./backend/app/auth/models/scheme.py)
  - Token
  - TokenData
  - RefreshTokenRequest
  - UserCreate
  - UserUpdate
  - UserRead

These files indicate the intended architecture:
- SQLAlchemy models define the database tables
- Pydantic schemas validate request/response payloads
- auth_services.py contains the business logic for user creation, token issuance, and email flows

## Runtime / startup

The app starts from [backend/main.py](./backend/main.py):

- It imports the FastAPI app from app.app
- Starts uvicorn on:
  - host: 127.0.0.1
  - port: 8000
  - reload enabled

Typical local run:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Environment variables needed

The app expects environment values to be loaded at runtime, especially in [backend/core/config.py](./backend/core/config.py). At minimum, expect:

- DATABASE_URL
- SECRET_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES
- REFRESH_TOKEN_EXPIRE_MINUTES
- ALGORITHM
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASSWORD
- FRONTEND_URL

Some variables may differ from the names currently used in the config file, so check those values carefully before running the app.

## Important notes for agents

- This project is in an early stage and some auth files look partially implemented or placeholder-based.
- The auth controller and dependencies may need review before thinking they are production-ready.
- Use the async SQLAlchemy pattern consistently.
- Keep database access isolated through get_db() and async sessions.
- Keep the app structure organized by feature domain rather than placing logic directly in main.py.
- Prefer the existing split:
  - models = database representation
  - scheme = schema/validation contracts
  - services = business logic
  - router/controller = HTTP layer

## Current app status

The backend currently exposes basic endpoints:

- /health
- /db-check

These are simple validation endpoints and are a good place to confirm that the app boots correctly before adding more features.

## Recommended working style

When making changes:

1. Read the relevant feature folder first
2. Follow existing naming conventions
3. Keep SQLAlchemy models and Pydantic schemas separate
4. Reuse database session injection via get_db()
5. Avoid mixing auth logic directly into the app entry file
6. Preserve the current FastAPI project layout unless a larger refactor is explicitly required

This repo is compact, but the backend structure is already clear enough for feature work and agent-assisted changes.
