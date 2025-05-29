# SQL Tool Testing

This directory contains scripts for testing the SQL query tool in the Agentic RAG system.

## Test Database

The test database is a SQLite database with the following tables:

- `staff`: Information about university staff members
- `departments`: Information about university departments
- `budgets`: Budget information for departments
- `facilities`: Information about university facilities

These tables match the allowed tables in the admin_bot.yaml configuration.

## Test Scripts

### 1. Create Test Database

The `create_test_db.py` script creates a test SQLite database with sample data:

```bash
python tests/create_test_db.py
```

This will create a file called `test_db.sqlite` in the project root directory.

### 2. Test SQL Tool

The `test_sql_tool.py` script tests the SQL query tool with various SQL queries:

```bash
python tests/test_sql_tool.py
```

This script tests:
- Basic SELECT queries
- JOIN queries
- Aggregate queries
- Complex queries
- Queries with Turkish characters

### 3. Update Bot Configurations

The `update_configs.py` script updates the bot configuration files to use the test database:

```bash
python tests/update_configs.py
```

This script updates the `connection_string` in the SQLQueryTool configuration in all bot configuration files to use the test database.

### 4. Run All Tests

The `run_sql_tests.ps1` PowerShell script runs all the tests in sequence:

```powershell
.\tests\run_sql_tests.ps1
```

## Sample Queries

Here are some sample queries you can use to test the SQL tool:

### Basic Queries

```sql
SELECT * FROM staff LIMIT 5
SELECT name, position FROM staff WHERE department_id = 1
SELECT * FROM departments
SELECT * FROM budgets WHERE fiscal_year = 2023
SELECT * FROM facilities WHERE type = 'Laboratory'
```

### JOIN Queries

```sql
SELECT s.name, d.name as department 
FROM staff s 
JOIN departments d ON s.department_id = d.id

SELECT d.name, b.amount 
FROM departments d 
JOIN budgets b ON d.id = b.department_id 
WHERE b.fiscal_year = 2023
```

### Aggregate Queries

```sql
SELECT department_id, COUNT(*) as staff_count 
FROM staff 
GROUP BY department_id

SELECT fiscal_year, SUM(amount) as total_budget 
FROM budgets 
GROUP BY fiscal_year
```

### Complex Queries

```sql
SELECT d.name as department, s.name as head, b.amount as budget
FROM departments d
JOIN staff s ON d.head_id = s.id
JOIN budgets b ON d.budget_id = b.id
WHERE b.fiscal_year = 2023
ORDER BY b.amount DESC
```

### Queries with Turkish Characters

```sql
SELECT * FROM staff WHERE name LIKE '%Öztürk%'
SELECT * FROM staff WHERE name LIKE '%Yılmaz%'
```

## Using the SQL Tool in the API

To use the SQL tool in the API, you can make a request like this:

```bash
curl -X POST "http://localhost:8000/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What is the budget for the Computer Science department?\", \"session_id\": \"test-sql\"}"
```

The system will automatically detect that this is a query that should use the SQL tool and execute the appropriate SQL query.
