"""
Main Application Entry Point.

Launches the PV Test Report Automation system with CLI interface.
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="PV Test Report Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch Streamlit UI
  python -m src.main ui

  # Run API server
  python -m src.main api

  # Run test
  python -m src.main test --protocol iec61215 --sample-id PV-001

  # Export report
  python -m src.main export --report-id <uuid> --format pdf

For more information, visit: https://github.com/ganeshgowri-ASA/pv-test-report-automation
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # UI command
    ui_parser = subparsers.add_parser('ui', help='Launch Streamlit UI')
    ui_parser.add_argument('--port', type=int, default=8501, help='Port number')

    # API command
    api_parser = subparsers.add_parser('api', help='Launch FastAPI server')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host address')
    api_parser.add_argument('--port', type=int, default=8000, help='Port number')
    api_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run PV module test')
    test_parser.add_argument('--protocol', required=True,
                            choices=['iec61215', 'iec61730', 'iec61853', 'iec61701'],
                            help='Test protocol')
    test_parser.add_argument('--sample-id', required=True, help='Sample ID')
    test_parser.add_argument('--config', help='Configuration file path')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export test report')
    export_parser.add_argument('--report-id', required=True, help='Report UUID')
    export_parser.add_argument('--format', required=True,
                              choices=['pdf', 'docx', 'xlsx', 'html', 'json', 'xml'],
                              help='Export format')
    export_parser.add_argument('--output', help='Output file path')

    # Database command
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_parser.add_argument('action', choices=['init', 'migrate', 'reset'],
                          help='Database action')

    args = parser.parse_args()

    if args.command == 'ui':
        launch_ui(args.port)
    elif args.command == 'api':
        launch_api(args.host, args.port, args.reload)
    elif args.command == 'test':
        run_test(args.protocol, args.sample_id, args.config)
    elif args.command == 'export':
        export_report(args.report_id, args.format, args.output)
    elif args.command == 'db':
        database_operation(args.action)
    else:
        parser.print_help()


def launch_ui(port: int) -> None:
    """Launch Streamlit UI."""
    import subprocess
    logger.info(f"Launching Streamlit UI on port {port}")
    subprocess.run([
        'streamlit', 'run',
        'src/ui/protocol_selection.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0'
    ])


def launch_api(host: str, port: int, reload: bool) -> None:
    """Launch FastAPI server."""
    import subprocess
    logger.info(f"Launching API server on {host}:{port}")
    cmd = ['uvicorn', 'src.api.main:app', '--host', host, '--port', str(port)]
    if reload:
        cmd.append('--reload')
    subprocess.run(cmd)


def run_test(protocol: str, sample_id: str, config_path: str | None) -> None:
    """Run PV module test."""
    logger.info(f"Running {protocol} test for sample {sample_id}")
    print("Test execution would happen here")
    # Test execution logic would be implemented here


def export_report(report_id: str, format: str, output: str | None) -> None:
    """Export test report."""
    logger.info(f"Exporting report {report_id} to {format}")
    print("Export would happen here")
    # Export logic would be implemented here


def database_operation(action: str) -> None:
    """Perform database operation."""
    logger.info(f"Database operation: {action}")
    from src.database.db_manager import db_manager

    if action == 'init':
        db_manager.initialize()
        db_manager.create_tables()
        logger.info("Database initialized")
    elif action == 'reset':
        response = input("WARNING: This will delete all data. Continue? (yes/no): ")
        if response.lower() == 'yes':
            db_manager.drop_tables()
            db_manager.create_tables()
            logger.info("Database reset completed")
    elif action == 'migrate':
        logger.info("Run migrations with: alembic upgrade head")


if __name__ == '__main__':
    main()
