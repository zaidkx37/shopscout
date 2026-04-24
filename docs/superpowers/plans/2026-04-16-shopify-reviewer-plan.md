# Shopify Review Automation Tool - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an internal tool that automates Shopify product review submissions via Trustoo, with a React dashboard for campaign management and scheduling.

**Architecture:** Python FastAPI monolith with SQLite + APScheduler for the backend, React + Vite SPA for the frontend. Single Docker container deployment. ShopScout pip package for Shopify store data.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy (async/aiosqlite), APScheduler, httpx, React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Recharts

**Spec:** `docs/superpowers/specs/2026-04-16-shopify-reviewer-design.md`

**New project location:** `D:/Projects/shopify-reviewer/` (separate repo from ShopScout)

**Note on frontend tests:** Frontend tasks do not include unit tests. This is an internal single-user admin tool; backend API tests provide sufficient coverage. Frontend correctness is verified via manual smoke tests in Task 14.

---

## File Structure

```
shopify-reviewer/
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, lifespan, static mount
│   │   ├── config.py               # Pydantic Settings from env vars
│   │   ├── database.py             # async SQLite engine, session factory, table creation
│   │   ├── models.py               # SQLAlchemy ORM models (6 tables + join table)
│   │   ├── auth.py                 # Signed cookie auth, middleware, dependency
│   │   ├── store.py                # ShopScout integration, shop_id scraper, sync logic
│   │   ├── campaigns.py            # Campaign CRUD, distribution algorithm, validation
│   │   ├── scheduler.py            # APScheduler setup, job creation, schedule generation
│   │   ├── submitter.py            # BaseSubmitter ABC, TrustooSubmitter, safety layers
│   │   └── routes/
│   │       ├── __init__.py         # Router aggregation
│   │       ├── auth.py             # POST login/logout, GET me
│   │       ├── health.py           # GET /api/health
│   │       ├── store.py            # GET store, POST sync, GET collections, GET products
│   │       ├── campaigns.py        # Full campaign CRUD + start/pause/resume
│   │       ├── reviews.py          # GET reviews, GET logs (per-campaign + global), POST retry
│   │       └── stats.py            # GET /api/stats with time-series + per-collection data
│   └── tests/
│       ├── conftest.py             # Test DB fixture, test client, env vars setup
│       ├── test_config.py          # Config loading tests
│       ├── test_models.py          # Model creation, constraints, relationships
│       ├── test_auth.py            # Login, logout, session validation, protected routes
│       ├── test_store.py           # Sync logic, shop_id scraping, error handling
│       ├── test_campaigns.py       # CRUD, validation, state transitions
│       ├── test_distribution.py    # Distribution algorithm, uniqueness, cross-collection dedup
│       ├── test_scheduler.py       # Schedule generation, jitter, gap enforcement, cross-campaign
│       ├── test_submitter.py       # Trustoo POST, retry, circuit breaker, rate limiting
│       └── test_routes.py          # API endpoint integration tests
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── index.html
│   ├── postcss.config.js
│   ├── components.json            # shadcn/ui config
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                 # Router setup
│       ├── index.css               # Tailwind imports
│       ├── lib/
│       │   └── utils.ts            # cn() helper
│       ├── api/
│       │   └── client.ts           # Fetch wrapper with auth, base URL
│       ├── hooks/
│       │   └── use-auth.ts         # Auth context + hook
│       ├── components/
│       │   ├── ui/                 # shadcn components (installed via CLI)
│       │   ├── layout/
│       │   │   ├── sidebar.tsx
│       │   │   └── app-layout.tsx
│       │   ├── stat-card.tsx
│       │   ├── status-badge.tsx
│       │   └── json-upload.tsx
│       └── pages/
│           ├── login.tsx
│           ├── dashboard.tsx
│           ├── store.tsx
│           ├── campaigns.tsx
│           ├── campaign-detail.tsx
│           ├── new-campaign.tsx
│           ├── logs.tsx
│           └── settings.tsx
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Phase 1: Backend Core

### Task 1: Project Scaffolding + Config + Database Models

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py` (empty)
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_config.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Create project directory and pyproject.toml**

Create `D:/Projects/shopify-reviewer/` directory and `backend/pyproject.toml`:

```toml
[project]
name = "shopify-reviewer"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "aiosqlite>=0.20",
    "httpx>=0.27",
    "apscheduler>=3.10,<4",
    "itsdangerous>=2.2",
    "pydantic-settings>=2.5",
    "shopscout>=0.1",
    "beautifulsoup4>=4.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx",
    "ruff>=0.6",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100
```

- [ ] **Step 2: Create conftest.py with test env vars and DB fixture**

Write `backend/tests/conftest.py`:

```python
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test env vars BEFORE importing app modules
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "pass"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["STORE_DOMAIN"] = "spharetech.com"

from app.database import Base


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
```

- [ ] **Step 3: Write config tests**

Write `backend/tests/test_config.py`:

```python
import os
import pytest
from app.config import Settings


def test_settings_loads_defaults():
    settings = Settings(
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="pass",
        SECRET_KEY="test-secret",
    )
    assert settings.STORE_DOMAIN == "spharetech.com"
    assert settings.TIMEZONE == "Asia/Karachi"
    assert settings.MAX_REQUESTS_PER_HOUR == 10
    assert settings.MIN_SUBMISSION_GAP_SECONDS == 120
    assert "aiosqlite" in settings.DATABASE_URL


def test_settings_requires_admin_credentials():
    with pytest.raises(Exception):
        Settings(SECRET_KEY="test")


def test_settings_requires_secret_key():
    with pytest.raises(Exception):
        Settings(ADMIN_USERNAME="admin", ADMIN_PASSWORD="pass")
```

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement config module**

Write `backend/app/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    SECRET_KEY: str
    STORE_DOMAIN: str = "spharetech.com"
    TIMEZONE: str = "Asia/Karachi"
    MAX_REQUESTS_PER_HOUR: int = 10
    MIN_SUBMISSION_GAP_SECONDS: int = 120
    DATABASE_URL: str = "sqlite+aiosqlite:///data/reviewer.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Create database module**

Write `backend/app/database.py`:

```python
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = None
async_session_factory = None


async def init_db(database_url: str):
    global engine, async_session_factory
    engine = create_async_engine(database_url, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sqlalchemy.text("PRAGMA foreign_keys = ON"))


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 6: Write model tests**

Write `backend/tests/test_models.py`:

```python
import pytest
from sqlalchemy import select, insert
from app.models import Store, Collection, Product, Campaign, Review, SubmissionLog, collection_product


async def test_create_store(db_session):
    store = Store(domain="test.com", shop_id=12345, name="Test Store", currency="USD")
    db_session.add(store)
    await db_session.commit()
    result = await db_session.execute(select(Store))
    assert result.scalar_one().domain == "test.com"


async def test_store_domain_unique(db_session):
    db_session.add(Store(domain="test.com", shop_id=1, name="A", currency="USD"))
    await db_session.commit()
    db_session.add(Store(domain="test.com", shop_id=2, name="B", currency="USD"))
    with pytest.raises(Exception):
        await db_session.commit()


async def test_review_content_hash_unique(db_session):
    store = Store(domain="test.com", shop_id=1, name="A", currency="USD")
    db_session.add(store)
    await db_session.flush()
    campaign = Campaign(store_id=store.id, name="Test", status="draft", total_reviews=0)
    db_session.add(campaign)
    await db_session.flush()
    r1 = Review(
        campaign_id=campaign.id, name="Ali", email="ali@x.com",
        rating=5, content="Great!", content_hash="hash1", status="pending"
    )
    r2 = Review(
        campaign_id=campaign.id, name="Sara", email="sara@x.com",
        rating=4, content="Nice!", content_hash="hash1", status="pending"
    )
    db_session.add_all([r1, r2])
    with pytest.raises(Exception):
        await db_session.commit()


async def test_product_belongs_to_multiple_collections(db_session):
    store = Store(domain="test.com", shop_id=1, name="A", currency="USD")
    db_session.add(store)
    await db_session.flush()
    c1 = Collection(store_id=store.id, handle="c1", title="C1", products_count=0)
    c2 = Collection(store_id=store.id, handle="c2", title="C2", products_count=0)
    db_session.add_all([c1, c2])
    await db_session.flush()
    p = Product(store_id=store.id, shopify_product_id=999, handle="prod", title="Prod")
    db_session.add(p)
    await db_session.flush()
    await db_session.execute(insert(collection_product).values(collection_id=c1.id, product_id=p.id))
    await db_session.execute(insert(collection_product).values(collection_id=c2.id, product_id=p.id))
    await db_session.commit()


async def test_collection_store_handle_unique(db_session):
    store = Store(domain="test.com", shop_id=1, name="A", currency="USD")
    db_session.add(store)
    await db_session.flush()
    db_session.add(Collection(store_id=store.id, handle="same", title="C1", products_count=0))
    await db_session.commit()
    db_session.add(Collection(store_id=store.id, handle="same", title="C2", products_count=0))
    with pytest.raises(Exception):
        await db_session.commit()
```

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: FAIL (models not defined)

- [ ] **Step 7: Implement all SQLAlchemy models**

Write `backend/app/models.py` with all 6 tables + join table matching the spec schema exactly. Include:
- `Store`, `Collection`, `Product`, `Campaign`, `Review`, `SubmissionLog`
- `collection_product` association table
- Unique constraints: `Store.domain`, `Review.content_hash`, `Product.shopify_product_id`, `UniqueConstraint(Collection.store_id, Collection.handle)`
- Relationships: Store -> Collections, Store -> Products, Collection <-> Product (M2M via collection_product), Campaign -> Reviews, Review -> SubmissionLogs, Campaign -> Store
- Default values matching spec (active_hours_start=9, active_hours_end=23, retry_count=0)

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 8: Create minimal FastAPI app**

Write `backend/app/__init__.py` (empty).
Write `backend/tests/__init__.py` (empty).

Write `backend/app/main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import Settings
from app.database import init_db

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.DATABASE_URL)
    yield


app = FastAPI(title="Shopify Reviewer", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 9: Commit**

```bash
git init
git add -A
git commit -m "feat: project scaffolding with config, database, and ORM models"
```

---

### Task 2: Auth Module

**Files:**
- Create: `backend/app/auth.py`
- Create: `backend/app/routes/auth.py`
- Create: `backend/app/routes/__init__.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

Write `backend/tests/test_auth.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_login_success(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    assert resp.status_code == 200
    assert "session" in resp.cookies


async def test_login_wrong_password(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


async def test_me_without_session(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_with_session(client):
    login = await client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    cookies = login.cookies
    resp = await client.get("/api/auth/me", cookies=cookies)
    assert resp.status_code == 200


async def test_logout(client):
    login = await client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    cookies = login.cookies
    resp = await client.post("/api/auth/logout", cookies=cookies)
    assert resp.status_code == 200
```

Note: env vars are already set in `conftest.py` (ADMIN_USERNAME=admin, ADMIN_PASSWORD=pass, SECRET_KEY set).

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: FAIL

- [ ] **Step 2: Implement auth module**

Write `backend/app/auth.py`:
- `create_session_cookie(username: str) -> str` using itsdangerous `URLSafeTimedSerializer`
- `verify_session_cookie(cookie: str) -> str | None` returns username or None
- `require_auth` FastAPI dependency that reads cookie from request, verifies, raises HTTPException(401) if invalid

Write `backend/app/routes/__init__.py` that creates an `api_router` and includes all sub-routers.

Write `backend/app/routes/auth.py`:
- `POST /api/auth/login` - validates credentials against settings, sets signed cookie
- `POST /api/auth/logout` - deletes cookie
- `GET /api/auth/me` - returns `{"username": ...}` if authenticated

Update `backend/app/main.py` to include the router.

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: auth module with signed cookie sessions"
```

---

### Task 3: Store Resolver Module

**Files:**
- Create: `backend/app/store.py`
- Create: `backend/app/routes/store.py`
- Test: `backend/tests/test_store.py`

**Note on shop_id scraping:** Verified via existing POC (`Reviewer/test_scrape.py` in the ShopScout repo). The product page contains `<script data-page-type="product" data-shop-id="79801712886" data-product-id="...">`. The `data-shop-id` attribute is confirmed present on spharetech.com.

- [ ] **Step 1: Write store resolver tests**

Write `backend/tests/test_store.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.store import scrape_shop_id, sync_store


def test_scrape_shop_id_from_html():
    html = '<html><script data-page-type="product" data-shop-id="79801712886" data-product-id="123"></script></html>'
    result = scrape_shop_id(html)
    assert result == 79801712886


def test_scrape_shop_id_missing_tag():
    html = '<html><body>No script tag</body></html>'
    result = scrape_shop_id(html)
    assert result is None


def test_scrape_shop_id_missing_attribute():
    html = '<html><script data-page-type="product" data-product-id="123"></script></html>'
    result = scrape_shop_id(html)
    assert result is None


async def test_sync_store_creates_store_record(db_session):
    mock_shop = MagicMock()
    mock_store = MagicMock()
    mock_store.name = "Test Store"
    mock_store.currency = "PKR"
    mock_shop.store.return_value = mock_store
    mock_shop.collections.return_value = [
        MagicMock(title="Power Banks", handle="power-banks", products_count=5),
    ]
    mock_product = MagicMock()
    mock_product.id = 111
    mock_product.title = "PB 1"
    mock_product.handle = "pb-1"
    mock_product.images = [MagicMock(src="img.jpg")]
    mock_shop.collection_products.return_value = [mock_product]

    with patch("app.store.Shopify", return_value=mock_shop):
        with patch("app.store.fetch_shop_id", new_callable=AsyncMock, return_value=79801712886):
            result = await sync_store(db_session, "spharetech.com")

    assert result.domain == "spharetech.com"
    assert result.shop_id == 79801712886


async def test_sync_store_error_preserves_cache(db_session):
    """If ShopScout fails, existing cached data should not be deleted."""
    from app.models import Store
    # Pre-populate cache
    store = Store(domain="spharetech.com", shop_id=123, name="Cached", currency="PKR")
    db_session.add(store)
    await db_session.commit()

    with patch("app.store.Shopify", side_effect=Exception("Network error")):
        with pytest.raises(Exception, match="Network error"):
            await sync_store(db_session, "spharetech.com")

    # Cached data should still be there
    from sqlalchemy import select
    result = await db_session.execute(select(Store).where(Store.domain == "spharetech.com"))
    cached = result.scalar_one()
    assert cached.name == "Cached"
```

Run: `cd backend && python -m pytest tests/test_store.py -v`
Expected: FAIL

- [ ] **Step 2: Implement store resolver**

Write `backend/app/store.py`:
- `scrape_shop_id(html: str) -> int | None` - BeautifulSoup parse for `<script data-page-type="product">`, extract `data-shop-id` attribute
- `async fetch_shop_id(domain: str) -> int | None` - fetches a product page via httpx, calls `scrape_shop_id`
- `async sync_store(session, domain) -> Store` - fetches store metadata via ShopScout, scrapes shop_id, upserts store/collection/product records, links via collection_product join table. On error: raises exception, does NOT delete existing cached data.

Write `backend/app/routes/store.py`:
- `GET /api/store` - returns cached store record (or empty object if not synced yet)
- `POST /api/store/sync` - triggers full sync, returns updated store. On error returns 500 with error message.
- `GET /api/collections` - lists collections with product counts
- `GET /api/collections/{handle}/products` - lists products in collection

All routes protected by `require_auth` dependency.

Run: `cd backend && python -m pytest tests/test_store.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: store resolver with ShopScout integration and sync"
```

---

### Task 4: Trustoo Submitter with Safety Layers

**Files:**
- Create: `backend/app/submitter.py`
- Test: `backend/tests/test_submitter.py`

- [ ] **Step 1: Write submitter tests including circuit breaker and rate limiter**

Write `backend/tests/test_submitter.py`:

```python
import pytest
import time
from unittest.mock import AsyncMock, patch
from app.submitter import TrustooSubmitter, SubmissionResult


async def test_successful_submission():
    submitter = TrustooSubmitter(domain="spharetech.com")
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 0, "message": "OK",
        "data": {"review_id": "123", "discount_code": "TT-ABC", "discount_value": "5%"}
    }
    with patch.object(submitter, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await submitter.submit(
            content="Great product", author="Ali", author_email="ali@x.com",
            rating=5, product_id=999, shop_id=111
        )
    assert result.success is True
    assert result.trustoo_review_id == "123"
    assert result.discount_code == "TT-ABC"


async def test_failed_submission_4xx_no_retry():
    submitter = TrustooSubmitter(domain="spharetech.com")
    mock_response = AsyncMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    with patch.object(submitter, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await submitter.submit(
            content="X", author="Y", author_email="y@x.com",
            rating=5, product_id=999, shop_id=111
        )
    assert result.success is False
    assert result.should_retry is False


async def test_retryable_submission_5xx():
    submitter = TrustooSubmitter(domain="spharetech.com")
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    with patch.object(submitter, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await submitter.submit(
            content="X", author="Y", author_email="y@x.com",
            rating=5, product_id=999, shop_id=111
        )
    assert result.success is False
    assert result.should_retry is True


def test_user_agent_rotation():
    submitter = TrustooSubmitter(domain="spharetech.com")
    agents = {submitter._get_random_user_agent() for _ in range(50)}
    assert len(agents) > 1


async def test_circuit_breaker_triggers_after_consecutive_failures():
    submitter = TrustooSubmitter(domain="spharetech.com")
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Error"

    with patch.object(submitter, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        for i in range(5):
            result = await submitter.submit(
                content=f"Review {i}", author="Y", author_email="y@x.com",
                rating=5, product_id=999, shop_id=111
            )
    assert submitter.circuit_open is True


async def test_circuit_breaker_resets_on_success():
    submitter = TrustooSubmitter(domain="spharetech.com")
    submitter._consecutive_failures = 4  # one away from tripping

    mock_success = AsyncMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "code": 0, "message": "OK",
        "data": {"review_id": "1", "discount_code": "", "discount_value": ""}
    }
    with patch.object(submitter, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_success)
        await submitter.submit(
            content="Good", author="Y", author_email="y@x.com",
            rating=5, product_id=999, shop_id=111
        )
    assert submitter._consecutive_failures == 0
    assert submitter.circuit_open is False


def test_rate_limiter_tracks_requests():
    submitter = TrustooSubmitter(domain="spharetech.com", max_requests_per_hour=5)
    assert submitter.can_submit() is True
    # Simulate 5 submissions
    for _ in range(5):
        submitter._record_request()
    assert submitter.can_submit() is False
```

Run: `cd backend && python -m pytest tests/test_submitter.py -v`
Expected: FAIL

- [ ] **Step 2: Implement submitter**

Write `backend/app/submitter.py`:
- `SubmissionResult` dataclass: `success`, `http_status`, `response_body`, `trustoo_review_id`, `discount_code`, `discount_value`, `error_message`, `should_retry`
- `BaseSubmitter` ABC with `submit()` and `health_check()` methods
- `TrustooSubmitter(BaseSubmitter)`:
  - `__init__(domain, max_requests_per_hour=10)` - stores domain, creates httpx client, initializes circuit breaker state and rate limiter
  - `submit(content, author, author_email, rating, product_id, shop_id)` - builds payload, adds random delay (1-5s via `asyncio.sleep`), selects random user-agent, POSTs to Trustoo endpoint, parses response, updates circuit breaker counters, records request for rate limiting, returns `SubmissionResult`
  - `health_check(domain)` - simple GET to store homepage
  - `_get_random_user_agent()` - returns from pool of 8 user-agent strings
  - `circuit_open` property - True if `_consecutive_failures >= 5`
  - `can_submit()` - checks rate limit (tracks request timestamps in a deque, removes entries older than 1 hour)
  - `_record_request()` - appends current timestamp to deque
  - Content-Type: `text/plain;charset=UTF-8`
  - Payload includes `"resources": []`

Run: `cd backend && python -m pytest tests/test_submitter.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: Trustoo submitter with circuit breaker, rate limiter, user-agent rotation"
```

---

### Task 5: Campaign Manager + Distribution Algorithm

**Files:**
- Create: `backend/app/campaigns.py`
- Test: `backend/tests/test_distribution.py`
- Test: `backend/tests/test_campaigns.py`

- [ ] **Step 1: Write distribution algorithm tests**

Write `backend/tests/test_distribution.py`:

```python
import pytest
from app.campaigns import distribute_reviews


def test_even_distribution():
    reviews = [{"name": f"R{i}", "email": f"r{i}@x.com", "rating": 5, "content": f"Review content {i}"} for i in range(6)]
    products = [{"id": 1, "title": "P1"}, {"id": 2, "title": "P2"}, {"id": 3, "title": "P3"}]
    assigned, warnings = distribute_reviews(reviews, products)
    for pid in [1, 2, 3]:
        count = sum(1 for r in assigned if r["product_id"] == pid)
        assert count == 2


def test_no_duplicate_assignments():
    reviews = [{"name": f"R{i}", "email": f"r{i}@x.com", "rating": 5, "content": f"Review content {i}"} for i in range(10)]
    products = [{"id": 1, "title": "P1"}, {"id": 2, "title": "P2"}]
    assigned, _ = distribute_reviews(reviews, products)
    contents = [r["content"] for r in assigned]
    assert len(contents) == len(set(contents))


def test_fewer_reviews_than_products():
    reviews = [{"name": "R1", "email": "r1@x.com", "rating": 5, "content": "Only review here"}]
    products = [{"id": 1, "title": "P1"}, {"id": 2, "title": "P2"}, {"id": 3, "title": "P3"}]
    assigned, warnings = distribute_reviews(reviews, products)
    assert len(assigned) == 1
    assert any("too small" in w.lower() for w in warnings)


def test_empty_reviews():
    assigned, _ = distribute_reviews([], [{"id": 1, "title": "P1"}])
    assert len(assigned) == 0


def test_randomized_assignment():
    reviews = [{"name": f"R{i}", "email": f"r{i}@x.com", "rating": 5, "content": f"Review content {i}"} for i in range(20)]
    products = [{"id": j, "title": f"P{j}"} for j in range(5)]
    a1, _ = distribute_reviews(reviews, products)
    a2, _ = distribute_reviews(reviews, products)
    assignments1 = [(r["content"], r["product_id"]) for r in a1]
    assignments2 = [(r["content"], r["product_id"]) for r in a2]
    assert assignments1 != assignments2


def test_cross_collection_product_dedup():
    """Product appearing in two collections should only get reviews from the first collection."""
    shared_product = {"id": 1, "title": "Shared Product"}
    collection_products = {
        "power-banks": [shared_product, {"id": 2, "title": "PB Only"}],
        "chargers": [shared_product, {"id": 3, "title": "Charger Only"}],
    }
    reviews_by_collection = {
        "power-banks": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "PB review content here"}],
        "chargers": [{"name": "B", "email": "b@x.com", "rating": 5, "content": "Charger review content"}],
    }
    from app.campaigns import distribute_reviews_by_collection
    assigned, warnings = distribute_reviews_by_collection(reviews_by_collection, collection_products)
    # Product 1 should only have reviews from power-banks (first collection)
    product1_reviews = [r for r in assigned if r["product_id"] == 1]
    for r in product1_reviews:
        assert r["content"] == "PB review content here"
```

Run: `cd backend && python -m pytest tests/test_distribution.py -v`
Expected: FAIL

- [ ] **Step 2: Implement distribution algorithm**

Add to `backend/app/campaigns.py`:

```python
import hashlib
import random


def compute_content_hash(content: str, email: str) -> str:
    return hashlib.sha256(f"{content}|{email}".encode()).hexdigest()


def distribute_reviews(
    reviews: list[dict], products: list[dict]
) -> tuple[list[dict], list[str]]:
    warnings = []
    if not reviews:
        return [], warnings

    if len(reviews) < len(products):
        warnings.append(
            f"Review pool too small: {len(reviews)} reviews for {len(products)} products. "
            f"{len(products) - len(reviews)} products will get zero reviews."
        )

    shuffled_reviews = reviews.copy()
    shuffled_products = products.copy()
    random.shuffle(shuffled_reviews)
    random.shuffle(shuffled_products)

    assigned = []
    for i, review in enumerate(shuffled_reviews):
        product = shuffled_products[i % len(shuffled_products)]
        assigned.append({**review, "product_id": product["id"]})

    return assigned, warnings


def distribute_reviews_by_collection(
    reviews_by_collection: dict[str, list[dict]],
    collection_products: dict[str, list[dict]],
) -> tuple[list[dict], list[str]]:
    """Distribute reviews respecting cross-collection product dedup.
    Products are only eligible in the first collection they appear in."""
    all_assigned = []
    all_warnings = []
    seen_product_ids = set()

    for collection_handle, reviews in reviews_by_collection.items():
        products = collection_products.get(collection_handle, [])
        # Filter out products already claimed by an earlier collection
        eligible = [p for p in products if p["id"] not in seen_product_ids]
        seen_product_ids.update(p["id"] for p in eligible)

        if not eligible:
            all_warnings.append(f"Collection '{collection_handle}': no eligible products (all already assigned)")
            continue

        assigned, warnings = distribute_reviews(reviews, eligible)
        all_assigned.extend(assigned)
        all_warnings.extend(warnings)

    return all_assigned, all_warnings
```

Run: `cd backend && python -m pytest tests/test_distribution.py -v`
Expected: PASS

- [ ] **Step 3: Write campaign validation tests**

Write `backend/tests/test_campaigns.py`:

```python
import pytest
from app.campaigns import validate_campaign_input


def test_valid_input():
    data = {
        "name": "Test Campaign",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {
            "power-banks": [
                {"name": "Ali", "email": "ali@x.com", "rating": 5, "content": "Great product really love it"}
            ]
        }
    }
    errors = validate_campaign_input(data, known_collections=["power-banks"])
    assert errors == []


def test_unknown_collection():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"nonexistent": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "Great stuff here"}]}
    }
    errors = validate_campaign_input(data, known_collections=["power-banks"])
    assert any("nonexistent" in e for e in errors)


def test_rating_out_of_range():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": [{"name": "A", "email": "a@x.com", "rating": 6, "content": "Great stuff here"}]}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("rating" in e.lower() for e in errors)


def test_content_too_short():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "Short"}]}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("10 characters" in e for e in errors)


def test_empty_review_array():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": []}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("empty" in e.lower() for e in errors)


def test_missing_email():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": [{"name": "A", "rating": 5, "content": "Great stuff here man"}]}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("email" in e.lower() for e in errors)


def test_too_many_reviews():
    reviews = [{"name": f"R{i}", "email": f"r{i}@x.com", "rating": 5, "content": f"Review content number {i}"} for i in range(1001)]
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": reviews}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("1000" in e for e in errors)


def test_invalid_active_hours():
    data = {
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 23, "end": 9}},
        "reviews": {"c": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "Great stuff here"}]}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("hours" in e.lower() for e in errors)


def test_missing_name():
    data = {
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"c": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "Great stuff here"}]}
    }
    errors = validate_campaign_input(data, known_collections=["c"])
    assert any("name" in e.lower() for e in errors)
```

Run: `cd backend && python -m pytest tests/test_campaigns.py -v`
Expected: FAIL

- [ ] **Step 4: Implement campaign validation**

Add `validate_campaign_input(data, known_collections)` to `backend/app/campaigns.py`:
- Validates all rules from spec: required fields (name, schedule, reviews), rating 1-5, content min 10 chars, email contains @, collection handles exist in `known_collections`, no empty arrays, schedule.active_hours start < end (both 0-23), total review count <= 1000
- Returns list of error strings (empty = valid)

Run: `cd backend && python -m pytest tests/test_campaigns.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: campaign manager with distribution algorithm, cross-collection dedup, and validation"
```

---

### Task 6: Scheduler Module

**Files:**
- Create: `backend/app/scheduler.py`
- Test: `backend/tests/test_scheduler.py`

- [ ] **Step 1: Write scheduler tests**

Write `backend/tests/test_scheduler.py`:

```python
import pytest
from datetime import date
from app.scheduler import generate_schedule


def test_generates_correct_number_of_slots():
    slots = generate_schedule(
        total_reviews=10, reviews_per_day=5,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    assert len(slots) == 10


def test_all_slots_within_active_hours():
    slots = generate_schedule(
        total_reviews=20, reviews_per_day=5,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    for slot in slots:
        assert 9 <= slot.hour < 23


def test_minimum_gap_between_slots():
    slots = generate_schedule(
        total_reviews=10, reviews_per_day=10,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    sorted_slots = sorted(slots)
    for i in range(1, len(sorted_slots)):
        gap = (sorted_slots[i] - sorted_slots[i-1]).total_seconds()
        assert gap >= 120  # 2 minute minimum


def test_duration_mode():
    slots = generate_schedule(
        total_reviews=30, duration_days=10,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    assert len(slots) == 30
    days = {s.date() for s in slots}
    assert len(days) == 10


def test_randomized_times():
    s1 = generate_schedule(
        total_reviews=10, reviews_per_day=5,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    s2 = generate_schedule(
        total_reviews=10, reviews_per_day=5,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1)
    )
    assert s1 != s2


def test_cross_campaign_gap_enforcement():
    """When existing_timestamps are provided, new slots must respect 2-min gap."""
    from datetime import datetime
    import pytz
    tz = pytz.timezone("Asia/Karachi")
    existing = [tz.localize(datetime(2026, 5, 1, 10, 0, 0))]

    slots = generate_schedule(
        total_reviews=1, reviews_per_day=1,
        active_start=9, active_end=23,
        timezone="Asia/Karachi", start_date=date(2026, 5, 1),
        existing_timestamps=existing,
    )
    for slot in slots:
        for existing_ts in existing:
            gap = abs((slot - existing_ts).total_seconds())
            assert gap >= 120
```

Run: `cd backend && python -m pytest tests/test_scheduler.py -v`
Expected: FAIL

- [ ] **Step 2: Implement schedule generation**

Write `backend/app/scheduler.py`:
- `generate_schedule(total_reviews, reviews_per_day=None, duration_days=None, active_start, active_end, timezone, start_date, existing_timestamps=None) -> list[datetime]`
  - If `reviews_per_day` given: calculate `duration_days = ceil(total_reviews / reviews_per_day)`
  - If `duration_days` given: calculate `reviews_per_day = ceil(total_reviews / duration_days)`
  - For each day, generate N random timestamps within active hours window
  - Sort all timestamps, merge with `existing_timestamps`, enforce 2-minute minimum gap (shift collisions forward)
  - Return list of timezone-aware datetimes (only the new ones, not existing)
- `init_scheduler(database_url)` - creates APScheduler `BackgroundScheduler` with `SQLAlchemyJobStore`
- `schedule_campaign_jobs(scheduler, campaign_id, review_ids, timestamps, callback)` - creates one `date` trigger job per review
- `remove_campaign_jobs(scheduler, campaign_id)` - removes all jobs for a campaign (jobs use id format `campaign_{id}_review_{review_id}`)

Run: `cd backend && python -m pytest tests/test_scheduler.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: scheduler with randomized time slots, cross-campaign gap enforcement"
```

---

### Task 7: API Routes (Campaigns, Reviews, Stats, Health, Logs)

**Files:**
- Create: `backend/app/routes/campaigns.py`
- Create: `backend/app/routes/reviews.py`
- Create: `backend/app/routes/stats.py`
- Create: `backend/app/routes/health.py`
- Update: `backend/app/routes/__init__.py`
- Update: `backend/app/main.py`
- Test: `backend/tests/test_routes.py`

- [ ] **Step 1: Write route integration tests**

Write `backend/tests/test_routes.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def auth_client():
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    client.cookies = resp.cookies
    yield client
    await client.aclose()


async def test_health_no_auth_required():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "db" in data
    assert "scheduler" in data


async def test_get_store_empty(auth_client):
    resp = await auth_client.get("/api/store")
    assert resp.status_code == 200


async def test_get_stats(auth_client):
    resp = await auth_client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_products" in data
    assert "total_collections" in data
    assert "total_reviews_submitted" in data
    assert "active_campaigns" in data
    assert "success_rate" in data
    assert "reviews_over_time" in data  # time-series data
    assert "reviews_by_collection" in data  # per-collection breakdown
    assert "rating_distribution" in data  # 1-5 star breakdown


async def test_create_campaign_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/campaigns", json={})
    assert resp.status_code == 401


async def test_create_campaign_validation_error(auth_client):
    resp = await auth_client.post("/api/campaigns", json={
        "name": "Test",
        "schedule": {"reviews_per_day": 5, "active_hours": {"start": 9, "end": 23}},
        "reviews": {"nonexistent": [{"name": "A", "email": "a@x.com", "rating": 5, "content": "Great stuff here"}]}
    })
    assert resp.status_code == 400


async def test_get_campaigns_empty(auth_client):
    resp = await auth_client.get("/api/campaigns")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_campaign_patch_only_draft(auth_client):
    """PATCH should only work on draft campaigns."""
    # This test requires a campaign to exist - tested via full lifecycle in smoke test
    # Here we just verify the endpoint exists and rejects invalid IDs
    resp = await auth_client.patch("/api/campaigns/999", json={"name": "New Name"})
    assert resp.status_code == 404


async def test_campaign_start_invalid_id(auth_client):
    resp = await auth_client.post("/api/campaigns/999/start")
    assert resp.status_code == 404


async def test_campaign_delete_invalid_id(auth_client):
    resp = await auth_client.delete("/api/campaigns/999")
    assert resp.status_code == 404


async def test_global_logs_endpoint(auth_client):
    """GET /api/logs should return logs across all campaigns."""
    resp = await auth_client.get("/api/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_global_logs_with_filters(auth_client):
    """GET /api/logs supports campaign_id, status, and date filters."""
    resp = await auth_client.get("/api/logs?status=success")
    assert resp.status_code == 200


async def test_retry_failed_invalid_campaign(auth_client):
    resp = await auth_client.post("/api/campaigns/999/retry-failed")
    assert resp.status_code == 404
```

Run: `cd backend && python -m pytest tests/test_routes.py -v`
Expected: FAIL

- [ ] **Step 2: Implement health route**

Write `backend/app/routes/health.py`:
- `GET /api/health` - returns `{"status": "ok", "db": "connected", "scheduler": "running"|"stopped", "uptime_seconds": N}`
- No auth required

- [ ] **Step 3: Implement stats route with time-series data**

Write `backend/app/routes/stats.py`:
- `GET /api/stats` - returns:
  - Scalar counts: `total_products`, `total_collections`, `total_reviews_submitted`, `total_reviews_failed`, `active_campaigns`, `success_rate` (float 0-100)
  - `reviews_over_time`: list of `{"date": "2026-04-15", "count": 5, "success": 4, "failed": 1}` for the last 30 days (query submission_log grouped by date)
  - `reviews_by_collection`: list of `{"collection": "power-banks", "count": 25}` (join reviews -> products -> collection_product -> collections)
  - `rating_distribution`: list of `{"rating": 5, "count": 30}` for ratings 1-5
  - `upcoming_reviews`: next 5 scheduled reviews with product title and scheduled_at
  - `recent_submissions`: last 10 submission log entries with reviewer name, product title, status

- [ ] **Step 4: Implement campaign routes**

Write `backend/app/routes/campaigns.py`:
- `GET /api/campaigns` - list all campaigns with computed progress (submitted/total)
- `POST /api/campaigns` - validate input (max 5MB checked via Content-Length header), resolve collections/products from DB cache, call `distribute_reviews_by_collection`, save as draft with `total_reviews` count
- `GET /api/campaigns/{id}` - campaign detail with review assignment summary
- `PATCH /api/campaigns/{id}` - update name/schedule. Return 400 if status != "draft".
- `DELETE /api/campaigns/{id}` - set status to "cancelled", call `remove_campaign_jobs`, keep records
- `POST /api/campaigns/{id}/start` - validate status is "draft", generate schedule (pass existing scheduled timestamps for gap enforcement), create APScheduler jobs, set status to "active"
- `POST /api/campaigns/{id}/pause` - validate status is "active", remove scheduler jobs, set status to "paused"
- `POST /api/campaigns/{id}/resume` - validate status is "paused", re-generate schedule for pending reviews, set status to "active"

- [ ] **Step 5: Implement reviews/logs routes (per-campaign + global)**

Write `backend/app/routes/reviews.py`:
- `GET /api/campaigns/{id}/reviews` - list reviews with status, assigned product title, scheduled_at
- `GET /api/campaigns/{id}/logs` - list submission_log entries for the campaign's reviews
- `GET /api/logs` - **global logs endpoint** across all campaigns. Query params: `campaign_id` (optional), `status` (optional: "success"/"failed"), `date_from` (optional), `date_to` (optional). Returns list of log entries with reviewer name, product title, campaign name.
- `POST /api/campaigns/{id}/retry-failed` - find all failed reviews in campaign, reset status to pending, re-schedule

- [ ] **Step 6: Wire up all routers and submission job**

Update `backend/app/routes/__init__.py` to aggregate all routers.
Update `backend/app/main.py`:
- Include the combined router
- Initialize APScheduler in lifespan (start on startup, shutdown on teardown)
- Register the submission job callback function:

```python
async def execute_review_submission(review_id: int):
    """Called by APScheduler for each scheduled review."""
    async with async_session_factory() as session:
        review = await session.get(Review, review_id)
        if not review or review.status == "submitted":
            return
        campaign = await session.get(Campaign, review.campaign_id)
        store = await session.get(Store, campaign.store_id)
        product = await session.get(Product, review.product_id)

        submitter = TrustooSubmitter(domain=store.domain, max_requests_per_hour=settings.MAX_REQUESTS_PER_HOUR)

        if submitter.circuit_open:
            campaign.status = "paused"
            await session.commit()
            return

        if not submitter.can_submit():
            # Reschedule for later
            return

        result = await submitter.submit(
            content=review.content, author=review.name, author_email=review.email,
            rating=review.rating, product_id=product.shopify_product_id, shop_id=store.shop_id
        )

        # Create submission log
        log = SubmissionLog(
            review_id=review.id, http_status=result.http_status,
            response_body=result.response_body, trustoo_review_id=result.trustoo_review_id,
            discount_code=result.discount_code, discount_value=result.discount_value,
            success=result.success, error_message=result.error_message
        )
        session.add(log)

        if result.success:
            review.status = "submitted"
            review.submitted_at = datetime.now(tz)
        elif result.should_retry and review.retry_count < 3:
            review.retry_count += 1
            review.error_message = result.error_message
            # Will be retried via retry-failed endpoint
        else:
            review.status = "failed"
            review.error_message = result.error_message

        await session.commit()

        # Check if campaign is complete
        pending = await session.execute(
            select(func.count()).where(Review.campaign_id == campaign.id, Review.status.in_(["pending", "scheduled"]))
        )
        if pending.scalar() == 0:
            campaign.status = "completed"
            campaign.completed_at = datetime.now(tz)
            await session.commit()
```

- [ ] **Step 7: Run full test suite**

Run: `cd backend && python -m pytest -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: complete API routes with global logs, time-series stats, campaign lifecycle"
```

---

## Phase 2: Frontend

### Task 8: Frontend Scaffolding

**Files:**
- Create: `frontend/` via Vite scaffold
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/lib/utils.ts`
- Modify: `frontend/vite.config.ts` (add proxy)

- [ ] **Step 1: Scaffold Vite + React + TypeScript project**

```bash
cd D:/Projects/shopify-reviewer
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install tailwindcss @tailwindcss/vite
npm install react-router-dom recharts lucide-react
npm install clsx tailwind-merge class-variance-authority
```

- [ ] **Step 3: Initialize shadcn/ui**

```bash
cd frontend
npx shadcn@latest init
```

Select: TypeScript, default style, slate base color, CSS variables.

Install needed components:

```bash
npx shadcn@latest add button card table input label dialog dropdown-menu toast badge progress separator tabs select
```

- [ ] **Step 4: Configure Vite proxy for backend**

Update `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite"
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: Create API client**

Write `frontend/src/api/client.ts`:

```typescript
const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
```

- [ ] **Step 6: Create auth hook**

Write `frontend/src/hooks/use-auth.ts`:
- `useAuth()` hook with `login(username, password)`, `logout()`, `user`, `isAuthenticated`
- Uses React context, checks `/api/auth/me` on mount

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: frontend scaffolding with Vite, Tailwind, shadcn/ui, API client"
```

---

### Task 9: Layout + Login + Routing

**Files:**
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/app-layout.tsx`
- Create: `frontend/src/pages/login.tsx`
- Update: `frontend/src/App.tsx`

- [ ] **Step 1: Build sidebar component**

Write `frontend/src/components/layout/sidebar.tsx`:
- Fixed left sidebar, 200px width, dark background (`bg-zinc-950`)
- Logo/brand "ReviewBot" at top
- Nav items: Dashboard, Store, Campaigns, New Campaign, Logs, Settings
- Use `lucide-react` icons: LayoutDashboard, Store, Megaphone, PlusCircle, ScrollText, Settings
- Active item highlighted with green accent (`text-emerald-400`)
- Use `NavLink` from react-router-dom for active state

Write `frontend/src/components/layout/app-layout.tsx`:
- Flex container: Sidebar + main content area
- Main area has padding, overflow-y scroll, dark background (`bg-zinc-900`)

- [ ] **Step 2: Build login page**

Write `frontend/src/pages/login.tsx`:
- Centered card on dark background
- Username + password inputs (shadcn Input)
- Login button (shadcn Button)
- Error message display
- Calls `api.post('/auth/login', {username, password})`
- On success, redirects to `/`

- [ ] **Step 3: Set up routing in App.tsx**

Write `frontend/src/App.tsx`:
- React Router with routes:
  - `/login` -> Login page (no layout)
  - `/` -> Dashboard (with AppLayout)
  - `/store` -> Store page
  - `/campaigns` -> Campaigns list
  - `/campaigns/:id` -> Campaign detail
  - `/campaigns/new` -> New Campaign
  - `/logs` -> Logs
  - `/settings` -> Settings
- Protected route wrapper that redirects to `/login` if not authenticated

- [ ] **Step 4: Verify UI renders**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173`, verify login page shows, sidebar renders after login.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: app layout with sidebar navigation, login page, and routing"
```

---

### Task 10: Dashboard Page

**Files:**
- Create: `frontend/src/components/stat-card.tsx`
- Create: `frontend/src/pages/dashboard.tsx`

- [ ] **Step 1: Build stat card component**

Write `frontend/src/components/stat-card.tsx`:
- Reusable card showing: label, value, optional icon, optional trend indicator
- Dark card style (`bg-zinc-800/50 border-zinc-700`)
- Large bold number, small uppercase label
- Use shadcn Card as base
- Use 21st.dev Magic components via MCP tool `mcp__magic__21st_magic_component_builder` if available for polished stat cards

- [ ] **Step 2: Build dashboard page**

Write `frontend/src/pages/dashboard.tsx`:
- Fetches `/api/stats` on mount
- **Stat cards row:** Total Products, Total Collections, Reviews Submitted (green), Active Campaigns (blue), Success Rate (%)
- **Charts section (2x2 grid):**
  - Reviews over time: Recharts AreaChart using `stats.reviews_over_time` data, with 7/30 day toggle
  - Success vs failure: Recharts PieChart (donut) using submitted vs failed counts
  - Reviews by collection: Recharts BarChart using `stats.reviews_by_collection` data
  - Rating distribution: Recharts BarChart using `stats.rating_distribution` data
- **Recent submissions:** Table from `stats.recent_submissions` with status badge (green=success, red=failed)
- **Upcoming schedule:** List from `stats.upcoming_reviews` with product name and countdown

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: dashboard page with stats, charts, and activity feed"
```

---

### Task 11: Store + Campaigns Pages

**Files:**
- Create: `frontend/src/components/status-badge.tsx`
- Create: `frontend/src/pages/store.tsx`
- Create: `frontend/src/pages/campaigns.tsx`
- Create: `frontend/src/pages/campaign-detail.tsx`

- [ ] **Step 1: Build status badge component**

Write `frontend/src/components/status-badge.tsx`:
- Maps status strings to colored badges: draft=gray, active=green, paused=yellow, completed=blue, cancelled=red, submitted=green, failed=red, pending=gray, scheduled=blue

- [ ] **Step 2: Build store page**

Write `frontend/src/pages/store.tsx`:
- Fetches `/api/store` and `/api/collections` on mount
- **Store info card:** domain, name, currency, shop_id
- **Sync button:** Calls `POST /api/store/sync`, shows loading spinner, displays "Last synced: {time}". On error shows warning banner with error message.
- **Collections table:** handle, title, products_count, expandable rows
- On expand, fetches `/api/collections/{handle}/products` and shows product list with image thumbnails

- [ ] **Step 3: Build campaigns list page**

Write `frontend/src/pages/campaigns.tsx`:
- Fetches `/api/campaigns` on mount
- Table: name, status badge, progress bar (submitted/total), created date, action buttons
- Action buttons: View (link to detail), Start/Pause (depending on status), Delete
- "New Campaign" button linking to `/campaigns/new`

- [ ] **Step 4: Build campaign detail page**

Write `frontend/src/pages/campaign-detail.tsx`:
- Fetches `/api/campaigns/{id}` on mount
- **Header:** Campaign name, status badge, action buttons (Start/Pause/Resume/Delete with state-appropriate visibility)
- **Progress section:** Progress bar, X of Y submitted, X failed, X pending
- **Reviews table:** Reviewer name, assigned product, rating (stars), status badge, scheduled time, submitted time
- **Logs section:** Fetches `/api/campaigns/{id}/logs`, shows submission attempts with HTTP status, Trustoo review ID, discount code, timestamp
- **"Retry Failed" button** at top of logs section, calls `POST /api/campaigns/{id}/retry-failed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: store, campaigns list, and campaign detail pages"
```

---

### Task 12: New Campaign + Logs + Settings Pages

**Files:**
- Create: `frontend/src/components/json-upload.tsx`
- Create: `frontend/src/pages/new-campaign.tsx`
- Create: `frontend/src/pages/logs.tsx`
- Create: `frontend/src/pages/settings.tsx`

- [ ] **Step 1: Build JSON upload component**

Write `frontend/src/components/json-upload.tsx`:
- Drag-and-drop zone + file picker button
- Accepts `.json` files only, max 5MB (reject larger files client-side)
- On upload: parses JSON, validates structure client-side (required fields, rating range, content length)
- Shows preview: collection names with review counts
- Highlights unknown collection handles in red (compares against collections fetched from `/api/collections`)
- Returns parsed data to parent component

- [ ] **Step 2: Build new campaign page**

Write `frontend/src/pages/new-campaign.tsx`:
- **Campaign name input**
- **JSON upload component** (from step 1)
- **Schedule config section:**
  - Toggle: "Reviews per day" / "Spread over N days"
  - Number input for the selected mode
  - Active hours: two select dropdowns (start hour 0-23, end hour 0-23), defaults 9-23
- **Preview panel:** After JSON parsed, shows which reviews will map to which collections, total review count per collection
- **Validation errors** displayed inline (from client-side + server 400 response)
- **Two buttons:** "Create Draft" (`POST /api/campaigns`) and "Create & Start" (POST then POST `/campaigns/{id}/start`)
- On success, redirect to `/campaigns/{id}`

- [ ] **Step 3: Build logs page**

Write `frontend/src/pages/logs.tsx`:
- Fetches `GET /api/logs` on mount (global logs endpoint)
- **Filters row:** Campaign dropdown (from `/api/campaigns`), Status dropdown (success/failed/all), Date range inputs
- Filters update query params: `GET /api/logs?campaign_id=X&status=success&date_from=...&date_to=...`
- **Table:** Timestamp, reviewer name, product name, campaign name, HTTP status, Trustoo review ID, discount code, status badge
- **Export CSV button:** Client-side CSV generation from loaded table data, triggers file download

- [ ] **Step 4: Build settings page**

Write `frontend/src/pages/settings.tsx`:
- **Store config card:** Domain (read-only), Shop ID (read-only)
- **Rate limits card:** MAX_REQUESTS_PER_HOUR, MIN_SUBMISSION_GAP_SECONDS (read-only, from `/api/health`)
- **Scheduler card:** Status (running/stopped indicator), next scheduled job time, total pending jobs
- **Active campaigns count**
- **"Pause All Campaigns" button:** Shows confirmation dialog (shadcn Dialog), on confirm calls `POST /api/campaigns/{id}/pause` for each active campaign

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: new campaign, logs, and settings pages"
```

---

## Phase 3: Integration & Deployment

### Task 13: Docker + Deployment Config

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create Dockerfile**

Write `Dockerfile` (multi-stage):

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim
WORKDIR /app

# Install dependencies first (cache layer)
COPY backend/pyproject.toml ./
COPY backend/app/__init__.py ./app/__init__.py
RUN pip install --no-cache-dir .

# Copy application source
COPY backend/app ./app
COPY --from=frontend-build /app/frontend/dist ./static

# Create data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Note: We copy `__init__.py` before `pip install` so the package has a minimal source tree for the install step. Then copy the full `app/` directory after, which overwrites `__init__.py` (same content) and adds all other modules.

- [ ] **Step 2: Create docker-compose.yml**

Write `docker-compose.yml`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - app-data:/app/data
    env_file:
      - .env
    restart: always

volumes:
  app-data:
```

- [ ] **Step 3: Create .env.example and .gitignore**

Write `.env.example`:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
SECRET_KEY=generate-a-random-secret-here
STORE_DOMAIN=spharetech.com
TIMEZONE=Asia/Karachi
MAX_REQUESTS_PER_HOUR=10
MIN_SUBMISSION_GAP_SECONDS=120
DATABASE_URL=sqlite+aiosqlite:///data/reviewer.db
```

Write `.gitignore`:

```
__pycache__/
*.pyc
.env
data/
node_modules/
frontend/dist/
.venv/
*.egg-info/
.ruff_cache/
.pytest_cache/
.superpowers/
```

- [ ] **Step 4: Update FastAPI to serve static files**

Update `backend/app/main.py`:
- Mount `StaticFiles` at `/static` for the frontend dist folder (if the directory exists)
- Add catch-all route that serves `index.html` for client-side SPA routing:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# After all API routes are included:
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(static_dir, "index.html"))
```

- [ ] **Step 5: Test Docker build**

```bash
cd D:/Projects/shopify-reviewer
docker build -t shopify-reviewer .
docker-compose up -d
```

Verify `http://localhost:8000` serves the app.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: Docker deployment with multi-stage build"
```

---

### Task 14: End-to-End Smoke Test

**Files:**
- No new files, manual verification

- [ ] **Step 1: Start the full stack locally**

```bash
cd D:/Projects/shopify-reviewer
# Terminal 1: Backend
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload
# Terminal 2: Frontend
cd frontend && npm run dev
```

- [ ] **Step 2: Verify auth flow**

- Open `http://localhost:5173`
- Should redirect to login
- Login with admin credentials from .env
- Should see dashboard with empty stats (all zeros)

- [ ] **Step 3: Verify store sync**

- Navigate to Store page
- Click "Sync Now"
- Should populate with spharetech.com data: collections, products, shop_id
- Verify collections are expandable and show products

- [ ] **Step 4: Verify campaign creation**

- Navigate to New Campaign
- Upload a test JSON file:

```json
{
  "power-banks": [
    {"name": "Test User 1", "email": "test1@example.com", "rating": 5, "content": "Excellent power bank, charges my phone super fast and the battery lasts for days."},
    {"name": "Test User 2", "email": "test2@example.com", "rating": 4, "content": "Good quality product, fast charging works well with my Samsung phone."}
  ]
}
```

- Verify preview shows collection mapping
- Set schedule: 1 review/day, hours 9-23
- Click "Create Draft"
- Verify campaign appears in campaigns list with "draft" status

- [ ] **Step 5: Verify campaign lifecycle**

- Click "Start" on the campaign
- Check campaign detail: reviews should show "scheduled" status with future timestamps
- Check dashboard: should show 1 active campaign, upcoming schedule
- Click "Pause", verify status changes
- Click "Resume", verify re-scheduling
- Click "Delete", verify soft delete to "cancelled"

- [ ] **Step 6: Verify Trustoo submission (optional, submits real review)**

- Create a new test campaign with 1 review, set to start immediately (active hours cover current time)
- Wait for scheduled time or manually trigger
- Check logs page for submission result (should show success with Trustoo review ID and discount code)

- [ ] **Step 7: Run full backend test suite**

```bash
cd backend && python -m pytest -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "chore: end-to-end verification complete"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | Tasks 1-7 | Backend: config, models, auth, store, submitter (with circuit breaker + rate limiter), campaigns (with cross-collection dedup), scheduler (with cross-campaign gaps), all routes (including global logs + time-series stats) |
| 2 | Tasks 8-12 | Frontend: scaffold, layout, dashboard (charts), store, campaigns, new campaign (JSON upload), logs (global + filters), settings |
| 3 | Tasks 13-14 | Docker deployment + end-to-end smoke test |

**Total: 14 tasks, ~50 commits**

**Critical path:** Tasks 1-7 are sequential (each builds on prior). Tasks 8-12 can partially parallelize once Task 7 is done (backend API is complete). Tasks 13-14 require both phases complete.
