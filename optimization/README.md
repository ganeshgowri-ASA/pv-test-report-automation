# Optimization Tools

This directory contains performance profiling scripts, optimization strategies, and code quality tools.

## Contents

- `profile_performance.py` - Performance profiling script
- `optimize_queries.py` - Database query optimization
- `cache_strategy.py` - Caching implementation
- `memory_profiler.py` - Memory usage profiling
- `pylintrc` - Pylint configuration
- `pyproject.toml` - Black, isort, mypy configuration

## Usage

### Performance Profiling

```bash
python optimization/profile_performance.py --module src.ingestion.excel_parser
```

### Database Query Optimization

```bash
python optimization/optimize_queries.py --analyze
```

### Memory Profiling

```bash
python -m memory_profiler optimization/memory_profiler.py
```

### Code Quality

```bash
# Format code with black
black src/

# Sort imports with isort
isort src/

# Type checking with mypy
mypy src/

# Linting with pylint
pylint src/
```

## Performance Targets

- API response time: < 200ms (p95)
- Database queries: < 100ms (p95)
- Report generation: < 30s
- Memory usage: < 500MB per worker
- Code coverage: > 80%
