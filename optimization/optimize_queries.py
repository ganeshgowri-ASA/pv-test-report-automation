"""
Database query optimization analyzer.

Analyzes and suggests optimizations for database queries.
"""
import re
from typing import List, Dict, Any
from datetime import datetime


class QueryOptimizer:
    """Database query optimization analyzer."""

    def __init__(self):
        self.slow_query_threshold_ms = 100
        self.recommendations = []

    def analyze_query(self, query: str, execution_time_ms: float) -> Dict[str, Any]:
        """
        Analyze a query and provide optimization recommendations.

        Args:
            query: SQL query string
            execution_time_ms: Query execution time in milliseconds

        Returns:
            Dictionary with analysis results and recommendations
        """
        analysis = {
            "query": query,
            "execution_time_ms": execution_time_ms,
            "is_slow": execution_time_ms > self.slow_query_threshold_ms,
            "recommendations": []
        }

        # Check for SELECT *
        if re.search(r'SELECT\s+\*', query, re.IGNORECASE):
            analysis["recommendations"].append({
                "issue": "Using SELECT *",
                "suggestion": "Select only required columns to reduce data transfer",
                "severity": "medium"
            })

        # Check for missing WHERE clause on large tables
        if re.search(r'SELECT.*FROM\s+reports', query, re.IGNORECASE):
            if not re.search(r'WHERE', query, re.IGNORECASE):
                analysis["recommendations"].append({
                    "issue": "Missing WHERE clause",
                    "suggestion": "Add WHERE clause to limit result set",
                    "severity": "high"
                })

        # Check for LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query, re.IGNORECASE):
            analysis["recommendations"].append({
                "issue": "Leading wildcard in LIKE",
                "suggestion": "Avoid leading wildcards - they prevent index usage",
                "severity": "high"
            })

        # Check for OR clauses (might need index optimization)
        or_count = len(re.findall(r'\bOR\b', query, re.IGNORECASE))
        if or_count > 2:
            analysis["recommendations"].append({
                "issue": f"Multiple OR clauses ({or_count})",
                "suggestion": "Consider using IN clause or UNION for better performance",
                "severity": "medium"
            })

        # Check for subqueries (might be optimizable with JOINs)
        if re.search(r'SELECT.*FROM.*\(.*SELECT', query, re.IGNORECASE):
            analysis["recommendations"].append({
                "issue": "Subquery detected",
                "suggestion": "Consider rewriting with JOIN if possible",
                "severity": "low"
            })

        # Check for missing LIMIT
        if re.search(r'SELECT.*FROM', query, re.IGNORECASE):
            if not re.search(r'LIMIT', query, re.IGNORECASE):
                analysis["recommendations"].append({
                    "issue": "Missing LIMIT clause",
                    "suggestion": "Add LIMIT to prevent returning excessive rows",
                    "severity": "medium"
                })

        return analysis

    def suggest_indexes(self, query: str) -> List[str]:
        """
        Suggest indexes for a query.

        Args:
            query: SQL query string

        Returns:
            List of index suggestions
        """
        suggestions = []

        # Extract WHERE clause columns
        where_match = re.search(r'WHERE\s+(.*?)(?:GROUP|ORDER|LIMIT|$)',
                               query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            columns = re.findall(r'(\w+)\s*[=<>]', where_clause)

            for column in set(columns):
                suggestions.append(f"CREATE INDEX idx_{column} ON table_name({column});")

        # Extract ORDER BY columns
        order_match = re.search(r'ORDER\s+BY\s+([\w,\s]+)', query, re.IGNORECASE)
        if order_match:
            order_columns = [c.strip() for c in order_match.group(1).split(',')]
            for column in order_columns:
                column = column.split()[0]  # Remove ASC/DESC
                suggestions.append(f"CREATE INDEX idx_{column} ON table_name({column});")

        # Extract JOIN columns
        join_matches = re.findall(r'JOIN\s+\w+\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
                                 query, re.IGNORECASE)
        for match in join_matches:
            suggestions.append(f"CREATE INDEX idx_{match[1]} ON {match[0]}({match[1]});")
            suggestions.append(f"CREATE INDEX idx_{match[3]} ON {match[2]}({match[3]});")

        return list(set(suggestions))  # Remove duplicates

    def analyze_slow_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze multiple queries and identify slow ones.

        Args:
            queries: List of query dictionaries with 'sql' and 'duration_ms'

        Returns:
            Analysis summary
        """
        slow_queries = []
        total_time = 0

        for query_info in queries:
            query = query_info.get('sql', '')
            duration = query_info.get('duration_ms', 0)
            total_time += duration

            analysis = self.analyze_query(query, duration)
            if analysis['is_slow']:
                slow_queries.append(analysis)

        return {
            "total_queries": len(queries),
            "slow_queries": len(slow_queries),
            "total_time_ms": total_time,
            "average_time_ms": total_time / len(queries) if queries else 0,
            "slow_query_details": slow_queries
        }


def generate_optimization_report():
    """Generate database optimization report."""
    print("=" * 80)
    print("DATABASE OPTIMIZATION REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    optimizer = QueryOptimizer()

    # Example queries to analyze
    example_queries = [
        {
            "sql": "SELECT * FROM reports WHERE created_at > '2024-01-01'",
            "duration_ms": 150
        },
        {
            "sql": "SELECT id, status FROM reports WHERE status = 'PENDING' LIMIT 10",
            "duration_ms": 25
        },
        {
            "sql": "SELECT * FROM equipment WHERE name LIKE '%simulator%'",
            "duration_ms": 200
        }
    ]

    analysis = optimizer.analyze_slow_queries(example_queries)

    print(f"Total Queries Analyzed: {analysis['total_queries']}")
    print(f"Slow Queries Found: {analysis['slow_queries']}")
    print(f"Average Query Time: {analysis['average_time_ms']:.2f}ms")
    print()

    if analysis['slow_query_details']:
        print("SLOW QUERIES AND RECOMMENDATIONS:")
        print("-" * 80)

        for i, query_analysis in enumerate(analysis['slow_query_details'], 1):
            print(f"\n{i}. Query (took {query_analysis['execution_time_ms']}ms):")
            print(f"   {query_analysis['query']}")
            print()
            print("   Recommendations:")
            for rec in query_analysis['recommendations']:
                print(f"   - [{rec['severity'].upper()}] {rec['issue']}")
                print(f"     Suggestion: {rec['suggestion']}")
            print()

    # Index suggestions
    print("\nSUGGESTED INDEXES:")
    print("-" * 80)
    for query_info in example_queries:
        indexes = optimizer.suggest_indexes(query_info['sql'])
        if indexes:
            print(f"\nFor query: {query_info['sql'][:60]}...")
            for index in indexes:
                print(f"  {index}")


def main():
    """Main entry point."""
    generate_optimization_report()


if __name__ == "__main__":
    main()
