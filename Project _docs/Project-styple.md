# Project Style Guide

## 1. DRY (Don't Repeat Yourself) when creating new functions, services, or modules
- **Check** `.Project-structure.md` before adding new functions, services, or modules to understand the existing project structure and to prevent redundancy.
- **Reuse** built-in and existing packages/services/modules whenever possible to minimize code duplication and leverage existing functionalities.
- **Ask** if unsure whether a functionality exists or if your upcoming changes could impact existing modules.


## 2. Single Responsibility Principle when creating new files
- **Single Responsibility:** Ensure each file or module has a single responsibility and adheres to one specific aspect of the functionality.
- **Logical Grouping:** Group similar functionalities together in logically organized files and folders.
- **Limit File Size:** Aim to keep files compact (suggested max of 200-300 lines) to facilitate ease of management and understanding.
- **Descriptive Naming:** Use descriptive and intuitive naming for files and directories to reflect their purpose and content clearly.
- **Modularize by Features:** Organize code into feature-specific modules to enhance clarity and reduce dependencies.

## 3. organise project dictories and files following the following structure:
### `/api` - API Interface Layer
Contains all the router definitions for the API endpoints. Each endpoint related to a specific resource has its own router file.

```plaintext
/backend
    /api
        /routers
            /users               # User-related endpoints
                add_user.py
                get_user.py
                update_user.py
                delete_user.py
            /transactions        # Transaction-related endpoints
                add_transaction.py
                get_transaction.py
            ...
        /schemas                # Pydantic models for request and response validation
            user_schema.py
            transaction_schema.py
        ...
```
### `/services` - Business Logic Layer
Handles the core business logic, separated from API routing. Each major functionality has its own service file.

```plaintext
/backend
    /services
        /user
            add_user_service.py
            get_user_service.py
            update_user_service.py
            delete_user_service.py
        /transaction
            add_transaction_service.py
            get_transaction_service.py
        ...
``` 

### `/utils` - Utility Functions
Contains reusable code snippets, helper functions, and common utilities that can be used across different parts of the application.

```plaintext
/backend
    /utils
        password_hashing.py
        email_sender.py
        ...
``` 

### `/utils` - Utility Functions
Contains reusable code snippets, helper functions, and common utilities that can be used across different parts of the application.

```plaintext
/backend
    /utils
        password_hashing.py
        email_sender.py
        ...
``` 

### `/database` - Database Interaction Layer
Manages all database models and database interaction logic. Includes ORM models and potentially database migration scripts.

```plaintext
/backend
    /database
        /models                 # ORM models
            user_model.py
            transaction_model.py
        ...
        /crud                   # CRUD operations utilities
            user_crud.py
            transaction_crud.py
        ...
        /migrations             # Database migration scripts (e.g., Alembic)
``` 

### `/docs` - Documentation
Contains all project documentation, including auto-generated API documentation and manual guides.

```plaintext
//docs
    api_docs.md
    project_setup.md
    ...
``` 

### `/tests` - Testing
Includes all test cases for unit testing and integration testing. 

```plaintext
/backend
    /tests
        /unit                   # Unit tests
            test_user_service.py
            test_transaction_service.py
        ...
        /integration            # Integration tests
            test_user_api.py
            test_transaction_api.py
        ...
``` 

### `/frontend` - Frontend Application
Contains all frontend-related files, organized by the Refine React Framework.

### `/config` - Configuration Files
Configurations for the application, Docker, and other infrastructure components.

```plaintext
/backend
    /config
        docker-compose.yml
        .env
        ...
``` 

## 4. Documentation Standards
- **Docstrings:** Include docstrings for all functions, classes, and modules to provide clear descriptions and facilitate maintenance. Use a consistent style, such as Google style or NumPy/SciPy style, for docstrings.
- **API Documentation:** Use **Swagger** for documenting all FastAPI REST API endpoints, ensuring that the API is easily understandable and usable.
- **Code Comments:** Add meaningful inline comments to elucidate complex logic or crucial sections of the code, enhancing readability and maintainability.
- **Automated Documentation Generation:** Utilize Sphinx for Python to generate documentation automatically from docstrings. This helps in maintaining up-to-date documentation and reduces manual effort. Ensure that all docstrings are written in a manner that supports Sphinx’s autodoc utility, which can pull documentation directly from the code comments.

## 5. Technology Stack
- **Database:** PostgreSQL. Alembic for migrations (sync db connection).
- **Backend Framework:** FastAPI + SQLAlchemy (async operations are preferred).
- **Frontend Framework:** Refine React Framework.
- **Authentication & Storage:** Use Firebase Auth for authentication and Filebase Storage for file management.
- **AI service** provide abstraction for Google, Deepseek, both cloud and local.
- **API Asynchronous Communication:** Follow best practices for asynchronous REST communications as recommended by the Refine's simple-rest data provider

