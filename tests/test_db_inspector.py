"""Unit tests for the database inspector utility."""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.db_inspector import DatabaseInspector, TableInfo, OutputFormat


@pytest.fixture
def test_db():
    """Create a test SQLite database with sample data."""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    # Set up test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)
    
    # Insert test data
    cursor.executemany(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        [("alice", "alice@example.com"), ("bob", "bob@example.com")]
    )
    
    cursor.executemany(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        [("Laptop", 999.99, 10), ("Mouse", 24.99, 50)]
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Clean up
    try:
        os.unlink(db_path)
    except OSError:
        pass


def test_database_inspector_init(test_db):
    """Test DatabaseInspector initialization."""
    # Test with valid database
    inspector = DatabaseInspector(test_db)
    assert inspector.db_path == Path(test_db).resolve()
    
    # Test with non-existent database
    with pytest.raises(FileNotFoundError):
        DatabaseInspector("nonexistent.db")


def test_get_table_names(test_db):
    """Test getting table names."""
    with DatabaseInspector(test_db) as inspector:
        tables = inspector.get_table_names()
        assert set(tables) == {"users", "products"}


def test_get_table_info(test_db):
    """Test getting table information."""
    with DatabaseInspector(test_db) as inspector:
        # Test with existing table
        table_info = inspector.get_table_info("users")
        assert isinstance(table_info, TableInfo)
        assert table_info.name == "users"
        assert len(table_info.schema) == 4  # id, username, email, is_active
        assert table_info.row_count == 2
        assert len(table_info.data) == 2  # We have 2 users
        
        # Test with non-existent table
        with pytest.raises(ValueError):
            inspector.get_table_info("nonexistent")


def test_inspect_output_formats(test_db, capsys):
    """Test different output formats."""
    with DatabaseInspector(test_db) as inspector:
        # Test grid format (default)
        inspector.inspect(limit=1)
        output = capsys.readouterr().out
        assert "users" in output
        assert "products" in output
        
        # Test JSON format
        inspector.inspect(output_format=OutputFormat.JSON)
        output = capsys.readouterr().out
        assert '"users"' in output
        assert '"products"' in output
        
        # Test table filtering
        inspector.inspect(table_filter="use%")
        output = capsys.readouterr().out
        assert "users" in output
        assert "products" not in output


def test_output_to_file(test_db, tmp_path):
    """Test output to file."""
    output_file = tmp_path / "output.json"
    
    with DatabaseInspector(test_db) as inspector:
        inspector.inspect(output_format=OutputFormat.JSON, output_file=str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text()
    assert '"users"' in content


def test_sanitize_identifier(tmp_path):
    """Test SQL identifier sanitization."""
    # Create a temporary database file
    db_path = tmp_path / "test.db"
    db_path.touch()
    
    inspector = DatabaseInspector(str(db_path))
    assert inspector._sanitize_identifier("test") == '"test"'
    assert inspector._sanitize_identifier("user data") == '"user data"'


@patch('builtins.print')
def test_command_line_interface(mock_print, test_db):
    """Test the command-line interface."""
    from src.utils.db_inspector import main
    
    # Mock sys.argv
    with patch('sys.argv', ['db_inspector.py', test_db, '--table', 'users', '--limit', '1']):
        main()
    
    # Get all print calls
    output = "\n".join(str(call[0][0]) for call in mock_print.call_args_list)
    
    # Verify output contains users table
    assert "users" in output
    assert "products" not in output  # Should be filtered out


def test_table_info_representation():
    """Test TableInfo string representation."""
    table_info = TableInfo(
        name="test",
        schema=[{"name": "id", "type": "INTEGER", "notnull": True}],
        row_count=5,
        data=[(1,), (2,)]
    )
    
    # Test string representation
    assert "TableInfo(name='test'" in str(table_info)
    
    # Test data access
    assert table_info.name == "test"
    assert len(table_info.schema) == 1
    assert table_info.schema[0]["name"] == "id"
    assert table_info.row_count == 5
    assert len(table_info.data) == 2


if __name__ == "__main__":
    pytest.main([__file__])
