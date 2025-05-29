#!/usr/bin/env python
"""
Script to create a test SQLite database for testing the SQL query tool.

This script creates a sample database with tables for:
- staff
- departments
- budgets
- facilities

These tables match the allowed_tables in the admin_bot.yaml configuration.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database file path
DB_PATH = "test_db.sqlite"


def create_database():
    """Create the test database with sample tables and data."""
    # Check if the database already exists
    if os.path.exists(DB_PATH):
        logger.info(f"Database {DB_PATH} already exists. Removing it...")
        os.remove(DB_PATH)

    # Create a new database
    logger.info(f"Creating database {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    logger.info("Creating tables...")

    # Staff table
    cursor.execute('''
    CREATE TABLE staff (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        position TEXT NOT NULL,
        department_id INTEGER,
        email TEXT,
        phone TEXT,
        hire_date TEXT
    )
    ''')

    # Departments table
    cursor.execute('''
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        head_id INTEGER,
        location TEXT,
        budget_id INTEGER
    )
    ''')

    # Budgets table
    cursor.execute('''
    CREATE TABLE budgets (
        id INTEGER PRIMARY KEY,
        department_id INTEGER,
        fiscal_year INTEGER,
        amount REAL,
        allocated_date TEXT,
        status TEXT
    )
    ''')

    # Facilities table
    cursor.execute('''
    CREATE TABLE facilities (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        location TEXT,
        capacity INTEGER,
        department_id INTEGER
    )
    ''')

    # Insert sample data
    logger.info("Inserting sample data...")

    # Insert departments
    departments = [
        (1, "Computer Science", 1, "Building A, Floor 2", 1),
        (2, "Mathematics", 2, "Building B, Floor 1", 2),
        (3, "Physics", 3, "Building C, Floor 3", 3),
        (4, "Chemistry", 4, "Building D, Floor 2", 4),
        (5, "Biology", 5, "Building E, Floor 1", 5),
    ]
    cursor.executemany(
        "INSERT INTO departments VALUES (?, ?, ?, ?, ?)", departments
    )

    # Insert staff
    staff = [
        (1, "Dr. Ahmet Yılmaz", "Department Head", 1, "ahmet.yilmaz@atlas.edu.tr", "+90 212 555 1001", "2010-09-01"),
        (2, "Dr. Ayşe Kaya", "Department Head", 2, "ayse.kaya@atlas.edu.tr", "+90 212 555 1002", "2011-08-15"),
        (3, "Dr. Mehmet Demir", "Department Head", 3, "mehmet.demir@atlas.edu.tr", "+90 212 555 1003", "2009-07-20"),
        (4, "Dr. Zeynep Şahin", "Department Head", 4, "zeynep.sahin@atlas.edu.tr", "+90 212 555 1004", "2012-06-10"),
        (5, "Dr. Mustafa Öztürk", "Department Head", 5, "mustafa.ozturk@atlas.edu.tr", "+90 212 555 1005", "2013-05-05"),
        (6, "Dr. Elif Yıldız", "Professor", 1, "elif.yildiz@atlas.edu.tr", "+90 212 555 1006", "2014-04-15"),
        (7, "Dr. Emre Kara", "Associate Professor", 2, "emre.kara@atlas.edu.tr", "+90 212 555 1007", "2015-03-20"),
        (8, "Dr. Selin Arslan", "Assistant Professor", 3, "selin.arslan@atlas.edu.tr", "+90 212 555 1008", "2016-02-25"),
        (9, "Dr. Burak Yılmaz", "Lecturer", 4, "burak.yilmaz@atlas.edu.tr", "+90 212 555 1009", "2017-01-30"),
        (10, "Dr. Deniz Çelik", "Research Assistant", 5, "deniz.celik@atlas.edu.tr", "+90 212 555 1010", "2018-12-05"),
    ]
    cursor.executemany(
        "INSERT INTO staff VALUES (?, ?, ?, ?, ?, ?, ?)", staff
    )

    # Insert budgets
    budgets = [
        (1, 1, 2023, 500000.00, "2023-01-15", "Approved"),
        (2, 2, 2023, 350000.00, "2023-01-20", "Approved"),
        (3, 3, 2023, 450000.00, "2023-01-25", "Approved"),
        (4, 4, 2023, 400000.00, "2023-01-30", "Approved"),
        (5, 5, 2023, 380000.00, "2023-02-05", "Approved"),
        (6, 1, 2022, 480000.00, "2022-01-10", "Closed"),
        (7, 2, 2022, 330000.00, "2022-01-15", "Closed"),
        (8, 3, 2022, 430000.00, "2022-01-20", "Closed"),
        (9, 4, 2022, 380000.00, "2022-01-25", "Closed"),
        (10, 5, 2022, 360000.00, "2022-01-30", "Closed"),
    ]
    cursor.executemany(
        "INSERT INTO budgets VALUES (?, ?, ?, ?, ?, ?)", budgets
    )

    # Insert facilities
    facilities = [
        (1, "Computer Lab A", "Laboratory", "Building A, Room 101", 30, 1),
        (2, "Computer Lab B", "Laboratory", "Building A, Room 102", 25, 1),
        (3, "Mathematics Library", "Library", "Building B, Room 201", 50, 2),
        (4, "Physics Lab", "Laboratory", "Building C, Room 301", 20, 3),
        (5, "Chemistry Lab", "Laboratory", "Building D, Room 401", 15, 4),
        (6, "Biology Lab", "Laboratory", "Building E, Room 501", 18, 5),
        (7, "Conference Room 1", "Meeting Room", "Building A, Room 103", 100, None),
        (8, "Conference Room 2", "Meeting Room", "Building B, Room 202", 80, None),
        (9, "Cafeteria", "Dining", "Building F, Floor 1", 200, None),
        (10, "Library", "Library", "Building G, Floor 1-3", 300, None),
    ]
    cursor.executemany(
        "INSERT INTO facilities VALUES (?, ?, ?, ?, ?, ?)", facilities
    )

    # Commit changes and close connection
    conn.commit()
    conn.close()

    logger.info(f"Database {DB_PATH} created successfully!")
    return os.path.abspath(DB_PATH)


if __name__ == "__main__":
    db_path = create_database()
    print(f"Test database created at: {db_path}")
