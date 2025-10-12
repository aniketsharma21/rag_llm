"""
Database Inspector Utility

This module provides functionality to inspect SQLite database schema and data.
It supports various output formats, table filtering, and pagination.

Usage:
    from src.utils.db_inspector import inspect_database
    
    # Basic usage
    inspector = DatabaseInspector("path/to/database.db")
    inspector.inspect()
    
    # With custom options
    inspector.inspect(
        table_filter="user%",  # Only show tables matching pattern
        limit=5,              # Rows per table
        output_format="grid",  # 'grid', 'plain', 'json', or 'csv'
        show_schema=True,     # Whether to show table schema
        show_data=True,       # Whether to show table data
    )
"""

import os
import sqlite3
import json
import csv
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class OutputFormat(str, Enum):
    """Supported output formats for the database inspection results."""
    GRID = "grid"
    PLAIN = "plain"
    JSON = "json"
    CSV = "csv"


@dataclass
class TableInfo:
    """Data class to store table information."""
    name: str
    schema: List[Dict[str, str]]
    row_count: int
    data: List[tuple]


class DatabaseInspector:
    """A utility class for inspecting SQLite database schema and data."""
    
    def __init__(self, db_path: str):
        """Initialize the database inspector with the path to the SQLite database.
        
        Args:
            db_path: Path to the SQLite database file.
            
        Raises:
            FileNotFoundError: If the database file does not exist.
            sqlite3.Error: If there's an error connecting to the database.
        """
        self.db_path = Path(db_path).resolve()
        self._validate_db_path()
        self.conn: Optional[sqlite3.Connection] = None
    
    def _validate_db_path(self) -> None:
        """Validate that the database file exists and is accessible."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        if not os.access(self.db_path, os.R_OK):
            raise PermissionError(f"No read permission for database file: {self.db_path}")
    
    def connect(self) -> None:
        """Establish a connection to the database."""
        try:
            self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Failed to connect to database: {e}")
    
    def close(self) -> None:
        """Close the database connection if it's open."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_table_names(self) -> List[str]:
        """Get a list of all tables in the database.
        
        Returns:
            List of table names.
            
        Raises:
            sqlite3.Error: If there's an error executing the query.
        """
        if not self.conn:
            self.connect()
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """)
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Failed to fetch table names: {e}")
    
    def get_table_info(self, table_name: str) -> TableInfo:
        """Get information about a specific table.
        
        Args:
            table_name: Name of the table to inspect.
            
        Returns:
            TableInfo object containing schema and data.
            
        Raises:
            sqlite3.Error: If there's an error executing the query.
            ValueError: If the table doesn't exist.
        """
        if not self.conn:
            self.connect()
        
        # First verify the table exists and get its schema
        cursor = self.conn.cursor()
        
        try:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({self._sanitize_identifier(table_name)});")
            schema = [
                {"name": row[1], "type": row[2], "notnull": bool(row[3])}
                for row in cursor.fetchall()
            ]
            
            if not schema:
                raise ValueError(f"Table '{table_name}' not found or has no columns")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {self._sanitize_identifier(table_name)};")
            row_count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {self._sanitize_identifier(table_name)} LIMIT 10;")
            data = cursor.fetchall()
            
            return TableInfo(
                name=table_name,
                schema=schema,
                row_count=row_count,
                data=data
            )
            
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Error inspecting table '{table_name}': {e}")
    
    @staticmethod
    def _sanitize_identifier(identifier: str) -> str:
        """Sanitize SQL identifiers to prevent SQL injection."""
        # For simplicity, just quote the identifier - in a production environment,
        # you might want to use a proper SQL escaping library
        return f'"{identifier}"'
    
    def inspect(
        self,
        table_filter: str = "%",
        limit: int = 10,
        output_format: Union[str, OutputFormat] = OutputFormat.GRID,
        show_schema: bool = True,
        show_data: bool = True,
        output_file: Optional[str] = None
    ) -> None:
        """Inspect the database and print the results.
        
        Args:
            table_filter: SQL LIKE pattern to filter tables (e.g., 'user%').
            limit: Maximum number of rows to show per table.
            output_format: Output format ('grid', 'plain', 'json', or 'csv').
            show_schema: Whether to show table schema.
            show_data: Whether to show table data.
            output_file: If provided, save output to this file instead of printing.
        """
        if not self.conn:
            self.connect()
        
        try:
            # Get list of tables matching the filter
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                AND name LIKE ?
                ORDER BY name;
            """, (table_filter,))
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print(f"{Fore.YELLOW}No tables found matching pattern: {table_filter}{Style.RESET_ALL}")
                return
            
            # Collect information about each table
            results = {}
            for table_name in tables:
                try:
                    table_info = self.get_table_info(table_name)
                    results[table_name] = table_info
                except Exception as e:
                    print(f"{Fore.RED}Error processing table '{table_name}': {e}{Style.RESET_ALL}")
            
            # Format and output the results
            output = self._format_output(results, output_format, show_schema, show_data, limit)
            
            if output_file:
                self._write_output(output, output_file, output_format)
            else:
                print(output)
                
        except sqlite3.Error as e:
            print(f"{Fore.RED}Database error: {e}{Style.RESET_ALL}")
    
    def _format_output(
        self,
        results: Dict[str, TableInfo],
        output_format: Union[str, OutputFormat],
        show_schema: bool,
        show_data: bool,
        limit: int
    ) -> str:
        """Format the inspection results according to the specified output format."""
        output_format = OutputFormat(output_format.lower())
        
        if output_format in (OutputFormat.JSON, OutputFormat.CSV):
            # For structured formats, build a complete data structure
            output_data = {}
            for table_name, table_info in results.items():
                table_data = {
                    "row_count": table_info.row_count
                }
                
                if show_schema:
                    table_data["schema"] = table_info.schema
                
                if show_data and table_info.data:
                    columns = [col["name"] for col in table_info.schema]
                    table_data["data"] = [
                        dict(zip(columns, row))
                        for row in table_info.data[:limit]
                    ]
                
                output_data[table_name] = table_data
            
            if output_format == OutputFormat.JSON:
                return json.dumps(output_data, indent=2, default=str)
            else:  # CSV
                # For CSV, we'll create a single table with all data
                all_rows = []
                for table_name, table_data in output_data.items():
                    if "data" in table_data:
                        for row in table_data["data"]:
                            row_with_table = {"table": table_name, **row}
                            all_rows.append(row_with_table)
                
                if not all_rows:
                    return "No data to export to CSV"
                
                output = []
                writer = csv.DictWriter(
                    output,
                    fieldnames=all_rows[0].keys(),
                    quoting=csv.QUOTE_NONNUMERIC
                )
                writer.writeheader()
                writer.writerows(all_rows)
                return output.getvalue()
        
        else:  # Text-based output (grid or plain)
            output = []
            for table_name, table_info in results.items():
                table_output = []
                
                # Table header
                table_output.append(f"\n{Fore.CYAN}=== {table_name} ({table_info.row_count} rows) ==={Style.RESET_ALL}")
                
                # Schema
                if show_schema and table_info.schema:
                    schema_headers = ["Column", "Type", "Nullable"]
                    schema_data = [
                        [col["name"], col["type"], "NO" if col["notnull"] else "YES"]
                        for col in table_info.schema
                    ]
                    
                    table_output.append("\nSchema:")
                    table_output.append(
                        tabulate(
                            schema_data,
                            headers=schema_headers,
                            tablefmt=output_format
                        )
                    )
                
                # Data
                if show_data and table_info.data:
                    columns = [col["name"] for col in table_info.schema]
                    table_output.append(f"\nData (first {min(limit, len(table_info.data))} of {table_info.row_count} rows):")
                    
                    if table_info.data:
                        table_output.append(
                            tabulate(
                                table_info.data[:limit],
                                headers=columns,
                                tablefmt=output_format
                            )
                        )
                    else:
                        table_output.append("  No data in this table.")
                
                output.append("\n".join(table_output))
            
            return "\n\n".join(output)
    
    @staticmethod
    def _write_output(output: str, output_file: str, output_format: OutputFormat) -> None:
        """Write the output to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output written to {output_file}")
        except IOError as e:
            print(f"{Fore.RED}Error writing to file {output_file}: {e}{Style.RESET_ALL}")


def main() -> None:
    """Command-line interface for the database inspector."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inspect SQLite database schema and data.')
    parser.add_argument('db_path', help='Path to the SQLite database file')
    parser.add_argument('--table', '-t', default='%',
                      help='Filter tables by name (SQL LIKE pattern)')
    parser.add_argument('--limit', '-l', type=int, default=10,
                      help='Maximum number of rows to show per table')
    parser.add_argument('--format', '-f', default='grid',
                      choices=['grid', 'plain', 'json', 'csv'],
                      help='Output format')
    parser.add_argument('--no-schema', action='store_false', dest='show_schema',
                      help='Do not show table schema')
    parser.add_argument('--no-data', action='store_false', dest='show_data',
                      help='Do not show table data')
    parser.add_argument('--output', '-o',
                      help='Output file (default: print to console)')
    
    args = parser.parse_args()
    
    try:
        inspector = DatabaseInspector(args.db_path)
        with inspector:
            inspector.inspect(
                table_filter=args.table,
                limit=args.limit,
                output_format=args.format,
                show_schema=args.show_schema,
                show_data=args.show_data,
                output_file=args.output
            )
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
