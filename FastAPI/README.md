# LLM Project to Build and Fine Tune a Large Language Model

This project is an example of a simple FastAPI implementation.

The implementation keypoints:
1. FastAPI Best Practices

Comprehensive API metadata (title, description, version, contact info)
Proper HTTP status codes (201 for creation, 204 for deletion)
Response models for all endpoints
Request/response examples in schema
Organized endpoints with tags for better documentation

2. Advanced FastAPI Features

Dependencies: Used Depends() for item retrieval logic
Query Parameters: Added pagination (limit, skip) and filtering
Path Parameters: Proper validation for UUIDs
Exception Handling: Custom HTTP exception handler
Middleware: CORS middleware for cross-origin requests
Lifecycle Events: Startup and shutdown event handlers

3. Production Features

Logging: Structured logging throughout the application
Health Check: Dedicated endpoint for monitoring
Statistics: Endpoint to get item statistics
Search Functionality: Text search in items
Error Responses: Standardized error format

4. CRUD Operations

Full CRUD (Create, Read, Update, Delete) implementation
Partial updates using exclude_unset=True
Proper error handling for not found items

5. Security & Performance

Input validation and sanitization
Pagination to prevent large response payloads
Proper HTTP methods and status codes

6. Test Coverage:

Basic Functionality Tests: Health check endpoint, Root welcome endpoint, Complete CRUD operations (Create, Read, Update, Delete)
Validation Tests: Input validation for item creation, Query parameter validation, UUID format validation, Field constraint testing (text length, required fields)
Advanced Feature Tests: Pagination (limit, skip parameters), Filtering (by completion status), Search functionality (text search), Statistics endpoint, Partial updates
Error Handling Tests: 404 errors for non-existent items, 422 validation errors, Proper HTTP status codes, Error response format validation
Edge Cases: Empty data scenarios, Boundary value testing, Invalid UUID handling, Large dataset handling

## How to Use This Code Project

### Step 1: Clone the Repository

First, clone this project repository to your local machine using the following command:

```bash
git clone 
cd '.\API\FastAPI'
```

### Step 2: Install Dependencies

Install the necessary Python packages defined in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 3: Launch FastAPI app

```bash
cd '.\src'
python main.py
```

### Step 4: Test the app

Option 1

```bash
python test_tools_api.py
```

Option 2

```bash
pytest test_todo_api.py -v
```

Option 3
Launch your preferred browser and go to: http://0.0.0.0:8000