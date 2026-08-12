# Database Optimization Strategies

This document outlines database optimization strategies for the Quality Deviation Risk Monitor.

## Current State (SQLite)

- **Engine**: SQLite3
- **File**: `data/deviations.db`  
- **Records**: 30 synthetic deviations
- **Status**: Suitable for portfolio demo and small-scale use

## Optimization 1: Add Database Indexes

For faster queries on commonly filtered columns:

```sql
-- Add indexes for frequently used filters
CREATE INDEX idx_deviations_severity ON deviations(severity);
CREATE INDEX idx_deviations_risk_level ON deviations(risk_level);
CREATE INDEX idx_deviations_due_date ON deviations(due_date);
CREATE INDEX idx_deviations_review_status ON deviations(review_status);
CREATE INDEX idx_deviations_investigation_owner ON deviations(investigation_owner);

-- Composite indexes for common query patterns
CREATE INDEX idx_severity_due_date ON deviations(severity, due_date);
CREATE INDEX idx_risk_review ON deviations(risk_level, review_status);
```

### Implementation

```python
# app/database.py
def add_indexes(database_file: Path = DATABASE_FILE) -> None:
    """Add performance indexes to database."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_deviations_severity ON deviations(severity)",
        "CREATE INDEX IF NOT EXISTS idx_deviations_due_date ON deviations(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_deviations_review_status ON deviations(review_status)",
        "CREATE INDEX IF NOT EXISTS idx_severity_due_date ON deviations(severity, due_date)",
    ]
    
    with connection(database_file) as conn:
        for index in indexes:
            conn.execute(index)
        conn.commit()
        logger.info(f"Added {len(indexes)} indexes to database")
```

## Optimization 2: Use Prepared Statements

Already implemented in current version - reduces SQL injection risk and improves performance.

## Optimization 3: Connection Pooling

For production with concurrent requests:

```python
# Install: pip install sqlalchemy

from sqlalchemy import create_engine

# Create engine with connection pool
engine = create_engine(
    'sqlite:///data/deviations.db',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,  # For SQLite in-memory
    # OR for file-based with pooling:
    # pool_size=10,
    # max_overflow=20,
    # pool_recycle=3600
)
```

## Optimization 4: Query Optimization

Current queries are simple, but for scaling:

```python
# Example: Use EXPLAIN QUERY PLAN to analyze
EXPLAIN QUERY PLAN SELECT * FROM deviations WHERE risk_level = 'High';

# Results will show if index is being used
```

## Optimization 5: Database Migrations

Use Alembic for schema versioning:

```bash
# Install
pip install alembic

# Initialize
alembic init migrations

# Create migration
alembic revision -m "add_indexes"

# Apply migration
alembic upgrade head
```

### Example Migration

```python
# migrations/versions/001_add_indexes.py
def upgrade():
    op.create_index('idx_severity', 'deviations', ['severity'])
    op.create_index('idx_due_date', 'deviations', ['due_date'])

def downgrade():
    op.drop_index('idx_severity', 'deviations')
    op.drop_index('idx_due_date', 'deviations')
```

## Optimization 6: Async Database Access

For high-concurrency scenarios:

```python
# Install: pip install aiosqlite

import aiosqlite

async def fetch_deviations_async():
    async with aiosqlite.connect('data/deviations.db') as db:
        async with db.execute('SELECT * FROM deviations') as cursor:
            return await cursor.fetchall()
```

## Optimization 7: Read Replicas (PostgreSQL/MySQL)

For production deployments:

```python
# Primary for writes
WRITE_DATABASE_URL = "postgresql://user:password@primary:5432/deviations"

# Replicas for reads
READ_DATABASE_URLS = [
    "postgresql://user:password@replica1:5432/deviations",
    "postgresql://user:password@replica2:5432/deviations",
]
```

## Optimization 8: Caching Strategy

Current implementation:
- ✅ In-memory cache (5 minute TTL)
- Suitable for: Small to medium datasets

Alternatives for scaling:
- **Redis**: Distributed caching for multiple instances
- **Memcached**: Simple key-value caching
- **Django Cache Framework**: More advanced caching patterns

```python
# Redis example
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)
cache.set('deviations:all', json.dumps(records), ex=300)
```

## Optimization 9: Data Archiving

For large historical datasets:

```python
# Archive old closed deviations
def archive_old_records(days: int = 90):
    cutoff_date = date.today() - timedelta(days=days)
    
    with connection() as conn:
        conn.execute("""
            INSERT INTO deviations_archive
            SELECT * FROM deviations 
            WHERE review_status = 'Closed' 
            AND updated_at < ?
        """, (cutoff_date,))
        
        conn.execute("""
            DELETE FROM deviations 
            WHERE review_status = 'Closed' 
            AND updated_at < ?
        """, (cutoff_date,))
        
        conn.commit()
```

## Optimization 10: Bulk Operations

For data imports:

```python
# Current approach: 1 batch insert
# Optimized: Use PRAGMA for faster bulk inserts

def bulk_insert_optimized(conn, records):
    # Disable synchronous mode temporarily
    conn.execute('PRAGMA synchronous = OFF')
    conn.execute('PRAGMA journal_mode = MEMORY')
    
    try:
        conn.executemany(INSERT_SQL, records)
        conn.commit()
    finally:
        # Re-enable safety
        conn.execute('PRAGMA synchronous = FULL')
        conn.execute('PRAGMA journal_mode = DELETE')
```

## Performance Impact Estimates

| Optimization | Improvement | Effort | Priority |
|---|---|---|---|
| Indexes | 50-200% for filtered queries | Low | 🔴 High |
| Connection Pooling | 20-50% for concurrent | Medium | 🔴 High |
| Query Analysis | Variable | Low | 🟠 Medium |
| Async I/O | 100-300% for high concurrency | High | 🟠 Medium |
| Migrations | Easier schema management | Low | 🟡 Low |
| Redis Caching | 10-100x for hot data | Medium | 🟡 Low (if scaling) |
| Read Replicas | Better availability, load distribution | High | 🟡 Low (production only) |

## Migration Path

1. **Phase 1 (Immediate)**: Add indexes to current SQLite setup
2. **Phase 2 (Month 1)**: Implement async database access
3. **Phase 3 (Month 2)**: Set up Redis caching for distributed deployments
4. **Phase 4 (Month 3+)**: Migrate to PostgreSQL with read replicas

## Monitoring Database Performance

```python
# Add performance monitoring
import time

def log_query_time(query_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"Query '{query_name}' took {elapsed:.2f}ms")
            return result
        return wrapper
    return decorator

@log_query_time("fetch_deviations")
async def fetch_deviations():
    ...
```

## Testing Database Changes

```bash
# Benchmark before/after
python tests/benchmark.py

# Run all tests
pytest tests/ -v

# Check for query bottlenecks
EXPLAIN QUERY PLAN SELECT ...
```

---

**Last Updated**: 2026-08-12  
**Status**: Ready for implementation  
**Next Review**: After Phase 1 completion
