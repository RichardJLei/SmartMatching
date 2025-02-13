# Project Style Document

## 1. DRY (Don't Repeat Yourself)
- **Check**  .Project-structure.md before adding new functions, services, or modules.
- **Reuse** built-in and existing packages/services/modules whenever possible.
- **Notify** if unsure whether a service is available.
- **Create new files only when:**
  - The required business logic is new.
  - Coordinating with multiple existing modules.
  - Using abstractions for shared/re-usable business logic.

## 2. Documentation Standards

- **Docstrings:** Include docstrings for all functions, classes, and modules.s
- **API Documentation:** Use **Swagger** for documenting FastAPI REST API endpoints.
- **Code Comments:** Add meaningful inline comments for complex logic or important sections of the code.

## 3. API Interaction Standards

- **Asynchronous Communication:** Follow Refine's simple-rest data provider best practices.

## 4. Technology Stack

- **Database:** PostgreSQL. Use SQLAlchemy for sync and async operations. Async operations are preferred.
- **Backend Framework:** FastAPI.
- **Frontend Framework:** Refine React Framework.
- **Schema middleware Framework:** Retool.
- **Authentication & Storage:** Firebase Auth and Filebase Storage.


### 5. Project structure Guidelines

\frontend: Refine React Framework
\backend\api: APIs using FastAPI routers 
\frontend\config: Frontend Environment variables
\backend\config: Backend Environment variables
\docs: Documentation
\backend\tests: Write unit and integration tests using frameworks like **pytest**
\backend\utils: Utility functions
\backend\database: Retool configuration
\Dockerfile: Docker configuration



  
