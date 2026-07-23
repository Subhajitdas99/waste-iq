# Waste-IQ

AI-ready circular economy platform for recyclable waste pickup, collector operations, dealer onboarding, and municipal analytics.

![MIT License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111111)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-ready-2088FF?logo=githubactions&logoColor=white)
![Tests Passing](https://img.shields.io/badge/Tests-133%20passing-brightgreen)

Waste-IQ connects citizens, collectors, dealers, recyclers, municipalities, and industries in one recyclable waste management workflow. Citizens create pickup requests, collectors accept and complete jobs, dealers maintain verified business profiles, and admins monitor users, requests, dealer verification, inventory, and marketplace analytics.

The project is built as a full-stack marketplace foundation with FastAPI, PostgreSQL, React, Docker, JWT authentication, role-based access control, pickup timelines, collector operations, dealer verification, inventory lots, pricing rules, and a roadmap for AI-assisted waste recognition and circular economy intelligence.

## Project Screenshots

> [!NOTE]
> Screenshots are placeholders. Add production screenshots when the hosted application UI is finalized.

| Citizen Dashboard | Collector Workspace | Admin Analytics |
| --- | --- | --- |
| `docs/screenshots/citizen-dashboard.png` | `docs/screenshots/collector-workspace.png` | `docs/screenshots/admin-analytics.png` |

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [API](#api)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Business Model](#business-model)
- [Future AI](#future-ai)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Features

| Capability | Citizen | Collector | Dealer | Admin |
| --- | --- | --- | --- | --- |
| Secure registration and login | ✅ | ✅ | ✅ | ✅ |
| JWT authentication | ✅ | ✅ | ✅ | ✅ |
| Role-based dashboards | ✅ | ✅ | ✅ | ✅ |
| Create pickup requests | ✅ | ❌ | ❌ | ❌ |
| View pickup request list | ✅ | ✅ | ❌ | ✅ |
| Pickup request details and timeline | ✅ | ✅ | ❌ | ✅ |
| Cancel eligible pickup requests | ✅ | ❌ | ❌ | ❌ |
| Accept collector jobs | ❌ | ✅ | ❌ | ❌ |
| Start, collect, and complete pickups | ❌ | ✅ | ❌ | ❌ |
| Report collected weight | ❌ | ✅ | ❌ | ❌ |
| Dealer profile submission | ❌ | ❌ | ✅ | ❌ |
| Dealer verification workflow | ❌ | ❌ | ❌ | ✅ |
| Inventory lots and material categories | ❌ | ❌ | 🚧 | ✅ |
| Pricing rules | ❌ | ❌ | ❌ | ✅ |
| Inventory reservations | ❌ | ❌ | 🚧 | ✅ |
| Municipality dashboard | ❌ | ❌ | ❌ | 🚧 |
| AI waste recognition | 🚧 | 🚧 | 🚧 | 🚧 |

---

## Architecture

```mermaid
graph TD
  Citizen["Citizen"] --> Frontend["React Frontend"]
  Frontend --> FastAPI["FastAPI Backend"]
  FastAPI --> PostgreSQL["PostgreSQL"]
  PostgreSQL --> Collectors["Collectors"]
  Collectors --> Dealers["Dealers"]
  Dealers --> Municipality["Municipality Dashboard"]
```

Waste-IQ uses a separated frontend, backend, database, and deployment model. The frontend talks to the FastAPI backend through a shared API layer, while backend routes delegate business logic to service modules and persist data through SQLAlchemy models and Alembic migrations.

---

## Tech Stack

### Backend

| Area | Technology |
| --- | --- |
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT, python-jose, Passlib bcrypt |
| Validation | Pydantic |
| Server | Uvicorn |

### Frontend

| Area | Technology |
| --- | --- |
| UI runtime | React 18 |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Routing | React Router |
| Server state | TanStack React Query |
| Forms | React Hook Form, Zod |
| HTTP | Axios through a shared API client |

### Database

| Area | Technology |
| --- | --- |
| Primary database | PostgreSQL |
| Driver | psycopg |
| Local container | PostgreSQL 16 Alpine |

### DevOps

| Area | Technology |
| --- | --- |
| Containers | Docker |
| Local orchestration | Docker Compose |
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| CI target | GitHub Actions |

### AI

| Area | Status |
| --- | --- |
| YOLO / OpenCV recognition | Planned |
| PyTorch / TensorFlow models | Planned |
| LangChain workflows | Planned |
| Vector database search | Planned |
| LLM-assisted analytics | Planned |

---

## Project Structure

```text
waste-iq/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
├── tests/
│   └── See backend/tests/
├── docker/
│   └── Docker assets are currently represented by docker-compose.yml and app Dockerfiles.
├── .github/
│   └── Add GitHub Actions workflows here when CI is configured.
├── docker-compose.yml
└── render.yaml
```

---

## Installation

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run Alembic migrations:

```bash
alembic upgrade head
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Running Locally

### Docker Compose

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8000` |
| Health check | `http://localhost:8000/health` |

### Manual Development

Run PostgreSQL locally, start the backend from `backend/`, and start the frontend from `frontend/`.

---

## Environment Variables

Create a backend `.env` file:

```env
DATABASE_URL=postgresql+psycopg://wasteiq:wasteiq@localhost:5432/wasteiq
ENVIRONMENT=development
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ADMIN_REGISTRATION_CODE=change-me
CORS_ORIGINS=http://localhost:5173

# Optional: Cloudinary Configuration for Image Uploads
# If these are not provided, local development will skip uploads and save image_url as NULL.
# In production, valid credentials are required for image uploads to succeed.
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

Local development can leave the Cloudinary variables empty. In that mode, `POST /pickup-requests` still succeeds and stores `image_url` as `NULL`. In production (`ENVIRONMENT=production`), image uploads require valid Cloudinary credentials and failed uploads return a controlled `502` or `503` response instead of an unhandled `500`.

Create a frontend `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

> [!IMPORTANT]
> The current backend settings read `JWT_SECRET_KEY`. Keep `SECRET_KEY` only if your deployment platform expects that name.

---

## API

<details>
<summary><strong>Authentication</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Register a user |
| `POST` | `/auth/login` | Authenticate and return a token |
| `GET` | `/auth/me` | Return the current authenticated user |

</details>

<details>
<summary><strong>Pickup Requests</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/pickup-requests` | Create a pickup request |
| `GET` | `/pickup-requests` | List pickup requests visible to the current role |
| `GET` | `/pickup-requests/citizen/summary` | Get citizen pickup summary |
| `GET` | `/pickup-requests/{request_id}` | Get pickup request details |
| `PATCH` | `/pickup-requests/{request_id}` | Update a pickup request |
| `POST` | `/pickup-requests/{request_id}/cancel` | Cancel an eligible pickup request |

</details>

<details>
<summary><strong>Collector</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/collector/summary` | Get collector job summary |
| `POST` | `/collector/accept/{request_id}` | Accept an open pickup request |
| `POST` | `/collector/start/{request_id}` | Start an accepted pickup |
| `POST` | `/collector/collect/{request_id}` | Mark a pickup as collected |
| `POST` | `/collector/complete/{request_id}` | Complete a pickup with collected weight |

</details>

<details>
<summary><strong>Dealer</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/dealer/profile` | Create dealer profile |
| `GET` | `/dealer/profile` | Get dealer profile |
| `PATCH` | `/dealer/profile` | Update dealer profile |

</details>

<details>
<summary><strong>Admin</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/admin/users` | List users |
| `GET` | `/admin/analytics` | Get platform analytics |
| `GET` | `/admin/dealers` | List dealer verification summaries |
| `POST` | `/admin/dealers/{dealer_user_id}/approve` | Approve a dealer |
| `POST` | `/admin/dealers/{dealer_user_id}/reject` | Reject a dealer |

</details>

<details>
<summary><strong>Inventory</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/admin/material-categories` | Create a material category |
| `GET` | `/admin/material-categories` | List material categories |
| `GET` | `/admin/eligible-pickups` | List pickups eligible for inventory |
| `GET` | `/admin/inventory-lots` | List admin inventory lots |
| `POST` | `/admin/inventory-lots` | Create an inventory lot |
| `GET` | `/admin/inventory-lots/{lot_id}` | Get admin inventory lot details |
| `PATCH` | `/admin/inventory-lots/{lot_id}` | Update an inventory lot |
| `POST` | `/admin/inventory-lots/{lot_id}/archive` | Archive an inventory lot |
| `POST` | `/admin/inventory-lots/{lot_id}/restore` | Restore an inventory lot |
| `GET` | `/admin/inventory-lots/{lot_id}/events` | List inventory lot events |
| `GET` | `/dealer/inventory-lots` | Browse dealer marketplace lots |
| `GET` | `/dealer/inventory-lots/{lot_id}` | Get dealer marketplace lot details |

</details>

<details>
<summary><strong>Pricing</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/admin/pricing-rules` | List pricing rules |
| `POST` | `/admin/pricing-rules` | Create a pricing rule |
| `PATCH` | `/admin/pricing-rules/{pricing_rule_id}` | Update a pricing rule |
| `POST` | `/admin/pricing-rules/{pricing_rule_id}/activate` | Activate a pricing rule |
| `POST` | `/admin/pricing-rules/{pricing_rule_id}/deactivate` | Deactivate a pricing rule |

</details>

<details>
<summary><strong>Reservations</strong></summary>

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/dealer/inventory-lots/{lot_id}/reserve` | Reserve an available inventory lot |

</details>

---

## Testing

### Backend

```bash
cd backend
python -m pytest
```

Backend test coverage currently includes authentication, citizens, collectors, dealers, permissions, health, inventory, pricing, reservations, and pickup image upload scenarios.

**133 Passing Tests**

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

---

## Deployment

| Layer | Target |
| --- | --- |
| Backend | Railway |
| Frontend | Vercel |
| Database | PostgreSQL |
| Containers | Docker and Docker Compose |

> [!TIP]
> Set `CORS_ORIGINS` to the deployed frontend origin when running the backend in production.

---

## Roadmap

### Phase 1: Marketplace

- [x] User authentication
- [x] Citizen pickup creation
- [x] Pickup list and details
- [x] Admin analytics
- [x] Completed

### Phase 2: Collector Workspace

- [x] Collector summary
- [x] Accept pickups
- [x] Start, collect, and complete pickups
- [ ] In Progress

### Phase 3: Dealer Marketplace

- [x] Dealer profile
- [x] Admin dealer verification
- [x] Inventory lot foundation
- [ ] Planned

### Phase 4: Municipality Dashboard

- [ ] City-level recycling metrics
- [ ] Collection heatmaps
- [ ] Operator performance reports
- [ ] Planned

### Phase 5: AI Waste Recognition

- [ ] Image classification
- [ ] Material detection
- [ ] Quality estimation
- [ ] Planned

### Phase 6: Analytics & Carbon Credits

- [ ] Carbon impact tracking
- [ ] Recycling contribution reports
- [ ] Carbon credit workflows
- [ ] Planned

---

## Business Model

| Model | Description |
| --- | --- |
| Commission | Platform fee on completed recyclable waste transactions |
| Subscriptions | Premium dashboards for dealers, recyclers, and municipalities |
| Enterprise | Waste intelligence and operational reporting for organizations |
| Carbon Credits | Future sustainability tracking and carbon accounting workflows |

---

## Future AI

Waste-IQ is structured to support AI-assisted recycling operations without coupling current marketplace workflows to experimental models.

| AI Area | Planned Use |
| --- | --- |
| YOLO | Waste object detection from images |
| OpenCV | Image preprocessing and material segmentation |
| PyTorch | Custom waste classification models |
| TensorFlow | Alternative model training and deployment workflows |
| LangChain | LLM-powered operational assistants and reporting workflows |
| Vector Database | Search over waste images, material metadata, and historical pickups |
| LLMs | Admin insights, support workflows, and natural language analytics |
| Collector Recommendation | Match pickups to collectors by distance, capacity, and activity |
| Dynamic Pricing | Suggest material pricing based on demand and supply |
| Demand Forecasting | Predict city-level pickup and material volume trends |
| Carbon Tracking | Estimate avoided emissions from recovered recyclable materials |

---

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit focused changes.
4. Push your branch.
5. Open a pull request.

```bash
git checkout -b feature/your-feature-name
git commit -m "Add your feature"
git push origin feature/your-feature-name
```

> [!NOTE]
> Keep backend changes covered by tests and run frontend lint/build before opening a pull request.

---

## License

MIT License

Copyright (c) 2026 Waste-IQ

---

## Author

**Subhajit Das**  
B.Tech AI & ML

| Link | URL |
| --- | --- |
| GitHub | [github.com/Subhajitdas99](https://github.com/Subhajitdas99) |
| LinkedIn | https://www.linkedin.com/in/subhajit-das-8207ab240/ |
| Email | dassubhojit750075@gmail.com |
