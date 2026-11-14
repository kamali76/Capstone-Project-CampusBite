# CampusBite

Full-stack restaurant ordering and delivery app for a campus: customers order food, restaurant owners
manage menus and orders, delivery partners deliver them.

| Layer    | Tech                                                                                                                                                |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend | React 19 (Vite), React Router, Axios, hooks (`useState`, `useEffect`, `useReducer`, `useContext`, `useMemo`, `useCallback`, `useRef`, custom hooks) |
| Backend  | FastAPI, Pydantic v2, SQLAlchemy 2, JWT (PyJWT), bcrypt                                                                                             |
| Database | SQLite (tables are created automatically on startup)                                                                                                |
| AI       | OpenAI Chat Completions (order insights for customers)                                                                                              |
| DevOps   | Docker + Docker Compose (backend)                                                                                                                   |

## Features

- **Roles:** Customer, Restaurant Owner, Delivery Partner. Access is enforced **on the backend** (RBAC), not just by hiding UI.
- **Order lifecycle:** `PLACED → ACCEPTED → PREPARING → READY → ASSIGNED → OUT_FOR_DELIVERY → DELIVERED`, plus `CANCELLED` and `REFUNDED`.
  Each transition is allowed for one specific role only.
- **Dummy payment** (`mock_paid`) with a **payment ledger** (charge and refund entries).
- **Returns / refunds:** customer requests a return on a delivered order; the owner approves (refund) or rejects.
- **Reviews:** one review per delivered order.
- **Reminders:** orders stuck in `PLACED` / `ACCEPTED` for more than 15 minutes show up in the owner's reminders
  (background job + on-demand check; no duplicate reminders).
- **Middleware:** request logging, `X-Process-Time` and `X-Request-ID` headers.
- **Pagination and filters** on lists (status, date range, menu search, price range).
- **AI order insights:** customers can ask questions about their own order history.

## Project structure

```
CampusBite/
├── Frontend/            React app (Vite)
├── Backend/             FastAPI app, tests, Dockerfile
├── docker-compose.yml   Runs the backend (with a persistent SQLite volume)
└── README.md
```

## Run the backend (Docker Compose)

```bash
cp Backend/.env.example Backend/.env
# generate a secret and paste it as JWT_SECRET in Backend/.env
python -c "import secrets; print(secrets.token_hex(32))"
# (optional) put your OpenAI key in OPENAI_API_KEY to enable AI insights

docker compose up --build
```

The API runs at <http://localhost:8000>. Interactive API docs (Swagger): <http://localhost:8000/docs>.

### Run the backend without Docker

```bash
cd Backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then set JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

### Run the tests

```bash
cd Backend
pip install -r requirements-dev.txt
pytest
```

## Run the frontend

```bash
cd Frontend
npm install
cp .env.example .env        # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open <http://localhost:5173>. The backend must be running. If you change `.env`, restart `npm run dev`.

## Environment variables (`Backend/.env`)

| Variable                      | Purpose                                                                                                                  | Default                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| `JWT_SECRET`                  | Signs login tokens. **Set this.** If empty, a random one is generated on each start (everyone is logged out on restart). | empty                            |
| `DATABASE_URL`                | Database connection string                                                                                               | `sqlite:///./data/campusbite.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login token lifetime                                                                                                     | `1440`                           |
| `CORS_ORIGINS`                | Allowed frontend origins (comma separated)                                                                               | `http://localhost:5173`          |
| `REMINDER_AFTER_MINUTES`      | Age after which a PLACED/ACCEPTED order triggers a reminder                                                              | `15`                             |
| `SEED_DEMO_DATA`              | Create demo restaurants and users when the DB is empty                                                                   | `true`                           |
| `SEED_DEMO_PASSWORD`          | Password for the demo accounts                                                                                           | `Demo@1234`                      |
| `OPENAI_API_KEY`              | Enables AI insights                                                                                                      | empty                            |
| `OPENAI_MODEL`                | Model used for AI insights                                                                                               | `gpt-4o-mini`                    |

Real secrets live only in `Backend/.env`, which is git-ignored. Only `.env.example` (blank values) is committed.

## Database setup

SQLite is used for simplicity. Tables are created automatically on first start and, when `SEED_DEMO_DATA=true`,
demo data is added. With Docker the database file lives in the `campusbite_data` volume, so it survives restarts.
To reset it: `docker compose down -v`.

## Demo accounts (password `Demo@1234`)

| Role             | Email                                                  |
| ---------------- | ------------------------------------------------------ |
| Customer         | `customer@campusbite.com`                              |
| Restaurant owner | `owner1@campusbite.com` … `owner4@campusbite.com`      |
| Delivery partner | `delivery1@campusbite.com`, `delivery2@campusbite.com` |

You can also register new users from the UI (owners get a restaurant created automatically).

## Main API endpoints

| Area     | Endpoints                                                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Auth     | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`                                                                                                                            |
| Browse   | `GET /restaurants`, `GET /restaurants/{id}/menu?search=&min_price=&max_price=`                                                                                                       |
| Customer | `POST /orders`, `GET /orders`, `POST /orders/{id}/cancel`, `POST /orders/{id}/review`, `POST /orders/{id}/return`                                                                    |
| Owner    | `/owner/restaurant`, `/owner/menu-items`, `/owner/orders`, `PATCH /owner/orders/{id}/status`, `POST /owner/orders/{id}/assign`, `/owner/returns`, `/owner/stats`, `/owner/reminders` |
| Delivery | `/delivery/orders`, `PATCH /delivery/orders/{id}/status`, `/delivery/history`                                                                                                        |
| AI       | `POST /ai/insights`                                                                                                                                                                  |
| System   | `GET /health`                                                                                                                                                                        |

## AI order insights

Set `OPENAI_API_KEY` in `Backend/.env` and restart. In the app, log in as a customer and open **AI Insights**.
Only the logged-in customer's own orders are sent to the model (the customer id comes from the login token, never from
the request), totals are computed in code, and requests are rate limited per customer.

## Notes

- Money is stored as floating-point numbers for simplicity; a production system should use decimals / integer paise.
- Payment is simulated; no real payment provider is involved.
