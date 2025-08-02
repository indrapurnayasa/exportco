# Hackathon Service API

A FastAPI-based service for hackathon management with user authentication, project management, and team collaboration features.

## Features

- 🔐 JWT-based authentication
- 👥 User management
- 📊 Project management
- 🏆 Team collaboration
- 🗄️ SQLAlchemy ORM with SQLite/PostgreSQL support
- 📝 Pydantic validation
- 🧪 Comprehensive testing with pytest
- 📚 Auto-generated API documentation

## Project Structure

```
hackathon-service/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app instance and configuration
│   ├── api/                      # API routers (organized by feature)
│   │   ├── __init__.py
│   │   └── v1/                   # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py           # Authentication endpoints
│   │       ├── user.py           # User management endpoints
│   │       ├── export_data.py    # Export data endpoints
│   │       ├── export.py         # Export analysis endpoints
│   │       ├── komoditi.py       # Commodity endpoints
│   │       └── prompt_library.py # Prompt library endpoints
│   ├── core/                     # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings and configuration
│   │   └── security.py           # Password hashing, JWT tokens, etc.
│   ├── models/                   # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── export_data.py        # Export data model
│   │   ├── export_document.py    # Export document model
│   │   ├── export_document_country.py
│   │   ├── export_duty_chunks.py
│   │   ├── currency_rates.py     # Currency exchange rates
│   │   ├── komoditi.py           # Commodity model
│   │   └── prompt_library.py     # Prompt library model
│   ├── schemas/                  # Pydantic schemas for request/response
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication schemas
│   │   ├── user.py               # User schemas
│   │   ├── export_data.py        # Export data schemas
│   │   ├── komoditi.py           # Commodity schemas
│   │   └── prompt_library.py     # Prompt library schemas
│   ├── services/                 # Business logic and services
│   │   ├── __init__.py
│   │   ├── user_service.py       # User management service
│   │   ├── export_data_service.py # Export data analysis service
│   │   ├── export_document_service.py
│   │   ├── export_duty_service.py # Export duty calculation service
│   │   ├── komoditi_service.py   # Commodity management service
│   │   ├── prompt_library_service.py # Prompt library service
│   │   ├── chain_of_thought_service.py # AI reasoning service
│   │   └── optimized_chatbot_service.py # AI chatbot service
│   ├── db/                       # Database configuration
│   │   ├── __init__.py
│   │   └── database.py           # Database session and connection
│   ├── middleware/               # Custom middleware
│   │   ├── __init__.py
│   │   └── logging_middleware.py # Request logging middleware
│   └── utils/                    # Helper functions and utilities
│       ├── __init__.py
│       ├── helpers.py            # General helper functions
│       └── logger.py             # Logging utilities
├── alembic/                      # Database migrations
│   ├── env.py                    # Alembic environment configuration
│   ├── script.py.mako            # Migration template
│   └── versions/                 # Migration files
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── test_user.py              # User tests
│   └── test_export.py            # Export tests
├── examples/                     # Example scripts and tests
│   ├── create_test_user.py       # User creation example
│   ├── test_auth_api.py          # Authentication API tests
│   ├── add_currency_rates.py     # Currency data examples
│   └── ...                       # Various other examples
├── logs/                         # Application logs
├── .env.example                  # Environment variables template
├── requirements.txt               # Python dependencies
├── alembic.ini                   # Alembic configuration
├── deploy.sh                     # Deployment script
├── deploy.config                  # Deployment configuration
├── update.sh                     # Update script
├── DEPLOYMENT.md                 # Deployment documentation
├── README.md                     # This file
└── vercel.json                   # Vercel deployment config
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd hackathon-service
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual values:

```env
# API Configuration
PROJECT_NAME=Hackathon Service API
VERSION=1.0.0
DESCRIPTION=A FastAPI service for export data analysis
API_V1_STR=/api/v1

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Configuration
ALLOWED_HOSTS=["*"]

# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# PostgreSQL Database Configuration
POSTGRES_DB=hackathondb
POSTGRES_USER=your-database-user
POSTGRES_PASSWORD=your-database-password
POSTGRES_HOST=your-database-host
POSTGRES_PORT=5432

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Logging Configuration
LOG_LEVEL=INFO
```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Available Endpoints

### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user info

### Users

- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get specific user
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Export Data

- `GET /api/v1/export/seasonal-trend` - Get seasonal trend data for commodities
- `GET /api/v1/export/country-demand` - Get all commodities for top 20 countries with growth calculations (ranked by total transaction value)
  - Response Format:
    ```json
    {
      "data": [
        {
          "countryId": "JP",
          "countryName": "Japan",
          "growthPercentage": 15.5,
          "currentTotalTransaction": 1500000.0,
          "products": [
            {
              "id": "CPO",
              "name": "Crude Palm Oil",
              "growth": 30.0
            },
            {
              "id": "COA",
              "name": "Cacao",
              "growth": 25.0
            },
            {
              "id": "ARA",
              "name": "Arabica Coffee",
              "growth": 1.5
            }
          ]
        }
      ]
    }
    ```

## Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app
```

## Database

The application uses SQLAlchemy ORM with PostgreSQL. Make sure your PostgreSQL server is running and accessible with the credentials specified in your `.env` file.

### Database Migrations (Optional)

If you want to use Alembic for database migrations:

1. Initialize Alembic:

```bash
alembic init alembic
```

2. Create a migration:

```bash
alembic revision --autogenerate -m "Initial migration"
```

3. Apply migrations:

```bash
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.
