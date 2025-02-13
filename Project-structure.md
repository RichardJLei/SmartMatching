# Project Structure Overview

## Root Directory
├── load-test.js - Artillery performance testing configuration
├── Project-structure.md - Architecture documentation
├── Spec-Pagination-Parameters.md - API pagination/filtering specification

## Backend Structure
backend/
├── api/
│   ├── dependencies/
│   │   ├── access_control.py - Role-based access control
│   │   ├── pagination.py - Pagination & filter parameter handling
│   │   ├── blog_post_sql.py - Blog post CRUD operations
│   │   └── auth.py - Authentication and authorization handling
│   ├── routes/
│   │   ├── blog_posts.py - Blog post related endpoints
│   │   └── users.py - User management endpoints
│   └── main.py - FastAPI app configuration and routes
│
├── database/
│   ├── models.py - SQLAlchemy data models
│   ├── migrations/ - Alembic database migrations
│   └── core.py - Database connection management
│
└── tests/
    ├── test_blog_posts.py - Blog post endpoint tests
    └── test_auth.py - Authentication tests

## Frontend Structure
frontend/src/
├── providers/
│   ├── dataProvider.ts - React-Admin data provider implementation
│   └── authProvider.ts - Authentication provider
│
├── hooks/
│   ├── useTableCustomization.tsx - Custom hook for table features
│   └── useAuth.tsx - Authentication hook
│
├── components/
│   ├── Table/
│   │   ├── CustomTable.tsx - Reusable table component
│   │   └── TableFilters.tsx - Table filtering components
│   └── common/
│       ├── Layout.tsx - Common layout components
│       └── Forms.tsx - Reusable form components
│
├── pages/
│   ├── blog-post-sql/
│   │   ├── list.tsx - Blog post listing UI with filtering/pagination
│   │   ├── create.tsx - Blog post creation form
│   │   └── edit.tsx - Blog post editing form
│   └── auth/
│       ├── login.tsx - Login page
│       └── register.tsx - Registration page
│
└── utils/
    ├── api.ts - API utility functions
    └── helpers.ts - Common helper functions

## Documentation
docs/
├── Spec-*.md - Technical specifications for API consumers
└── api-docs/ - OpenAPI documentation

## Key Implementation Details
1. **Pagination** - Uses `_start`/`_end` parameters with `X-Total-Count` header
2. **Filtering** - Supports 12 operators via `filter[field]` query params
3. **CORS** - Configured in main.py with exposed headers
4. **Error Handling** - Standardized error responses for client parsing
5. **Testing** - Artillery load tests and React component tests
6. **Authentication** - JWT-based authentication system
7. **Database Migrations** - Alembic for version control of database schema

## Critical Dependencies
- `pagination.py`: Central parameter validation
- `dataProvider.ts`: Frontend API communication layer
- `useTableCustomization.tsx`: Table feature customization
- `Spec-Pagination-Parameters.md`: Frontend/backend contract
- `auth.py`: Authentication middleware
- `authProvider.ts`: Frontend authentication handling
