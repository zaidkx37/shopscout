# Shopify Review Automation Tool - Design Specification

## Overview

An internal tool for automating product review submissions on a Shopify store (spharetech.com) via the Trustoo review app. Provides a dashboard for managing review campaigns, scheduling submissions with anti-detection measures, and monitoring results.

**Scope:** Single-tenant, single-store, single-admin internal tool. Designed with clean module boundaries so it can be extended to multi-tenant SaaS later without a rewrite.

## Architecture

**Pattern:** Simple monolith - one Python process, one Docker container.

**Stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLite, APScheduler |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| UI Components | shadcn/ui, 21st.dev (Magic UI), Recharts |
| HTTP Client | httpx (async) |
| Store Data | shopscout (pip package) |
| Deployment | Docker container on VPS |

**Component diagram:**

```
React Dashboard (Vite SPA)
        |
        v
FastAPI (REST API + static file serving)
    |           |
    v           v
SQLite      APScheduler (jobs persisted in SQLite)
                |
                v
        TrustooSubmitter (httpx POST)
                |
                v
        Shopify Store (Trustoo API)
```

## Modules

### 1. Auth Module

Simple password gate. Single admin user.

- Credentials stored in environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD`)
- Session-based authentication using signed cookies (itsdangerous/JWT-style). No server-side session storage needed. Session survives server restarts since the signature is verified against `SECRET_KEY` env var.
- No registration, no password reset, no multi-user
- All API endpoints (except `/api/auth/login` and `/api/health`) require valid session

### 2. Store Resolver Module

Fetches and caches store metadata using the `shopscout` pip package.

```python
from shopscout import Shopify

shop = Shopify('spharetech.com')
store = shop.store()          # name, currency, domain
collections = shop.collections()  # all collections
products = shop.collection_products('power-banks')  # products per collection
```

- `shop_id` is scraped from a product page's `<script data-page-type="product">` tag using a dedicated helper function (not provided by ShopScout). Scraped once on first sync and cached in the `store` table.
- Collections and products are fetched via ShopScout and cached in DB
- Cache is refreshed on demand (manual sync button in dashboard)
- `fetched_at` timestamp displayed in UI ("Last synced 2 hours ago")

**Error handling:** If ShopScout fails during sync (network error, store unavailable, Shopify rate limit), the API returns the error to the UI. The dashboard continues to display stale cached data with a warning banner ("Sync failed at {time}: {error}. Showing cached data from {fetched_at}."). Cached data is never deleted on a failed sync.

### 3. Campaign Manager Module

The central orchestration unit. A campaign represents one JSON upload with a schedule.

**Campaign lifecycle:** `draft` -> `active` -> `completed` (or `paused` at any point)

**State transition rules:**
- `draft` -> `active`: via `/start` endpoint. Creates scheduler jobs.
- `active` -> `paused`: via `/pause`. Removes scheduled jobs, keeps review assignments.
- `paused` -> `active`: via `/resume`. Re-schedules remaining pending reviews.
- `active` -> `completed`: automatic when all reviews are submitted or failed.
- `PATCH` updates (rename, schedule change) are only allowed on `draft` campaigns. Active campaigns must be paused first, then the schedule is recalculated on resume.

**Creation flow:**

1. Admin uploads JSON file with reviews grouped by collection handle
2. System validates collection handles exist in store
3. System fetches products per collection via ShopScout (using cached data)
4. System distributes reviews randomly across products (uniqueness enforced)
5. System warns if a review pool is too small for the number of products
6. Admin configures schedule (reviews per day OR total duration + active hours window)
7. Campaign saved as `draft`
8. On start, APScheduler jobs are created with randomized timestamps

**Uniqueness constraint:** Each review is assigned to exactly one product. No review content is ever duplicated across the store. Enforced by a unique index on `content_hash` in the `review` table. The `content_hash` is `SHA-256(content + "|" + author_email)` to allow different reviewers to write similar short content without collision.

**Distribution algorithm:**

1. For each collection key in the JSON, fetch the product list
2. If a product appears in multiple collections in the same upload, it is only eligible in the first collection encountered (prevents double-targeting)
3. Shuffle both the review pool and product list
4. Deal reviews to products round-robin (review 1 -> product 1, review 2 -> product 2, ...)
5. Once a review is dealt, it is consumed and cannot be reused
6. If pool size < product count, some products get zero reviews (warning shown to admin)
7. If pool size > product count, products get multiple unique reviews

**Delete behavior:** `DELETE /api/campaigns/{id}` sets status to `cancelled`, removes all APScheduler jobs, but retains the campaign and review records in the database for audit purposes. A future "purge old campaigns" feature may hard-delete records older than a configurable threshold.

### 4. Scheduler Module

APScheduler with SQLite job store for persistence across restarts.

**Timezone:** All scheduled times use the timezone configured in `TIMEZONE` env var (default: `Asia/Karachi`). The store's local timezone ensures reviews appear during plausible local hours.

**Schedule generation:**

Given a campaign config like `reviews_per_day: 5, active_hours: 9-23, duration: 10 days`:

1. Calculate total reviews to schedule
2. For each day in the duration, pick N random timestamps within the active hours window
3. Enforce minimum 2-minute gap between any two submissions (across all campaigns)
4. Add 1-5 second random jitter before each actual submission
5. Create one APScheduler `date` trigger job per review

**Example output:**

```
Day 1: 09:23, 11:47, 14:02, 17:35, 21:18
Day 2: 10:11, 12:55, 15:40, 18:22, 22:03
```

**Schedule modes (admin picks one):**

- `reviews_per_day` + `active_hours` - system calculates duration from total reviews
- `duration_days` + `active_hours` - system calculates reviews per day from total reviews

**Note:** Active hours are whole hours only (e.g. 9 means 9:00, 23 means 23:00). Fractional hours are not supported.

### 5. Trustoo Submitter Module

Pure HTTP submission to the Trustoo review API.

**Endpoint:** `POST https://{domain}/apps/trustoo/api/v1/reviews/add_review_via_shopify`

**Payload:**

```json
{
  "content": "Review text here",
  "author": "Reviewer Name",
  "author_email": "reviewer@email.com",
  "resources": [],
  "product_id": 9309304946934,
  "shop_id": 79801712886,
  "rating": 5
}
```

**Confirmed:** No cookies, no auth tokens, no `author_country` field required. Content-Type: `text/plain;charset=UTF-8`.

**Note on `resources` field:** This is Trustoo's field for image/media attachments. We send it as an empty array. Supporting media uploads is a potential future enhancement but not in scope.

**Response on success (HTTP 200):**

```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "review_id": "25989551",
    "discount_code": "TT-1O8ONDAU",
    "discount_value": "5%",
    "resource_type": 1,
    "is_skip_media_upload": 0
  }
}
```

**Pluggable interface for future review apps:**

```python
class BaseSubmitter(ABC):
    @abstractmethod
    async def submit(self, review: Review, product: Product, store: Store) -> SubmissionResult: ...

    @abstractmethod
    async def health_check(self, domain: str) -> bool: ...

class TrustooSubmitter(BaseSubmitter): ...
# Future: class JudgeMeSubmitter(BaseSubmitter): ...
```

**Safety layers:**

| Layer | Behavior |
|-------|----------|
| Rate limiting | Max N requests per hour (configurable, default 10) |
| Random delays | 1-5 second random sleep before each POST |
| Minimum gap | No two submissions within 2 minutes of each other |
| User-Agent rotation | Pool of 5-10 realistic browser user-agent strings |
| Retry with backoff | HTTP 429/500/timeout: retry up to 3 times (30s, 60s, 120s backoff) |
| No retry on 4xx | Bad request = mark as failed, do not retry |
| Circuit breaker | 5 consecutive failures = pause campaign, show alert on dashboard |

**IP fingerprinting note:** All submissions originate from a single VPS IP. This is an accepted risk for v1. If Trustoo ever correlates submissions by source IP, a proxy rotation layer can be added to the submitter without changing the rest of the system.

### 6. Logging Module

Immutable append-only submission log for auditing.

Each submission attempt is recorded with:
- HTTP status code
- Response body
- Trustoo review ID (on success)
- Discount code and value (on success)
- Timestamp
- Success/failure flag
- Error message (on failure)

One review can have multiple log entries (retries).

## Database Schema

### Tables

**store**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| domain | TEXT UNIQUE | e.g. "spharetech.com" |
| shop_id | INTEGER | Scraped from product page |
| name | TEXT | Store display name |
| currency | TEXT | e.g. "PKR" |
| fetched_at | DATETIME | Last sync timestamp |

**collection**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| store_id | INTEGER FK | References store.id |
| handle | TEXT | e.g. "power-banks" |
| title | TEXT | Display name |
| products_count | INTEGER | Count from ShopScout |
| fetched_at | DATETIME | Last sync timestamp |

**Unique index:** `(store_id, handle)`

**collection_product** (join table - products can belong to multiple collections)

| Column | Type | Notes |
|--------|------|-------|
| collection_id | INTEGER FK | References collection.id |
| product_id | INTEGER FK | References product.id |

**Primary key:** `(collection_id, product_id)`

**product**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| store_id | INTEGER FK | References store.id |
| shopify_product_id | INTEGER UNIQUE | Shopify's numeric product ID |
| handle | TEXT | URL slug |
| title | TEXT | Product display name |
| image_url | TEXT | Primary image URL (nullable) |
| fetched_at | DATETIME | Last sync timestamp |

**campaign**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| store_id | INTEGER FK | References store.id (for future multi-store) |
| name | TEXT | Admin-provided campaign name |
| status | TEXT | draft / active / paused / completed / cancelled |
| reviews_per_day | INTEGER | Nullable (if duration_days is set) |
| duration_days | INTEGER | Nullable (if reviews_per_day is set) |
| active_hours_start | INTEGER | Default 9 (whole hours only) |
| active_hours_end | INTEGER | Default 23 (whole hours only) |
| total_reviews | INTEGER | Denormalized count for quick progress display |
| created_at | DATETIME | |
| started_at | DATETIME | Nullable |
| completed_at | DATETIME | Nullable |

**review**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| campaign_id | INTEGER FK | References campaign.id |
| product_id | INTEGER FK | References product.id (nullable until assigned) |
| name | TEXT | Reviewer display name |
| email | TEXT | Reviewer email |
| rating | INTEGER | 1-5 (validated on input) |
| content | TEXT | Review text (must be non-empty, non-whitespace) |
| content_hash | TEXT | SHA-256 of (content + "|" + email) |
| status | TEXT | pending / scheduled / submitted / failed |
| scheduled_at | DATETIME | When the review is scheduled to be submitted |
| submitted_at | DATETIME | When actually submitted (nullable) |
| error_message | TEXT | Last error (nullable) |
| retry_count | INTEGER | Default 0 |

**Unique index:** `content_hash` (enforces no duplicate content+email combos across the entire store)

**submission_log**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| review_id | INTEGER FK | References review.id |
| http_status | INTEGER | Response status code |
| response_body | TEXT | Raw response |
| trustoo_review_id | TEXT | From response data (nullable) |
| discount_code | TEXT | From response data (nullable) |
| discount_value | TEXT | e.g. "5%" (nullable) |
| success | BOOLEAN | |
| error_message | TEXT | Nullable |
| attempted_at | DATETIME | |

## API Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Username + password, returns session cookie |
| POST | `/api/auth/logout` | Clears session |
| GET | `/api/auth/me` | Check if session is valid |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (no auth required). Returns DB status, scheduler status, uptime. |

### Store & Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/store` | Get cached store info |
| POST | `/api/store/sync` | Re-fetch store + collections + products from ShopScout |
| GET | `/api/collections` | List all collections with product counts |
| GET | `/api/collections/{handle}/products` | List products in a collection |
| GET | `/api/stats` | Dashboard stats aggregate |

### Campaigns

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns` | List all campaigns with status + progress |
| POST | `/api/campaigns` | Create campaign (JSON upload + schedule config) |
| GET | `/api/campaigns/{id}` | Campaign detail with assigned reviews and progress |
| PATCH | `/api/campaigns/{id}` | Update schedule config or rename (draft only) |
| DELETE | `/api/campaigns/{id}` | Cancel campaign, unschedule pending reviews (soft delete) |
| POST | `/api/campaigns/{id}/start` | Activate campaign, create scheduler jobs |
| POST | `/api/campaigns/{id}/pause` | Pause campaign, remove scheduled jobs |
| POST | `/api/campaigns/{id}/resume` | Resume campaign, re-schedule remaining reviews |

### Reviews & Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns/{id}/reviews` | List reviews with status, product, scheduled time |
| GET | `/api/campaigns/{id}/logs` | Submission logs (success/failure/retry history) |
| POST | `/api/campaigns/{id}/retry-failed` | Re-schedule all failed reviews |

### Campaign Creation Payload

```json
{
  "name": "May Power Banks + Headsets",
  "schedule": {
    "reviews_per_day": 5,
    "active_hours": {"start": 9, "end": 23}
  },
  "reviews": {
    "power-banks": [
      {"name": "Ali Khan", "email": "ali@mail.com", "rating": 5, "content": "Charges super fast..."},
      {"name": "Sara Ahmed", "email": "sara@mail.com", "rating": 4, "content": "Great battery life..."}
    ],
    "headsets": [
      {"name": "Ahmed Raza", "email": "ahmed@mail.com", "rating": 5, "content": "Crystal clear audio..."}
    ]
  }
}
```

**Validation rules for JSON upload:**

| Rule | Constraint |
|------|-----------|
| Max file size | 5 MB |
| Max reviews per upload | 1000 |
| Required fields per review | `name`, `email`, `rating`, `content` |
| Rating range | Integer 1-5 |
| Content | Non-empty, non-whitespace, min 10 characters |
| Email | Basic format validation (contains @) |
| Collection keys | Must match existing collection handles in store |
| Empty review arrays | Rejected (collection key with [] is an error) |

## Frontend

### Tech Stack

- React 18+ with Vite and TypeScript
- Tailwind CSS (dark theme, solid colors, clean spacing)
- shadcn/ui (buttons, tables, forms, dialogs, dropdowns, toasts, cards)
- 21st.dev / Magic UI (animated stat cards, polished components)
- Recharts (charts and data visualizations)

### Pages

**1. Dashboard**

- Stat cards: total products, total collections, reviews submitted, active campaigns, success rate
- Charts:
  - Reviews over time (area/line chart, last 7/30 days toggle)
  - Success vs failure rate (donut chart)
  - Reviews by collection (bar chart)
  - Rating distribution (bar chart showing 1-5 star breakdown)
- Recent submissions feed (last 10, with status indicators)
- Upcoming schedule (next 5 scheduled submissions with countdown)

**2. Store**

- Store info card (name, domain, currency, shop_id)
- Collections list with product counts
- Expandable collection rows showing products
- "Sync Now" button with last-synced timestamp
- Total products count

**3. Campaigns**

- Campaign list table (name, status badge, progress bar, created date, actions)
- Click into campaign for detail view:
  - Progress summary (X of Y reviews submitted)
  - Review assignment table (reviewer name, product, status, scheduled time)
  - Per-campaign logs
  - Start / Pause / Resume / Delete actions

**4. New Campaign**

- Campaign name input
- JSON file upload with drag-and-drop
- Preview panel: parsed JSON showing collection -> review count mapping
- Validation: highlights unknown collection handles in red
- Schedule configuration:
  - Toggle between "reviews per day" and "spread over N days"
  - Active hours range selector (default 9-23)
- Review assignment preview: shows which reviews will go to which products
- "Create Draft" and "Create & Start" buttons

**5. Logs**

- Filterable table of all submission logs
- Filters: campaign, status (success/failed), date range
- Columns: timestamp, reviewer name, product, campaign, HTTP status, Trustoo review ID, discount code, status
- Export to CSV: client-side CSV generation from loaded table data (sufficient for expected data volumes)

**6. Settings**

- Store domain configuration (read-only, from env)
- Rate limit display (MAX_REQUESTS_PER_HOUR, MIN_SUBMISSION_GAP_SECONDS)
- Scheduler status (running/stopped, next job time)
- Active campaigns count
- "Pause All Campaigns" emergency button

### Layout

- Sidebar navigation (fixed left, 200px)
- Dark theme default, solid color palette
- Navigation items: Dashboard, Store, Campaigns, New Campaign, Logs, Settings
- Responsive (but primarily desktop-focused for admin tool)

## Deployment

### Docker

Single Dockerfile:

- Python backend (FastAPI + APScheduler) runs via uvicorn
- React frontend built at Docker build time, served as static files by FastAPI
- SQLite database stored in a Docker volume for persistence
- Environment variables for configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_USERNAME` | Login username | (required) |
| `ADMIN_PASSWORD` | Login password | (required) |
| `STORE_DOMAIN` | Shopify store domain | spharetech.com |
| `SECRET_KEY` | Session signing key | (required) |
| `TIMEZONE` | Timezone for scheduling | Asia/Karachi |
| `MAX_REQUESTS_PER_HOUR` | Rate limit for submissions | 10 |
| `MIN_SUBMISSION_GAP_SECONDS` | Minimum gap between submissions | 120 |
| `DATABASE_URL` | SQLite path | sqlite:///data/reviewer.db |

### VPS Deployment

- Any VPS provider (Hetzner CX22 recommended, ~$4/mo)
- Docker + docker-compose
- Nginx reverse proxy with SSL (Let's Encrypt)
- Domain A record pointing to VPS IP

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Trustoo changes/removes the open endpoint | Submissions break completely | Circuit breaker stops campaigns. Submitter is pluggable, can switch to alternative approach. Monitor for failures. |
| Trustoo adds rate limiting or CAPTCHA | Submissions start failing | Configurable rate limits already built in. Playwright-based fallback is a future option. |
| Duplicate content detected by Trustoo | Reviews rejected or flagged | Content hash uniqueness enforced at DB level before submission. |
| Store data goes stale (new products/collections) | Reviews assigned to outdated product list | Manual sync button. `fetched_at` timestamp shown in UI. |
| APScheduler jobs lost on crash | Scheduled reviews not submitted | Jobs persisted in SQLite, restored on restart. Docker restart policy: always. |
| VPS goes down | All submissions stop | Docker restart policy + VPS provider uptime SLA. Health check endpoint for external monitoring. |
| All submissions from single IP | Trustoo could flag the IP | Accepted risk for v1. Proxy rotation layer can be added to submitter later. |

## Future Extensions (designed for, not built now)

- **Multi-store support:** `store_id` FK already on campaign table. Add store selector to UI.
- **Multi-tenant SaaS:** Swap SQLite for PostgreSQL, add user model, add Stripe billing
- **AI review generation:** "Generate draft JSON" button that feeds product data to an LLM
- **Review scraping from Amazon/Daraz/Flipkart:** New scraper modules that output the same JSON format
- **Judge.me / Loox submitters:** Implement `BaseSubmitter` interface for other review apps
- **Team roles:** Admin / Editor / Viewer permission levels
- **Webhook notifications:** Slack/Discord alerts on campaign completion or failures
- **Image/media reviews:** Populate `resources` array in Trustoo payload with image URLs
- **Campaign data purge:** Hard-delete cancelled/completed campaigns older than N days
