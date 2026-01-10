"""
Flask application factory.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request, redirect
from flask_cors import cross_origin

from app.config import config
from app.extensions import db, migrate, jwt, cors, socketio, limiter
from flask_jwt_extended import get_jwt


def validate_security_config(app, config_name):
    """
    Validate security-critical configuration settings.
    Raises RuntimeError if insecure defaults are detected in production.
    """
    warnings = []
    errors = []

    # Check JWT secret key
    jwt_secret = app.config.get('JWT_SECRET_KEY', '')
    if jwt_secret == 'jwt-secret-key-change-in-production':
        msg = "JWT_SECRET_KEY is using default value"
        if config_name == 'production':
            errors.append(msg)
        else:
            warnings.append(msg)

    # Check Flask secret key
    secret_key = app.config.get('SECRET_KEY', '')
    if secret_key == 'dev-secret-key-change-in-production':
        msg = "SECRET_KEY is using default value"
        if config_name == 'production':
            errors.append(msg)
        else:
            warnings.append(msg)

    # Check default admin password
    default_admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD', '')
    if default_admin_password == 'changeme':
        msg = "DEFAULT_ADMIN_PASSWORD is set to 'changeme'"
        if config_name == 'production':
            warnings.append(msg + " - ensure admin changes password on first login")
        else:
            warnings.append(msg)

    # Check bootstrap password
    bootstrap_password = app.config.get('BOOTSTRAP_PASSWORD', '')
    if bootstrap_password == 'changeme':
        msg = "BOOTSTRAP_PASSWORD is set to 'changeme'"
        if config_name == 'production':
            warnings.append(msg + " - update before provisioning admin account")
        else:
            warnings.append(msg)

    # Check encryption key
    encryption_key = app.config.get('ENCRYPTION_KEY')
    if not encryption_key:
        msg = "ENCRYPTION_KEY is not set - sensitive data cannot be encrypted"
        if config_name == 'production':
            errors.append(msg)
        else:
            warnings.append(msg)

    # Log warnings
    if warnings and not app.testing:
        for warning in warnings:
            app.logger.warning(f"SECURITY WARNING: {warning}")

    # Raise errors for production
    if errors:
        error_msg = "Security configuration errors detected:\n" + "\n".join(f"  - {e}" for e in errors)
        error_msg += "\n\nPlease set the following environment variables:"
        if any('JWT_SECRET_KEY' in e for e in errors):
            error_msg += "\n  export JWT_SECRET_KEY='<your-random-secret-key>'"
        if any('SECRET_KEY' in e for e in errors):
            error_msg += "\n  export SECRET_KEY='<your-random-secret-key>'"
        if any('ENCRYPTION_KEY' in e for e in errors):
            error_msg += "\n  export ENCRYPTION_KEY='<your-encryption-key>'"
        error_msg += "\n\nGenerate random keys with:"
        error_msg += "\n  python -c 'import secrets; print(secrets.token_hex(32))'"
        error_msg += "\n  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        raise RuntimeError(error_msg)


def setup_jwt_blacklist(app):
    """Setup JWT token blacklist checking."""
    from app.utils.token_blacklist import get_blacklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is in blacklist."""
        jti = jwt_payload["jti"]
        blacklist = get_blacklist()
        return blacklist.is_blacklisted(jti)


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

    # Validate security configuration
    validate_security_config(app, config_name)

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

    # Setup JWT token blacklist checking
    setup_jwt_blacklist(app)

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

    # Add security headers
    add_security_headers(app)

    # Add HTTPS redirect middleware (production only)
    if not app.debug and not app.testing:
        add_https_redirect(app)

    # Ensure database tables exist before starting background jobs
    init_database(app)
    try:
        from app.utils.permissions import seed_permissions_and_roles, ensure_creator_assignments
        with app.app_context():
            seed_permissions_and_roles()
            ensure_creator_assignments()
    except Exception as e:
        app.logger.warning(f"Failed to seed roles/permissions: {e}")

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
    from app.api import auth, servers, monitoring, mods, backups, users, ldap_config, versions, files, roles

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
    app.register_blueprint(roles.bp, url_prefix='/api')


def add_https_redirect(app):
    """Redirect HTTP requests to HTTPS in production."""

    @app.before_request
    def redirect_to_https():
        # Don't redirect for health check endpoints
        if request.path == '/health' or request.path.startswith('/api/health'):
            return None

        # Check if request is over HTTP (not HTTPS)
        if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)  # Permanent redirect

        return None


def add_security_headers(app):
    """Add security headers to all responses."""

    @app.after_request
    def set_security_headers(response):
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Enable XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HTTPS-only (if not in development)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        # Note: Adjust CSP for your frontend needs
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
        response.headers['Content-Security-Policy'] = csp

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response


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
    """Create a bootstrap user on first run when no admin exists."""
    from app.models.user import User
    from app.models.system_setup import SystemSetup
    from flask import current_app
    from sqlalchemy.exc import OperationalError, IntegrityError

    try:
        if not SystemSetup.is_first_run():
            if User.query.filter_by(role='admin').count() == 0:
                current_app.logger.warning('No admin users exist')
            return

        if User.query.filter_by(role='admin').first():
            SystemSetup.mark_setup_complete()
            return

        if User.query.filter_by(role='bootstrap').first():
            return

        try:
            bootstrap = User(
                username=current_app.config['BOOTSTRAP_USERNAME'],
                email=current_app.config['BOOTSTRAP_EMAIL'],
                role='bootstrap',
                is_ldap_user=False
            )
            bootstrap.set_password(current_app.config['BOOTSTRAP_PASSWORD'])
            db.session.add(bootstrap)
            db.session.commit()
            current_app.logger.info(f'Bootstrap user created: {bootstrap.username}')
        except IntegrityError:
            db.session.rollback()

    except OperationalError:
        pass
