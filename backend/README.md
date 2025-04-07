# jonas Backend (FastAPI)

This directory contains the Python backend API for jonas, built using FastAPI.

## Prerequisites

- Ensure you have completed the root-level setup described in the main [README.md](../../README.md), including installing `pnpm`.
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v1.27.0+ or V2) installed.
- Python 3.10+ (primarily needed for local development/linting/type checking if not using Docker exclusively).

## Running the Application (Recommended: Docker)

The easiest and recommended way to run the backend service along with its Redis dependency is using Docker Compose from the **project root directory**.

1. **Environment Variables:**
    * Navigate to the `backend` directory: `cd backend`
    * Create a `.env` file by copying the example: `cp .env.example .env`
    * **Crucially, edit the `.env` file** and fill in secure values for `SECRET_KEY`, `JWT_SECRET_KEY`, and any other necessary configurations (like `MONGODB_URL` if used).
    * Return to the project root: `cd ..`
2. **Start Containers:**
    From the **project root directory**, run:
    ```bash
    docker-compose up -d
    ```
    This command will build the backend image (if it doesn't exist) and start the backend and Redis containers in the background.
3. **Accessing the API:**
    The API should now be running and accessible, typically at `http://localhost:8000` (or the `PORT` specified in your root `.env` file if you customized the `docker-compose.yml` port mapping). Check the `/docs` endpoint for the Swagger UI: `http://localhost:8000/docs`.
4. **Stopping Containers:**
    To stop the containers, run from the **project root directory**:
    ```bash
    docker-compose down
    ```

## Running Locally (Alternative / Debugging)

If you prefer to run the backend directly on your host machine (e.g., for easier debugging with certain IDE setups), follow these steps:

1. **Prerequisites:** Ensure Python 3.10+ and `pip` are installed.
2. **Virtual Environment:** From within the `backend` directory:
    ```bash
    python -m venv .venv # Create virtual environment
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```
3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Environment Variables:** Create and configure the `.env` file as described in the Docker setup section (copy `.env.example`).
5. **Run Redis:** You need a separate Redis instance running. If you don't have one installed locally, you can easily start one using Docker:
    ```bash
    docker run -d -p 6379:6379 --name local-redis redis:7-alpine
    ```
    (Remember to stop/remove this container later: `docker stop local-redis && docker rm local-redis`)
6. **Run Uvicorn:** From within the `backend` directory (with the virtual environment activated):
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 
    ```
    The `--reload` flag enables hot reloading for development.

## Architecture: Layered Approach

This backend follows a layered architecture pattern to promote separation of concerns, maintainability, and testability.

1.  **API / Presentation Layer (`app/api/` or `app/routers/`)**
    *   **Responsibility:** Handles incoming HTTP requests, performs input validation (using Pydantic models), and interacts with the Service Layer.
    *   Defines API routes using FastAPI's `APIRouter`.
    *   Parses request data (query parameters, path parameters, request bodies).
    *   Formats HTTP responses.
    *   Handles API-specific exceptions and maps them to appropriate HTTP status codes.
    *   **Does not contain business logic.**

2.  **Service Layer (`app/services/`)**
    *   **Responsibility:** Contains the core business logic of the application.
    *   Orchestrates operations by coordinating calls to one or more repositories.
    *   Implements use cases and application-specific workflows.
    *   Handles business rule validation.
    *   May perform data transformations between domain models and API models if necessary.
    *   **Is independent of the web framework (FastAPI) and the database implementation details.**

3.  **Repository / Data Access Layer (`app/repositories/` or `app/db/`)**
    *   **Responsibility:** Abstracts the data persistence mechanism (MongoDB in this case).
    *   Handles all interactions with the database (CRUD operations: Create, Read, Update, Delete).
    *   Contains database-specific queries.
    *   Maps data between domain models/objects and database representations.
    *   **Provides a clean interface for the Service Layer to interact with data, hiding database specifics.**

4.  **Domain Models / Schemas (`app/models/` or `app/schemas/`)**
    *   **Responsibility:** Defines the core data structures and validation rules for the application's domain entities.
    *   Typically implemented using Pydantic models.
    *   Used across layers for data transfer and validation (e.g., API request/response models, service layer inputs/outputs, repository data structures).

5.  **Core / Utils (`app/core/`, `app/utils/`)**
    *   **Responsibility:** Contains cross-cutting concerns and shared functionality.
    *   Configuration loading (`app/core/config.py`).
    *   Common utilities, helper functions.
    *   Potentially base classes or shared exceptions.

## Exception Handling Flow

Exceptions are used to handle errors and exceptional conditions gracefully across the layers.

1.  **Custom Exceptions:** Define custom exception classes (e.g., in `app/core/exceptions.py` or within relevant modules) to represent specific error conditions:
    *   `ServiceError`: General errors originating from the Service Layer.
    *   `RepositoryError`: Errors related to database operations.
    *   `NotFoundError`: When a requested resource is not found (can be raised by Service or Repository layer).
    *   `DuplicateError`: When attempting to create a resource that already exists.
    *   `ValidationError`: Business rule validation errors (usually raised by the Service Layer).
    *   `AuthenticationError` / `AuthorizationError`: Security-related errors.

2.  **Raising Exceptions:**
    *   The **Repository Layer** might raise `RepositoryError` on database connection issues or `NotFoundError` if a query yields no results.
    *   The **Service Layer** catches specific repository exceptions (like `NotFoundError`), performs business logic, and might raise its own exceptions (like `ValidationError`, `DuplicateError`, or re-raise `NotFoundError` if appropriate for the use case).
    *   The **API Layer** primarily relies on FastAPI's built-in validation for request data (which raises `RequestValidationError`). It generally does *not* raise custom business exceptions itself.

3.  **Propagation:** Custom exceptions are generally allowed to propagate *up* from the Repository Layer to the Service Layer, and from the Service Layer up to the API Layer.

4.  **API Layer Handling:** The key is how the API Layer translates these exceptions into HTTP responses.
    *   **FastAPI Exception Handlers:** Use FastAPI's `@app.exception_handler(...)` decorator (often defined in `app/main.py` or a dedicated `app/core/error_handlers.py`) to catch specific custom exceptions.
    *   **Mapping to HTTP Status Codes:** Inside the exception handler, map the caught custom exception to an appropriate HTTP status code (e.g., `NotFoundError` -> 404, `ValidationError`/`DuplicateError` -> 400 or 422, `AuthenticationError` -> 401, `AuthorizationError` -> 403, general `ServiceError` -> 500).
    *   **Consistent Error Response:** Format a consistent JSON error response body containing details about the error.
    *   **Default Handler:** FastAPI has default handlers for standard exceptions like `RequestValidationError` (422) and `HTTPException`.


**Flow Example (Creating a User):**

1.  HTTP POST request hits `/api/v1/users/`.
2.  The corresponding router function in the **API Layer** validates the incoming JSON payload against a Pydantic schema.
3.  The API Layer calls the `create_user` method in the `UserService` (**Service Layer**), passing the validated data.
4.  The `UserService` performs business logic (e.g., checks if email exists by calling the `UserRepository`).
5.  The `UserService` calls the `create` method in the `UserRepository` (**Repository Layer**).
6.  The `UserRepository` constructs the MongoDB document and inserts it into the database.
7.  The result propagates back up the layers, potentially transforming data models as needed.
8.  The **API Layer** returns an HTTP 201 Created response with the new user data. 