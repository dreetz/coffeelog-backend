# CoffeLog Backend

Backend for storing collected data from coffee counter.

## Changelog

### 2025-09-13

- Added CORS middleware
- Make offset + limit optional for coffee endpoint

### 2025-07-02

- Migrate from SQLModel to SQLAlchemy and Alembic

### 2025-07-01

- Move repository to gitlab
- Migrate to [uv](https://github.com/astral-sh/uv) as a package manager
- Update base image to python 3.12