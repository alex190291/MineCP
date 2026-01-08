"""
Flask application factory.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import cross_origin

from app.config import config
from app.extensions import db, migrate, jwt, cors, socketio, limiter


def create_app(config_name=None):
    """
    Application factory pattern.

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__,
                static_folder='static',
                static_url_path='')

    # Load configuration
    app.config.from_object(config[config_name])

    # Ensure required directories exist
    for directory in [app.config['UPLOAD_FOLDER'],
                     app.config['LOG_FILE'].parent,
                     app.config['MC_SERVER_DATA_DIR'],
                     app.config['MC_BACKUP_DIR']]:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    socketio.init_app(app,
                     cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
                     async_mode=app.config['SOCKETIO_ASYNC_MODE'])
    limiter.init_app(app)

    # Register WebSocket handlers
    from app import websockets  # noqa: F401

    # Setup logging
    setup_logging(app)

    # Enable SQLite WAL mode for better concurrency
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        try:
            with app.app_context():
                with db.engine.connect() as conn:
                    conn.execute(db.text("PRAGMA journal_mode=WAL"))
                    conn.commit()
        except Exception as e:
            app.logger.warning(f"Failed to enable WAL mode: {e}")

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Ensure database tables exist before starting background jobs
    init_database(app)

    # Start background monitoring scheduler
    from app.background.monitoring_tasks import start_monitoring_scheduler
    start_monitoring_scheduler(app)

    # Create default admin user
    with app.app_context():
        from app.models.user import User
        create_default_admin()

    # Serve React App (catch-all route for SPA)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        """Serve React application."""
        if path and Path(app.static_folder, path).exists():
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    app.logger.info(f'Application started in {config_name} mode')

    return app


def setup_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # File handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Minecraft Manager startup')


def init_database(app):
    """Initialize database tables if they don't exist."""
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import inspect

    try:
        with app.app_context():
            # Ensure models are registered before inspecting metadata
            from app import models  # noqa: F401
            inspector = inspect(db.engine)
            existing_tables = set(inspector.get_table_names())
            expected_tables = set(db.metadata.tables.keys())

            if not expected_tables:
                app.logger.warning('No database tables defined; skipping init')
                return

            missing_tables = expected_tables - existing_tables
            if missing_tables:
                db.create_all()
                app.logger.info(
                    f"Database initialized (created: {', '.join(sorted(missing_tables))})"
                )
            else:
                app.logger.info('Database already initialized')
    except OperationalError as e:
        app.logger.warning(f'Failed to initialize database: {e}')


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.api import auth, servers, monitoring, mods, backups, users, ldap_config, versions, files

    # Register API blueprints with /api prefix
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(servers.bp, url_prefix='/api/servers')
    app.register_blueprint(monitoring.bp, url_prefix='/api/monitoring')
    app.register_blueprint(mods.bp, url_prefix='/api')
    app.register_blueprint(backups.bp, url_prefix='/api')
    app.register_blueprint(users.bp, url_prefix='/api/users')
    app.register_blueprint(ldap_config.bp, url_prefix='/api/ldap')
    app.register_blueprint(versions.bp, url_prefix='/api/versions')
    app.register_blueprint(files.bp, url_prefix='/api')


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403

    @app.errorhandler(404)
    def not_found(error):
        if not request.path.startswith('/api'):
            index_path = Path(app.static_folder, 'index.html')
            if index_path.exists():
                return send_from_directory(app.static_folder, 'index.html')
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal error: {error}')
        return jsonify({'error': 'Internal server error'}), 500


def create_default_admin():
    """Create default admin user if none exists."""
    from app.models.user import User
    from flask import current_app
    from sqlalchemy.exc import OperationalError

    try:
        if User.query.filter_by(username=current_app.config['DEFAULT_ADMIN_USERNAME']).first() is None:
            admin = User(
                username=current_app.config['DEFAULT_ADMIN_USERNAME'],
                email=current_app.config['DEFAULT_ADMIN_EMAIL'],
                role='admin',
                is_ldap_user=False
            )
            admin.set_password(current_app.config['DEFAULT_ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            current_app.logger.info(f'Default admin user created: {admin.username}')
    except OperationalError:
        current_app.logger.warning('Database not initialized yet; skipping default admin creation')
