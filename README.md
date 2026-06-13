 # Waste-IQ MVP

Waste-IQ is a recyclable waste pickup marketplace for Kolkata. Citizens create pickup requests, collectors accept and complete them, and admins monitor marketplace activity.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT
- Frontend: React, Vite, Tailwind CSS, React Router, Axios
- Media: Cloudinary unsigned uploads from the frontend
- Deployment: Docker, Render

## Project Structure

```text
waste-iq/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   `-- services/
|   |-- alembic/
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- contexts/
|   |   `-- pages/
|   |-- Dockerfile
|   `-- package.json
|-- docker-compose.yml
`-- render.yaml
```

## Features

- Citizen registration, login, and authenticated profile lookup
- Pickup request creation with waste photo upload support
- Role-based pickup request visibility
- Collector accept and complete flows with collected weight entry
- Admin user directory and analytics dashboard
- Auto-generated OpenAPI docs at `/docs`

## Core API

### Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Pickup Requests

- `POST /pickup-requests`
- `GET /pickup-requests`
- `GET /pickup-requests/{id}`
- `PATCH /pickup-requests/{id}`

### Collector

- `POST /collector/accept/{request_id}`
- `POST /collector/complete/{request_id}`

### Admin

- `GET /admin/users`
- `GET /admin/analytics`

## Local Development

### 1. Backend

```bash
cd waste-iq/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` and Swagger docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd waste-iq/frontend
npm install
copy .env.example .env
npm run dev
```

The frontend will run at `http://localhost:5173`.

### 3. PostgreSQL

Use a local PostgreSQL database and set `DATABASE_URL` in `backend/.env`, or start the full stack with Docker Compose.

## Docker Setup

```bash
cd waste-iq
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Environment Variables

### Backend

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS`
- `ADMIN_REGISTRATION_CODE`
- `BOOTSTRAP_ADMIN_NAME`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PHONE`
- `BOOTSTRAP_ADMIN_PASSWORD`

### Frontend

- `VITE_API_BASE_URL`
- `VITE_CLOUDINARY_CLOUD_NAME`
- `VITE_CLOUDINARY_UPLOAD_PRESET`

## Cloudinary Setup

1. Create a Cloudinary account.
2. Create an unsigned upload preset.
3. Put the cloud name and preset in `frontend/.env`.

## Render Deployment

- `render.yaml` provisions:
  - one Dockerized FastAPI web service
  - one Dockerized React web service
  - one PostgreSQL database

Before deploying, set production Cloudinary values on the frontend service and optional bootstrap admin credentials on the backend service.

## Notes

- Public registration supports `citizen` and `collector`.
- `admin` registration requires `ADMIN_REGISTRATION_CODE`.
- On startup, the backend can create a bootstrap admin automatically when the `BOOTSTRAP_ADMIN_*` variables are set.
