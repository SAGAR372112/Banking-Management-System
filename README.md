# Bank Management API

A production-grade REST API for bank account management, built with Django REST Framework.

## Features

- **JWT Authentication** with token refresh and blacklisting
- **Role-based access** (Admin / Customer)
- **Atomic transactions** with `select_for_update()` for concurrency safety
- **Full CRUD** for accounts, branches, and users
- **Deposit / Withdrawal / Transfer** with daily limit enforcement
- **OpenAPI 3 docs** via drf-spectacular (Swagger UI at `/api/docs/`)
- **Structured logging** with loguru + correlation IDs
- **Custom exception handler** for consistent error responses
- **80%+ test coverage** target with pytest + factory-boy
- **One-command deploy** to Railway / Heroku

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo>
cd bank_management
cp .env.example .env
# Edit .env with your values
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up the database

```bash
# PostgreSQL (recommended)
createdb bank_management

# Apply migrations
python manage.py migrate

# Create a superuser (admin)
python manage.py createsuperuser
```

### 4. Run the development server

```bash
DJANGO_SETTINGS_MODULE=bank_management.settings.development python manage.py runserver
```

API is now available at `http://localhost:8000/api/`

### 5. Run tests

```bash
pytest
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required in prod)* |
| `DEBUG` | Debug mode | `True` |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (dev only) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token TTL | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token TTL | `7` |
| `DAILY_TRANSFER_LIMIT` | Max daily outgoing per account | `50000` |

---

## API Reference

### Authentication

```
POST /api/users/token/          # Obtain JWT tokens
POST /api/users/token/refresh/  # Refresh access token
POST /api/users/token/blacklist/ # Logout (blacklist refresh token)
```

All protected endpoints require: `Authorization: Bearer <access_token>`

### Users

```
POST /api/users/register/       # Register new customer
GET  /api/users/profile/        # Get own profile
PUT  /api/users/profile/        # Update own profile (partial)
```

### Accounts

```
GET  /api/accounts/             # List accounts (own, or all for admins)
POST /api/accounts/             # Create new account
GET  /api/accounts/{id}/        # Get account details
PUT  /api/accounts/{id}/        # Update account
DEL  /api/accounts/{id}/        # Soft-delete account (admins, zero balance only)
```

**Filtering:** `?account_type=savings&status=active&min_balance=100`

### Transactions

```
POST /api/accounts/{id}/deposit/      # Deposit funds
POST /api/accounts/{id}/withdraw/     # Withdraw funds
POST /api/transfer/                   # Transfer between accounts
GET  /api/accounts/{id}/transactions/ # List account transactions
```

**Pagination:** `?limit=20&offset=0`

### Branches

```
GET /api/branches/              # List all branches
```

### Admin

```
GET /api/admin/dashboard/stats/ # Aggregate statistics (admin only)
```

### Health

```
GET /health/                    # Returns {"status": "healthy"}
```

### Documentation

```
GET /api/docs/   # Swagger UI
GET /api/redoc/  # ReDoc
GET /api/schema/ # OpenAPI 3 JSON schema
```

---

## Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Insufficient balance. Available: 10.00, Requested: 500.00.",
    "details": {}
  }
}
```

---

## Deploy to Railway

```bash
railway login
railway init
railway add postgresql
railway variables set SECRET_KEY=your-key DEBUG=False DJANGO_SETTINGS_MODULE=bank_management.settings.production
railway up
railway run python manage.py migrate
```

## Deploy to Heroku

```bash
heroku create bank-management-api
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY=your-key DEBUG=False DJANGO_SETTINGS_MODULE=bank_management.settings.production
git push heroku main
heroku run python manage.py migrate
```

Add a `Procfile`:
```
web: gunicorn bank_management.wsgi --log-file -
```

---

## Project Structure

```
bank_management/
├── manage.py
├── requirements.txt
├── .env.example
├── pytest.ini
├── conftest.py              # factory-boy factories
├── bank_management/
│   ├── settings/
│   │   ├── base.py         # shared settings
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── middleware.py        # correlation IDs + request logging
│   └── exceptions.py       # custom exception handler
├── users/                  # custom User model + auth
├── accounts/               # BankAccount CRUD + permissions
├── transactions/           # deposit/withdraw/transfer services
└── branches/               # Branch directory
```

---

## Security Notes

- Passwords are validated against Django's built-in validators (min length, common password list, etc.)
- JWT tokens are blacklisted on logout
- Transfers use `select_for_update()` with ordered lock acquisition to prevent deadlocks
- Content Security Policy headers via `django-csp`
- SQL injection: prevented by ORM parameterized queries
- All balance math uses `Decimal`, never `float`
