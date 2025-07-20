# Enhanced Authentication System Documentation

## Overview

This document describes the enhanced authentication system implemented for the Hackathon Service API. The system uses JWT (JSON Web Tokens) for secure authentication and supports user registration and login using phone numbers, email addresses, or usernames.

## Key Features

- **Multi-Identifier Login**: Login using phone number, email, or username
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: Bcrypt password hashing for security
- **Comprehensive Validation**: Registration validation for all fields
- **User Registration**: Complete user registration with validation
- **User Login**: Secure login with multiple identifier options
- **User Profile**: Get current user information
- **Logout**: Token invalidation endpoint
- **Availability Checking**: Check if phone number, email, or username is available

## Database Schema

The users table has been updated with the following structure:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    region VARCHAR,
    email VARCHAR UNIQUE,
    username VARCHAR UNIQUE,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### 1. User Registration
**POST** `/api/v1/auth/register`

Register a new user with comprehensive validation.

**Request Body:**
```json
{
    "phone_number": "+6281234567890",
    "name": "John Doe",
    "region": "Jakarta",
    "password": "SecurePass123",
    "email": "john@example.com",
    "username": "johndoe"
}
```

**Validation Rules:**
- Phone number: Required, must be unique, valid format
- Name: Required
- Region: Optional
- Password: Must be at least 8 characters, contain uppercase, lowercase, and number
- Email: Optional, must be unique, valid format
- Username: Optional, must be unique, at least 3 characters, alphanumeric + underscore

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

**Error Response (Multiple Validation Errors):**
```json
{
    "message": "Multiple validation errors",
    "errors": [
        "Phone number already registered",
        "Email already registered",
        "Password must contain at least one uppercase letter"
    ]
}
```

### 2. User Login (Multi-Identifier)
**POST** `/api/v1/auth/login`

Authenticate user with phone number, email, or username and password.

**Request Body:**
```json
{
    "identifier": "+6281234567890",  // Can be phone, email, or username
    "password": "SecurePass123"
}
```

**Login Examples:**
```json
// Login with phone number
{"identifier": "+6281234567890", "password": "SecurePass123"}

// Login with email
{"identifier": "john@example.com", "password": "SecurePass123"}

// Login with username
{"identifier": "johndoe", "password": "SecurePass123"}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### 3. Get Current User
**GET** `/api/v1/auth/me`

Get information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "phone_number": "+6281234567890",
    "name": "John Doe",
    "region": "Jakarta",
    "email": "john@example.com",
    "username": "johndoe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-07-20T13:24:50.914974+00:00",
    "updated_at": null
}
```

### 4. Check Availability
**GET** `/api/v1/auth/check-availability`

Check if phone number, email, or username is available.

**Query Parameters:**
- `phone_number` (optional): Phone number to check
- `email` (optional): Email to check
- `username` (optional): Username to check

**Example:**
```
GET /api/v1/auth/check-availability?phone_number=+6281234567890&email=john@example.com
```

**Response:**
```json
{
    "phone_number": {
        "available": false,
        "message": "Phone number already registered"
    },
    "email": {
        "available": true,
        "message": "Available"
    }
}
```

### 5. Logout
**POST** `/api/v1/auth/logout`

Logout endpoint (client should discard the token).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

## Validation Rules

### Phone Number Validation
- Required field
- Must be unique
- Format: `^\+?[1-9]\d{1,14}$` (international format)
- Examples: `+6281234567890`, `6281234567890`

### Email Validation
- Optional field
- Must be unique if provided
- Standard email format validation
- Examples: `user@example.com`, `john.doe@company.co.id`

### Username Validation
- Optional field
- Must be unique if provided
- Minimum 3 characters
- Only alphanumeric characters and underscores
- Examples: `johndoe`, `user123`, `john_doe`

### Password Validation
- Minimum 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one number
- Examples: `SecurePass123`, `MyPassword2024`

## Usage Examples

### Python Requests Example

```python
import requests

# Register a new user
register_data = {
    "phone_number": "+6281234567890",
    "name": "Test User",
    "region": "Jakarta",
    "password": "SecurePass123",
    "email": "test@example.com",
    "username": "testuser"
}

response = requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
token = response.json()["access_token"]

# Login with different identifiers
login_data = {"identifier": "+6281234567890", "password": "SecurePass123"}
response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)

# Or login with email
login_data = {"identifier": "test@example.com", "password": "SecurePass123"}
response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)

# Or login with username
login_data = {"identifier": "testuser", "password": "SecurePass123"}
response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)

# Use the token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
user_info = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers)
```

### cURL Examples

```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+6281234567890",
    "name": "Test User",
    "region": "Jakarta",
    "password": "SecurePass123",
    "email": "test@example.com",
    "username": "testuser"
  }'

# Login with phone number
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "+6281234567890",
    "password": "SecurePass123"
  }'

# Login with email
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "password": "SecurePass123"
  }'

# Login with username
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "testuser",
    "password": "SecurePass123"
  }'

# Check availability
curl -X GET "http://localhost:8000/api/v1/auth/check-availability?phone_number=+6281234567890&email=test@example.com"

# Get user info
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <your_token>"
```

## Security Features

### Password Security
- Passwords are hashed using bcrypt with salt
- Strong password requirements enforced
- Secure password storage

### JWT Token Security
- Tokens expire after 30 minutes (configurable)
- HS256 algorithm for token signing
- Secure token generation and validation

### Rate Limiting
- Configurable rate limiting per client
- Prevents brute force attacks
- Request throttling

### Input Validation
- Comprehensive validation for all fields
- SQL injection prevention
- XSS protection

## Configuration

The authentication system uses the following configuration settings in `app/core/config.py`:

```python
# Security settings
SECRET_KEY: str = "your-secret-key-here"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Rate limiting settings
RATE_LIMIT_REQUESTS: int = 100
RATE_LIMIT_WINDOW: int = 1  # 1 second window
```

## Testing

### Test Scripts

1. **Create Test User**: `python examples/create_test_user.py`
   - Creates a test user in the database
   - Tests authentication with phone, email, and username

2. **Test API Endpoints**: `python examples/test_auth_api.py`
   - Tests all authentication endpoints
   - Demonstrates multi-login functionality
   - Tests validation and availability checking

### Manual Testing

1. Start the server: `uvicorn app.main:app --reload`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Test the authentication endpoints interactively

## Error Handling

The authentication system includes comprehensive error handling:

- **400 Bad Request**: Invalid input data or validation errors
- **401 Unauthorized**: Invalid credentials or missing token
- **409 Conflict**: Duplicate phone number, email, or username
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side errors

### Validation Error Examples

```json
// Single validation error
{
    "detail": "Phone number already registered"
}

// Multiple validation errors
{
    "detail": {
        "message": "Multiple validation errors",
        "errors": [
            "Phone number already registered",
            "Email already registered",
            "Password must contain at least one uppercase letter"
        ]
    }
}
```

## Security Best Practices

1. **Environment Variables**: Store sensitive data in environment variables
2. **HTTPS**: Use HTTPS in production
3. **Token Expiration**: Short-lived tokens with refresh mechanism
4. **Input Validation**: Validate all user inputs
5. **Rate Limiting**: Prevent abuse and brute force attacks
6. **Password Policy**: Enforce strong password requirements
7. **Logging**: Log authentication events for monitoring
8. **Unique Constraints**: Ensure data integrity with database constraints

## Future Enhancements

- [ ] Email verification
- [ ] Phone number verification via SMS
- [ ] Password reset functionality
- [ ] Refresh token mechanism
- [ ] Multi-factor authentication
- [ ] OAuth integration
- [ ] Role-based access control
- [ ] Session management
- [ ] Account lockout after failed attempts
- [ ] Password history tracking

## Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure database connection is correct
2. **Token Expiration**: Check token expiration time
3. **Rate Limiting**: Reduce request frequency
4. **Password Issues**: Verify password meets requirements
5. **Duplicate Identifiers**: Check for existing phone numbers, emails, or usernames

### Debug Mode

Enable debug logging by setting:
```python
LOG_LEVEL = "DEBUG"
```

## Support

For issues or questions about the authentication system, please refer to:
- API Documentation: `/docs` endpoint
- Database Schema: Check migration files
- Configuration: `app/core/config.py`
- Test Scripts: `examples/` directory 