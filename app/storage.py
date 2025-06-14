import sqlite3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from threading import local

logger = logging.getLogger(__name__)
_thread_local = local()

class KnowledgeStorage:
    def __init__(self, db_path="knowledge.db"):
        self.db_path = db_path
        self.metrics = {
            'query_times': [],
            'insert_times': [],
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_operations': 0
        }
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Thread-local connection with connection pooling"""
        if not hasattr(_thread_local, "conn"):
            _thread_local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10,
                isolation_level=None
            )
            _thread_local.conn.execute("PRAGMA journal_mode=WAL")
        return _thread_local.conn

    def _init_db(self):
        """Initialize database with optimized schema"""
        conn = self._get_conn()
        
        # Main posts table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            source TEXT CHECK(source IN ('discourse', 'docsify')),
            external_id TEXT,
            title TEXT,
            content TEXT,
            url TEXT UNIQUE,
            is_solution BOOLEAN DEFAULT 0,
            created_at TEXT,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            search_text TEXT GENERATED ALWAYS AS (lower(title || ' ' || content)) VIRTUAL
        )""")
        
        # Cache table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            source TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )""")
        
        # Indexes
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_posts_source_updated 
        ON posts(source, last_updated)
        """)
        
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_expiry 
        ON cache(expires_at)
        """)
        
        conn.commit()

    def _log_metric(self, metric_type: str, value: float = 1):
        """Store performance metrics with timestamp"""
        if metric_type.endswith('_times'):
            self.metrics.setdefault(metric_type, []).append({
                'timestamp': datetime.now().isoformat(),
                'duration': value
            })
            # Keep only last 100 measurements
            if len(self.metrics[metric_type]) > 100:
                self.metrics[metric_type].pop(0)
        else:
            self.metrics[metric_type] = self.metrics.get(metric_type, 0) + value

    def get_performance_stats(self) -> Dict:
        """Calculate aggregated performance metrics"""
        return {
            'cache': {
                'hit_rate': self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses']),
                'operations': self.metrics['cache_operations']
            },
            'query_time_avg': sum(t['duration'] for t in self.metrics['query_times']) / max(1, len(self.metrics['query_times'])),
            'insert_time_avg': sum(t['duration'] for t in self.metrics['insert_times']) / max(1, len(self.metrics['insert_times']))
        }

    def save_posts(self, posts: List[Dict]) -> Tuple[int, float]:
        """Optimized bulk insert"""
        start = time.perf_counter()
        conn = self._get_conn()
        
        try:
            conn.executemany("""
            INSERT OR REPLACE INTO posts 
            (source, external_id, title, content, url, is_solution, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    post["source"],
                    post["url"].split("/")[-1],
                    post.get("title", ""),
                    post["content"],
                    post["url"],
                    post.get("is_solution", False),
                    post.get("date", datetime.now().isoformat())
                )
                for post in posts
            ])
            conn.commit()
            duration = time.perf_counter() - start
            self._log_metric('insert_times', duration)
            return len(posts), duration
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Batch insert failed: {e}")
            return 0, 0

    def get_recent_posts(self, source: str, max_age_hours: int = 24) -> Tuple[List[Dict], bool]:
        """Returns (posts, from_cache)"""
        start = time.perf_counter()
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM posts 
            WHERE source = ? 
            AND datetime(last_updated) > datetime('now', ?)
            """, (source, f"-{max_age_hours} hours"))
            
            rows = cursor.fetchall()
            duration = time.perf_counter() - start
            self._log_metric('query_times', duration)
            
            if rows:
                self._log_metric('cache_hits')
                return [dict(row) for row in rows], True
            
            self._log_metric('cache_misses')
            return [], False
            
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {e}")
            return [], False

    def get_cached_data(self, source: str, ttl_hours: int = 6) -> Optional[dict]:
        """Retrieve cached data if it exists and is fresh."""
        try:
            row = self._get_conn().execute(
                "SELECT data FROM cache WHERE source = ? AND expires_at > ?",
                (source, datetime.now().isoformat())
            ).fetchone()
            
            self._log_metric('cache_operations')
            return json.loads(row[0]) if row else None
            
        except sqlite3.Error as e:
            logger.error(f"Cache read failed: {e}")
            return None

    def set_cached_data(self, source: str, data: dict, ttl_hours: int = 6) -> bool:
        """Cache data with a time-to-live (TTL). Returns success status."""
        try:
            expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            self._get_conn().execute(
                "INSERT OR REPLACE INTO cache (source, data, expires_at) VALUES (?, ?, ?)",
                (source, json.dumps(data), expires_at)
            )
            self._get_conn().commit()
            self._log_metric('cache_operations')
            return True
        except sqlite3.Error as e:
            logger.error(f"Cache write failed: {e}")
            return False