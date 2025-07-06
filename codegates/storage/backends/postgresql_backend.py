"""
PostgreSQL Storage Backend

Implements persistent storage using PostgreSQL database for enterprise deployments.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncpg
from urllib.parse import urlparse

from .base import BaseStorageBackend
from ..models import ScanResultModel, GateResultModel, StorageConfig


class PostgreSQLBackend(BaseStorageBackend):
    """PostgreSQL storage backend"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.database_url = config.database_url
        self.pool = None
        
        if not self.database_url:
            raise ValueError("PostgreSQL backend requires database_url in configuration")
    
    async def initialize(self) -> bool:
        """Initialize PostgreSQL connection pool"""
        try:
            # Parse connection parameters
            parsed = urlparse(self.database_url)
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                min_size=1,
                max_size=self.config.max_connections,
                command_timeout=self.config.connection_timeout
            )
            
            # Create tables
            await self._create_tables()
            
            # Create indexes if enabled
            if self.config.enable_indexing:
                await self._create_indexes()
            
            self._initialized = True
            print(f"✅ PostgreSQL storage initialized: {parsed.hostname}:{parsed.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize PostgreSQL storage: {e}")
            return False
    
    async def close(self):
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
        self._initialized = False
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Main scan results table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scan_results (
                    scan_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    repository_url TEXT,
                    branch TEXT,
                    github_token_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    message TEXT,
                    error TEXT,
                    report_url TEXT,
                    report_file TEXT,
                    llm_enhanced BOOLEAN DEFAULT FALSE,
                    total_files INTEGER DEFAULT 0,
                    total_lines INTEGER DEFAULT 0,
                    languages_detected JSONB,
                    checkout_method TEXT,
                    jira_result JSONB,
                    comments JSONB,
                    recommendations JSONB
                )
            ''')
            
            # Gate results table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS gate_results (
                    id SERIAL PRIMARY KEY,
                    scan_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    details JSONB,
                    expected INTEGER,
                    found INTEGER,
                    coverage REAL,
                    quality_score REAL,
                    matches JSONB,
                    FOREIGN KEY (scan_id) REFERENCES scan_results (scan_id) ON DELETE CASCADE
                )
            ''')
    
    async def _create_indexes(self):
        """Create database indexes"""
        async with self.pool.acquire() as conn:
            indexes = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scan_results_status ON scan_results(status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scan_results_created_at ON scan_results(created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scan_results_repository ON scan_results(repository_url)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gate_results_scan_id ON gate_results(scan_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gate_results_name ON gate_results(name)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gate_results_status ON gate_results(status)",
                # JSONB indexes for better query performance
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scan_results_languages ON scan_results USING GIN (languages_detected)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gate_results_matches ON gate_results USING GIN (matches)"
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    print(f"⚠️ Failed to create index: {e}")
    
    async def save_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Save a scan result to PostgreSQL"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Insert or update main scan result
                    await conn.execute('''
                        INSERT INTO scan_results (
                            scan_id, status, score, repository_url, branch, github_token_used,
                            created_at, updated_at, completed_at, message, error, report_url,
                            report_file, llm_enhanced, total_files, total_lines, languages_detected,
                            checkout_method, jira_result, comments, recommendations
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                        ON CONFLICT (scan_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            score = EXCLUDED.score,
                            repository_url = EXCLUDED.repository_url,
                            branch = EXCLUDED.branch,
                            github_token_used = EXCLUDED.github_token_used,
                            updated_at = EXCLUDED.updated_at,
                            completed_at = EXCLUDED.completed_at,
                            message = EXCLUDED.message,
                            error = EXCLUDED.error,
                            report_url = EXCLUDED.report_url,
                            report_file = EXCLUDED.report_file,
                            llm_enhanced = EXCLUDED.llm_enhanced,
                            total_files = EXCLUDED.total_files,
                            total_lines = EXCLUDED.total_lines,
                            languages_detected = EXCLUDED.languages_detected,
                            checkout_method = EXCLUDED.checkout_method,
                            jira_result = EXCLUDED.jira_result,
                            comments = EXCLUDED.comments,
                            recommendations = EXCLUDED.recommendations
                    ''', 
                        scan_result.scan_id,
                        scan_result.status,
                        scan_result.score,
                        scan_result.repository_url,
                        scan_result.branch,
                        scan_result.github_token_used,
                        scan_result.created_at,
                        scan_result.updated_at,
                        scan_result.completed_at,
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
                    )
                    
                    # Delete existing gate results
                    await conn.execute('DELETE FROM gate_results WHERE scan_id = $1', scan_result.scan_id)
                    
                    # Insert gate results
                    for gate in scan_result.gates:
                        await conn.execute('''
                            INSERT INTO gate_results (
                                scan_id, name, status, score, details, expected, found,
                                coverage, quality_score, matches
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ''',
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
                        )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save scan result {scan_result.scan_id}: {e}")
            return False
    
    async def get_scan_result(self, scan_id: str) -> Optional[ScanResultModel]:
        """Get a scan result by ID"""
        try:
            async with self.pool.acquire() as conn:
                # Get main scan result
                row = await conn.fetchrow(
                    'SELECT * FROM scan_results WHERE scan_id = $1',
                    scan_id
                )
                
                if not row:
                    return None
                
                # Convert row to dict
                scan_data = dict(row)
                
                # Parse JSON fields
                if scan_data['languages_detected']:
                    scan_data['languages_detected'] = json.loads(scan_data['languages_detected'])
                if scan_data['recommendations']:
                    scan_data['recommendations'] = json.loads(scan_data['recommendations'])
                if scan_data['comments']:
                    scan_data['comments'] = json.loads(scan_data['comments'])
                if scan_data['jira_result']:
                    scan_data['jira_result'] = json.loads(scan_data['jira_result'])
                
                # Get gate results
                gate_rows = await conn.fetch(
                    'SELECT * FROM gate_results WHERE scan_id = $1 ORDER BY id',
                    scan_id
                )
                
                gates = []
                for gate_row in gate_rows:
                    gate_data = dict(gate_row)
                    
                    # Parse JSON fields
                    if gate_data['details']:
                        gate_data['details'] = json.loads(gate_data['details'])
                    if gate_data['matches']:
                        gate_data['matches'] = json.loads(gate_data['matches'])
                    
                    gates.append(GateResultModel.from_dict(gate_data))
                
                # Create scan result model
                scan_data['gates'] = gates
                return ScanResultModel.from_dict(scan_data)
                
        except Exception as e:
            print(f"❌ Failed to get scan result {scan_id}: {e}")
            return None
    
    async def update_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Update an existing scan result"""
        return await self.save_scan_result(scan_result)
    
    async def delete_scan_result(self, scan_id: str) -> bool:
        """Delete a scan result"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('DELETE FROM scan_results WHERE scan_id = $1', scan_id)
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
            async with self.pool.acquire() as conn:
                # Build query
                query = "SELECT * FROM scan_results WHERE 1=1"
                params = []
                param_count = 0
                
                if status_filter:
                    param_count += 1
                    query += f" AND status = ${param_count}"
                    params.append(status_filter)
                
                if repository_filter:
                    param_count += 1
                    query += f" AND repository_url ILIKE ${param_count}"
                    params.append(f"%{repository_filter}%")
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    param_count += 1
                    query += f" LIMIT ${param_count}"
                    params.append(limit)
                
                if offset:
                    param_count += 1
                    query += f" OFFSET ${param_count}"
                    params.append(offset)
                
                # Execute query
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    scan_data = dict(row)
                    
                    # Parse JSON fields
                    if scan_data['languages_detected']:
                        scan_data['languages_detected'] = json.loads(scan_data['languages_detected'])
                    if scan_data['recommendations']:
                        scan_data['recommendations'] = json.loads(scan_data['recommendations'])
                    if scan_data['comments']:
                        scan_data['comments'] = json.loads(scan_data['comments'])
                    if scan_data['jira_result']:
                        scan_data['jira_result'] = json.loads(scan_data['jira_result'])
                    
                    # Get gate results for this scan
                    gate_rows = await conn.fetch(
                        'SELECT * FROM gate_results WHERE scan_id = $1 ORDER BY id',
                        scan_data['scan_id']
                    )
                    
                    gates = []
                    for gate_row in gate_rows:
                        gate_data = dict(gate_row)
                        
                        # Parse JSON fields
                        if gate_data['details']:
                            gate_data['details'] = json.loads(gate_data['details'])
                        if gate_data['matches']:
                            gate_data['matches'] = json.loads(gate_data['matches'])
                        
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
            async with self.pool.acquire() as conn:
                query = "SELECT COUNT(*) FROM scan_results WHERE 1=1"
                params = []
                param_count = 0
                
                if status_filter:
                    param_count += 1
                    query += f" AND status = ${param_count}"
                    params.append(status_filter)
                
                if repository_filter:
                    param_count += 1
                    query += f" AND repository_url ILIKE ${param_count}"
                    params.append(f"%{repository_filter}%")
                
                row = await conn.fetchrow(query, *params)
                return row[0] if row else 0
                
        except Exception as e:
            print(f"❌ Failed to count scan results: {e}")
            return 0
    
    async def cleanup_old_results(self, older_than: datetime) -> int:
        """Clean up old scan results"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    'DELETE FROM scan_results WHERE created_at < $1',
                    older_than
                )
                # Extract number from result like "DELETE 5"
                return int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
        except Exception as e:
            print(f"❌ Failed to cleanup old results: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Get total counts
                total_scans = await conn.fetchval('SELECT COUNT(*) FROM scan_results')
                total_gates = await conn.fetchval('SELECT COUNT(*) FROM gate_results')
                
                # Get status breakdown
                status_rows = await conn.fetch(
                    'SELECT status, COUNT(*) FROM scan_results GROUP BY status'
                )
                status_counts = {row['status']: row['count'] for row in status_rows}
                
                # Get database size (PostgreSQL specific)
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database())"
                )
                
                return {
                    'backend': 'postgresql',
                    'database_url': self.database_url.split('@')[1] if '@' in self.database_url else self.database_url,  # Hide credentials
                    'database_size_bytes': db_size,
                    'total_scans': total_scans,
                    'total_gates': total_gates,
                    'status_counts': status_counts,
                    'initialized': self._initialized,
                    'pool_size': self.pool.get_size() if self.pool else 0,
                    'pool_max_size': self.config.max_connections
                }
                
        except Exception as e:
            print(f"❌ Failed to get storage stats: {e}")
            return {
                'backend': 'postgresql',
                'error': str(e),
                'initialized': self._initialized
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL backend health"""
        try:
            if not self._initialized or not self.pool:
                return {
                    'healthy': False,
                    'message': 'Backend not initialized'
                }
            
            # Try a simple query
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            
            return {
                'healthy': True,
                'message': 'PostgreSQL backend is healthy',
                'database_url': self.database_url.split('@')[1] if '@' in self.database_url else self.database_url,  # Hide credentials
                'pool_size': self.pool.get_size(),
                'pool_max_size': self.config.max_connections
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'message': f'PostgreSQL health check failed: {e}'
            } 