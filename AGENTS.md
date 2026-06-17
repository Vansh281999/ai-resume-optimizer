# Development Commands

## Backend
- `python -m pytest tests/ -v` - Run all backend tests
- `pip install -e ".[dev]"` - Install with dev dependencies

## Frontend
- `npm run test` - Run frontend tests
- `npm run build` - Build frontend for production
- `npm run typecheck` - TypeScript type checking

## Database
- `alembic upgrade head` - Apply migrations
- `alembic revision --autogenerate -m "description"` - Create migration

## Environment
- `SECRET_KEY` - Required. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`