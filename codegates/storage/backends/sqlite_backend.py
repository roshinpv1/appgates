"""
SQLite Storage Backend

Implements persistent storage using SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiosqlite

from .base import BaseStorageBackend
from ..models import ScanResultModel, GateResultModel, StorageConfig


class SQLiteBackend(BaseStorageBackend):
    """SQLite storage backend"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.db_path = config.database_path or './data/codegates.db'
        self.connection = None
    
    async def initialize(self) -> bool:
        """Initialize SQLite database"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            self.connection = await aiosqlite.connect(self.db_path)
            
            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await self._create_tables()
            
            # Create indexes if enabled
            if self.config.enable_indexing:
                await self._create_indexes()
            
            self._initialized = True
            print(f"✅ SQLite storage initialized: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize SQLite storage: {e}")
            return False
    
    async def close(self):
        """Close SQLite connection"""
        if self.connection:
            await self.connection.close()
            self.connection = None
        self._initialized = False
    
    async def _create_tables(self):
        """Create database tables"""
        # Main scan results table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                scan_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                score REAL NOT NULL,
                repository_url TEXT,
                branch TEXT,
                github_token_used BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                message TEXT,
                error TEXT,
                report_url TEXT,
                report_file TEXT,
                llm_enhanced BOOLEAN DEFAULT FALSE,
                total_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                languages_detected TEXT,  -- JSON array
                checkout_method TEXT,
                jira_result TEXT,  -- JSON object
                comments TEXT,  -- JSON object
                recommendations TEXT  -- JSON array
            )
        ''')
        
        # Gate results table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS gate_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL NOT NULL,
                details TEXT,  -- JSON array
                expected INTEGER,
                found INTEGER,
                coverage REAL,
                quality_score REAL,
                matches TEXT,  -- JSON array
                FOREIGN KEY (scan_id) REFERENCES scan_results (scan_id) ON DELETE CASCADE
            )
        ''')
        
        await self.connection.commit()
    
    async def _create_indexes(self):
        """Create database indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scan_results_status ON scan_results(status)",
            "CREATE INDEX IF NOT EXISTS idx_scan_results_created_at ON scan_results(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_scan_results_repository ON scan_results(repository_url)",
            "CREATE INDEX IF NOT EXISTS idx_gate_results_scan_id ON gate_results(scan_id)",
            "CREATE INDEX IF NOT EXISTS idx_gate_results_name ON gate_results(name)",
            "CREATE INDEX IF NOT EXISTS idx_gate_results_status ON gate_results(status)"
        ]
        
        for index_sql in indexes:
            await self.connection.execute(index_sql)
        
        await self.connection.commit()
    
    async def save_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Save a scan result to SQLite"""
        try:
            # Insert main scan result
            await self.connection.execute('''
                INSERT OR REPLACE INTO scan_results (
                    scan_id, status, score, repository_url, branch, github_token_used,
                    created_at, updated_at, completed_at, message, error, report_url,
                    report_file, llm_enhanced, total_files, total_lines, languages_detected,
                    checkout_method, jira_result, comments, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_result.scan_id,
                scan_result.status,
                scan_result.score,
                scan_result.repository_url,
                scan_result.branch,
                scan_result.github_token_used,
                scan_result.created_at.isoformat(),
                scan_result.updated_at.isoformat(),
                scan_result.completed_at.isoformat() if scan_result.completed_at else None,
                scan_result.message,
                scan_result.error,
                scan_result.report_url,
                scan_result.report_file,
                scan_result.llm_enhanced,
                scan_result.total_files,
                scan_result.total_lines,
                json.dumps(scan_result.languages_detected),
                scan_result.checkout_method,
                json.dumps(scan_result.jira_result) if scan_result.jira_result else None,
                json.dumps(scan_result.comments),
                json.dumps(scan_result.recommendations)
            ))
            
            # Delete existing gate results
            await self.connection.execute(
                'DELETE FROM gate_results WHERE scan_id = ?',
                (scan_result.scan_id,)
            )
            
            # Insert gate results
            for gate in scan_result.gates:
                await self.connection.execute('''
                    INSERT INTO gate_results (
                        scan_id, name, status, score, details, expected, found,
                        coverage, quality_score, matches
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_result.scan_id,
                    gate.name,
                    gate.status,
                    gate.score,
                    json.dumps(gate.details),
                    gate.expected,
                    gate.found,
                    gate.coverage,
                    gate.quality_score,
                    json.dumps(gate.matches)
                ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to save scan result {scan_result.scan_id}: {e}")
            return False
    
    async def get_scan_result(self, scan_id: str) -> Optional[ScanResultModel]:
        """Get a scan result by ID"""
        try:
            # Get main scan result
            cursor = await self.connection.execute(
                'SELECT * FROM scan_results WHERE scan_id = ?',
                (scan_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dict
            columns = [description[0] for description in cursor.description]
            scan_data = dict(zip(columns, row))
            
            # Parse JSON fields
            scan_data['languages_detected'] = json.loads(scan_data['languages_detected'] or '[]')
            scan_data['recommendations'] = json.loads(scan_data['recommendations'] or '[]')
            scan_data['comments'] = json.loads(scan_data['comments'] or '{}')
            if scan_data['jira_result']:
                scan_data['jira_result'] = json.loads(scan_data['jira_result'])
            
            # Get gate results
            cursor = await self.connection.execute(
                'SELECT * FROM gate_results WHERE scan_id = ? ORDER BY id',
                (scan_id,)
            )
            gate_rows = await cursor.fetchall()
            
            gates = []
            for gate_row in gate_rows:
                gate_columns = [description[0] for description in cursor.description]
                gate_data = dict(zip(gate_columns, gate_row))
                
                # Parse JSON fields
                gate_data['details'] = json.loads(gate_data['details'] or '[]')
                gate_data['matches'] = json.loads(gate_data['matches'] or '[]')
                
                gates.append(GateResultModel.from_dict(gate_data))
            
            # Create scan result model
            scan_data['gates'] = gates
            return ScanResultModel.from_dict(scan_data)
            
        except Exception as e:
            print(f"❌ Failed to get scan result {scan_id}: {e}")
            return None
    
    async def update_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Update an existing scan result"""
        # For SQLite, we can use the same save method with INSERT OR REPLACE
        return await self.save_scan_result(scan_result)
    
    async def delete_scan_result(self, scan_id: str) -> bool:
        """Delete a scan result"""
        try:
            await self.connection.execute(
                'DELETE FROM scan_results WHERE scan_id = ?',
                (scan_id,)
            )
            await self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete scan result {scan_id}: {e}")
            return False
    
    async def list_scan_results(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> List[ScanResultModel]:
        """List scan results with optional filtering"""
        try:
            # Build query
            query = "SELECT * FROM scan_results WHERE 1=1"
            params = []
            
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            
            if repository_filter:
                query += " AND repository_url LIKE ?"
                params.append(f"%{repository_filter}%")
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
            
            # Execute query
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                columns = [description[0] for description in cursor.description]
                scan_data = dict(zip(columns, row))
                
                # Parse JSON fields
                scan_data['languages_detected'] = json.loads(scan_data['languages_detected'] or '[]')
                scan_data['recommendations'] = json.loads(scan_data['recommendations'] or '[]')
                scan_data['comments'] = json.loads(scan_data['comments'] or '{}')
                if scan_data['jira_result']:
                    scan_data['jira_result'] = json.loads(scan_data['jira_result'])
                
                # Get gate results for this scan
                gate_cursor = await self.connection.execute(
                    'SELECT * FROM gate_results WHERE scan_id = ? ORDER BY id',
                    (scan_data['scan_id'],)
                )
                gate_rows = await gate_cursor.fetchall()
                
                gates = []
                for gate_row in gate_rows:
                    gate_columns = [description[0] for description in gate_cursor.description]
                    gate_data = dict(zip(gate_columns, gate_row))
                    
                    # Parse JSON fields
                    gate_data['details'] = json.loads(gate_data['details'] or '[]')
                    gate_data['matches'] = json.loads(gate_data['matches'] or '[]')
                    
                    gates.append(GateResultModel.from_dict(gate_data))
                
                scan_data['gates'] = gates
                results.append(ScanResultModel.from_dict(scan_data))
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to list scan results: {e}")
            return []
    
    async def count_scan_results(
        self,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> int:
        """Count scan results with optional filtering"""
        try:
            query = "SELECT COUNT(*) FROM scan_results WHERE 1=1"
            params = []
            
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            
            if repository_filter:
                query += " AND repository_url LIKE ?"
                params.append(f"%{repository_filter}%")
            
            cursor = await self.connection.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0
            
        except Exception as e:
            print(f"❌ Failed to count scan results: {e}")
            return 0
    
    async def cleanup_old_results(self, older_than: datetime) -> int:
        """Clean up old scan results"""
        try:
            cursor = await self.connection.execute(
                'DELETE FROM scan_results WHERE created_at < ?',
                (older_than.isoformat(),)
            )
            await self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            print(f"❌ Failed to cleanup old results: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            # Get total counts
            cursor = await self.connection.execute('SELECT COUNT(*) FROM scan_results')
            total_scans = (await cursor.fetchone())[0]
            
            cursor = await self.connection.execute('SELECT COUNT(*) FROM gate_results')
            total_gates = (await cursor.fetchone())[0]
            
            # Get status breakdown
            cursor = await self.connection.execute(
                'SELECT status, COUNT(*) FROM scan_results GROUP BY status'
            )
            status_counts = dict(await cursor.fetchall())
            
            # Get database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'backend': 'sqlite',
                'database_path': self.db_path,
                'database_size_bytes': db_size,
                'total_scans': total_scans,
                'total_gates': total_gates,
                'status_counts': status_counts,
                'initialized': self._initialized
            }
            
        except Exception as e:
            print(f"❌ Failed to get storage stats: {e}")
            return {
                'backend': 'sqlite',
                'error': str(e),
                'initialized': self._initialized
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SQLite backend health"""
        try:
            if not self._initialized or not self.connection:
                return {
                    'healthy': False,
                    'message': 'Backend not initialized'
                }
            
            # Try a simple query
            cursor = await self.connection.execute('SELECT 1')
            await cursor.fetchone()
            
            return {
                'healthy': True,
                'message': 'SQLite backend is healthy',
                'database_path': self.db_path,
                'database_exists': os.path.exists(self.db_path)
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'message': f'SQLite health check failed: {e}'
            } 