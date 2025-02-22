# DSL Specification for Safe SQL Queries

## Overview
This specification defines a secure way to execute user-provided SQL queries with built-in security controls. It uses a JSON-based DSL (Domain Specific Language) to ensure queries are safe and properly validated before execution.

## 1. DSL Schema

### 1.1 Schema Definition
```json
{
    "version": "1.0",
    "metadata": {
        "description": "Description of the query's purpose",
        "requestId": "unique-request-id"
    },
    "user_variables": {
        "my_matching_unit_id": "user input matching id",
        "org_id": "user input org id"
    },
    "user_view_only_query": "SELECT other.matching_unit_id, other.file_id FROM matching_units AS my JOIN matching_units AS other ON my.trading_party_code = other.counterparty_code AND my.counterparty_code = other.trading_party_code AND my.transaction_details->'pay_leg'->>'currency' = other.transaction_details->'receive_leg'->>'currency' WHERE my.matching_unit_id = :my_matching_unit_id AND my.org_id = :org_id",
    "allowed_tables": [
        "matching_units"
    ]
}
```

### 1.2 Schema Components
- **version**: Schema version for compatibility checking
- **metadata**: Query metadata including description and request tracking
- **user_variables**: Named parameters that will be bound to the query
- **user_view_only_query**: The SQL SELECT query to execute
- **allowed_tables**: List of tables the query is allowed to access

## 2. Query Processing Flow

### 2.1 Request Handling
```python
def process_query_request(dsl_json: dict, user_vars: dict) -> dict:
    """
    Process an incoming query request
    
    Args:
        dsl_json: The DSL specification
        user_vars: User-provided variable values
    
    Returns:
        dict: Query results or error message
    """
    try:
        # Validate DSL schema
        validate_dsl_schema(dsl_json)
        
        # Validate SQL
        validate_sql(dsl_json["user_view_only_query"])
        
        # Execute query
        results = execute_safe_query(dsl_json, user_vars)
        
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 2.2 Query Execution
```python
def execute_safe_query(dsl: dict, user_vars: dict) -> list:
    """Execute query with security controls"""
    # Merge variables
    parameters = {**dsl["user_variables"], **user_vars}
    
    # Build secure query
    final_sql = f"""
        SELECT * 
        FROM ({dsl['user_view_only_query']}) AS secure_subquery 
        WHERE org_id = :org_id
    """
    
    # Execute with role restriction
    with engine.connect() as conn:
        conn.execute("SET ROLE dsl_executor")
        try:
            result = conn.execute(text(final_sql), parameters)
            return [dict(row) for row in result]
        finally:
            conn.execute("RESET ROLE")
```

## 3. Security Controls

### 3.1 SQL Validation
```python
def validate_sql(sql: str) -> bool:
    """Validate SQL query meets security requirements"""
    # Parse SQL
    parsed = sqlparse.parse(sql)
    if not parsed:
        raise ValueError("Empty SQL query")
    
    # Must be SELECT statement
    stmt = parsed[0]
    if stmt.get_type() != "SELECT":
        raise ValueError("Only SELECT statements allowed")
    
    # Check for dangerous operations
    lower_sql = sql.lower()
    forbidden = ["insert", "update", "delete", "drop", "alter", "create"]
    if any(kw in lower_sql for kw in forbidden):
        raise ValueError("Disallowed SQL operation detected")
    
    return True
```

### 3.2 Table and Function Validation
```python
def validate_tables_and_functions(sql: str, allowed_tables: list, allowed_functions: list) -> bool:
    """Validate tables and functions against allowed lists"""
    lower_sql = sql.lower()
    
    # Check tables
    table_matches = re.findall(r'\bfrom\s+([\w]+)', lower_sql)
    for table in table_matches:
        if table not in allowed_tables:
            raise ValueError(f"Unauthorized table: {table}")
    
    # Check functions
    function_matches = re.findall(r'(\w+)\s*\(', lower_sql)
    for func in function_matches:
        if func.upper() not in allowed_functions:
            raise ValueError(f"Unauthorized function: {func}")
    
    return True
```

## 4. Security Best Practices

### 4.1 Query Protection
- Use parameterized queries to prevent SQL injection
- Wrap user queries in subqueries for additional filtering
- Validate all SQL before execution
- Restrict to SELECT operations only

### 4.2 Access Control
- Execute queries under restricted database role
- Implement table-level access control
- Apply row-level security via org_id filtering
- Control allowed SQL functions

### 4.3 Error Handling
- Return standardized error responses
- Log all validation failures
- Don't expose internal error details to users
- Track queries with request IDs

## 5. Example Usage

### 5.1 Basic Query Request
```python
dsl_request = {
    "version": "1.0",
    "metadata": {
        "description": "Find matching trades",
        "requestId": "req-123"
    },
    "user_variables": {
        "my_matching_unit_id": "MU001",
        "org_id": "ORG1"
    },
    "user_view_only_query": """
        SELECT other.matching_unit_id, other.file_id
        FROM matching_units AS my
        JOIN matching_units AS other 
            ON my.trading_party_code = other.counterparty_code
        WHERE my.matching_unit_id = :my_matching_unit_id
            AND my.org_id = :org_id
    """,
    "allowed_tables": ["matching_units"]
}

# Process request
result = process_query_request(dsl_request, {"my_matching_unit_id": "MU002"})