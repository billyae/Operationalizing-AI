"""
Unit tests for metrics module.

This module tests database operations for recording and fetching invocation metrics,
including database initialization, thread safety, and connection management.
"""

import unittest
import tempfile
import os
import sqlite3
import time
import threading
from unittest.mock import patch, MagicMock
import sys
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from metrics import (
    create_db_directory, initialize_db, record_invocation, 
    fetch_all_invocations, _get_connection, METRICS_DB_PATH
)


class TestCreateDbDirectory(unittest.TestCase):
    """Test database directory creation function."""
    
    def test_create_db_directory_new_directory(self):
        """Test creating a new database directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, 'new_dir', 'test.db')
            
            result = create_db_directory(test_db_path)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(os.path.dirname(test_db_path)))
    
    def test_create_db_directory_existing_directory(self):
        """Test creating database directory when it already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, 'test.db')
            
            result = create_db_directory(test_db_path)
            
            self.assertTrue(result)
    
    @patch('metrics.os.makedirs')
    def test_create_db_directory_permission_error(self, mock_makedirs):
        """Test handling permission error when creating directory."""
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        test_db_path = "/root/restricted/test.db"
        
        result = create_db_directory(test_db_path)
        
        self.assertFalse(result)


class TestDatabaseOperations(unittest.TestCase):
    """Test database initialization and operations."""
    
    def setUp(self):
        """Set up test database before each test."""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        
        # Patch the database path
        self.db_patcher = patch('metrics.METRICS_DB_PATH', self.test_db_path)
        self.db_patcher.start()
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.db_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_initialize_db(self):
        """Test database initialization."""
        initialize_db()
        
        # Check that database file exists
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Check that invocations table exists with correct structure
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invocations';")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'invocations')
        
        # Check table structure
        cursor.execute("PRAGMA table_info(invocations);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = ['id', 'timestamp', 'model_id', 'input_tokens', 'output_tokens', 'response_time']
        for col in expected_columns:
            self.assertIn(col, column_names)
        
        conn.close()
    
    def test_get_connection(self):
        """Test database connection function."""
        initialize_db()
        
        conn = _get_connection()
        
        self.assertIsNotNone(conn)
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # Test that connection works
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invocations;")
        result = cursor.fetchone()
        self.assertEqual(result[0], 0)
        
        conn.close()
    
    def test_record_invocation_success(self):
        """Test successful invocation recording."""
        initialize_db()
        
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        input_tokens = 100
        output_tokens = 200
        response_time = 1.5
        
        result = record_invocation(model_id, input_tokens, output_tokens, response_time)
        
        self.assertTrue(result)
        
        # Verify record was inserted
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invocations ORDER BY id DESC LIMIT 1;")
        record = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(record)
        self.assertEqual(record['model_id'], model_id)
        self.assertEqual(record['input_tokens'], input_tokens)
        self.assertEqual(record['output_tokens'], output_tokens)
        self.assertEqual(record['response_time'], response_time)
        self.assertIsNotNone(record['timestamp'])
    
    def test_record_invocation_with_optional_parameters(self):
        """Test recording invocation with None values for optional parameters."""
        initialize_db()
        
        model_id = "test-model"
        
        result = record_invocation(model_id, None, None, None)
        
        self.assertTrue(result)
        
        # Verify record was inserted with None values
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invocations ORDER BY id DESC LIMIT 1;")
        record = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(record)
        self.assertEqual(record['model_id'], model_id)
        self.assertIsNone(record['input_tokens'])
        self.assertIsNone(record['output_tokens'])
        self.assertIsNone(record['response_time'])
    
    @patch('metrics._get_connection')
    def test_record_invocation_database_error(self, mock_get_connection):
        """Test handling database error during invocation recording."""
        mock_get_connection.side_effect = sqlite3.Error("Database error")
        
        result = record_invocation("test-model", 100, 200, 1.5)
        
        self.assertFalse(result)
    
    def test_fetch_all_invocations_empty(self):
        """Test fetching invocations from empty database."""
        initialize_db()
        
        invocations = fetch_all_invocations()
        
        self.assertEqual(len(invocations), 0)
    
    def test_fetch_all_invocations_with_data(self):
        """Test fetching invocations with data in database."""
        initialize_db()
        
        # Insert test data
        test_records = [
            ("model-1", 100, 150, 1.2),
            ("model-2", 200, 250, 2.1),
            ("model-3", 50, 75, 0.8)
        ]
        
        for model_id, input_tokens, output_tokens, response_time in test_records:
            record_invocation(model_id, input_tokens, output_tokens, response_time)
        
        invocations = fetch_all_invocations()
        
        self.assertEqual(len(invocations), 3)
        
        # Check that records are returned in correct format
        for invocation in invocations:
            self.assertIn('id', invocation)
            self.assertIn('timestamp', invocation)
            self.assertIn('model_id', invocation)
            self.assertIn('input_tokens', invocation)
            self.assertIn('output_tokens', invocation)
            self.assertIn('response_time', invocation)
    
    def test_fetch_all_invocations_ordering(self):
        """Test that invocations are fetched in descending order by timestamp."""
        initialize_db()
        
        # Insert records with small delays to ensure different timestamps
        record_invocation("model-1", 100, 150, 1.0)
        time.sleep(0.001)
        record_invocation("model-2", 200, 250, 2.0)
        time.sleep(0.001)
        record_invocation("model-3", 300, 350, 3.0)
        
        invocations = fetch_all_invocations()
        
        self.assertEqual(len(invocations), 3)
        
        # Check that records are in descending timestamp order (most recent first)
        timestamps = [inv['timestamp'] for inv in invocations]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
        
        # Check that the most recent record is first
        self.assertEqual(invocations[0]['model_id'], "model-3")
    
    @patch('metrics._get_connection')
    def test_fetch_all_invocations_database_error(self, mock_get_connection):
        """Test handling database error during invocation fetching."""
        mock_get_connection.side_effect = sqlite3.Error("Database error")
        
        invocations = fetch_all_invocations()
        
        self.assertEqual(len(invocations), 0)


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of database operations."""
    
    def setUp(self):
        """Set up test database before each test."""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        
        # Patch the database path
        self.db_patcher = patch('metrics.METRICS_DB_PATH', self.test_db_path)
        self.db_patcher.start()
        
        initialize_db()
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.db_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_concurrent_record_invocation(self):
        """Test concurrent invocation recording from multiple threads."""
        num_threads = 10
        records_per_thread = 5
        threads = []
        results = []
        
        def record_multiple():
            thread_results = []
            for i in range(records_per_thread):
                result = record_invocation(f"model-{threading.current_thread().ident}-{i}", 
                                         100 + i, 200 + i, 1.0 + i * 0.1)
                thread_results.append(result)
            results.extend(thread_results)
        
        # Create and start threads
        for _ in range(num_threads):
            thread = threading.Thread(target=record_multiple)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all records were successfully inserted
        self.assertEqual(len(results), num_threads * records_per_thread)
        self.assertTrue(all(results))
        
        # Verify total number of records in database
        invocations = fetch_all_invocations()
        self.assertEqual(len(invocations), num_threads * records_per_thread)
    
    def test_concurrent_read_write(self):
        """Test concurrent reading and writing operations."""
        write_threads = []
        read_threads = []
        write_results = []
        read_results = []
        
        def write_records():
            for i in range(5):
                result = record_invocation(f"concurrent-model-{i}", 100, 200, 1.0)
                write_results.append(result)
        
        def read_records():
            for _ in range(3):
                invocations = fetch_all_invocations()
                read_results.append(len(invocations))
                time.sleep(0.01)  # Small delay to allow interleaving
        
        # Start write threads
        for _ in range(3):
            thread = threading.Thread(target=write_records)
            write_threads.append(thread)
            thread.start()
        
        # Start read threads
        for _ in range(2):
            thread = threading.Thread(target=read_records)
            read_threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in write_threads + read_threads:
            thread.join()
        
        # Check that writes were successful
        self.assertTrue(all(write_results))
        
        # Check that reads returned valid results
        self.assertTrue(all(count >= 0 for count in read_results))
        
        # Final verification
        final_invocations = fetch_all_invocations()
        self.assertEqual(len(final_invocations), 15)  # 3 threads * 5 records each


if __name__ == '__main__':
    unittest.main() 