# Minecraft Server Manager - Backend

Flask-based REST API backend for the Minecraft Server Management Platform.

## Quick Start

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Set Flask app environment variable
export FLASK_APP=app

# Initialize Alembic migrations
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

Or use the provided setup script:

```bash
python3 setup_db.py
```

### 3. Run Development Server

```bash
python run.py
```

The API will be available at `http://localhost:5000`

## Default Admin Credentials

- **Username:** admin
- **Password:** changeme

**Important:** Change the default password after first login!

## API Endpoints

### Authentication (`/api/auth`)

- `POST /api/auth/login` - Login and get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout (client-side token removal)

### Testing Authentication

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'

# Get current user (replace TOKEN with access_token from login response)
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions
│   ├── api/                 # API blueprints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── servers.py       # Server management (TODO)
│   │   ├── monitoring.py    # Monitoring endpoints (TODO)
│   │   ├── mods.py          # Mod management (TODO)
│   │   ├── backups.py       # Backup management (TODO)
│   │   ├── users.py         # User management (TODO)
│   │   └── ldap_config.py   # LDAP configuration (TODO)
│   ├── models/              # Database models
│   │   ├── user.py          # User model
│   │   ├── server.py        # Server model
│   │   ├── server_mod.py    # ServerMod model
│   │   ├── backup.py        # Backup model
│   │   ├── player.py        # Player model
│   │   ├── audit_log.py     # AuditLog model
│   │   └── ldap_config.py   # LDAPConfig model
│   ├── services/            # Business logic services
│   ├── background/          # Background tasks
│   ├── schemas/             # Marshmallow schemas
│   ├── utils/               # Utility functions
│   └── websockets/          # WebSocket handlers
├── migrations/              # Alembic migrations
├── tests/                   # Unit tests
├── logs/                    # Application logs
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Development server
├── wsgi.py                  # Production WSGI entry point
└── setup_db.py              # Database setup script

```

## Database Models

### User
- Authentication and authorization
- Local users with password hash
- LDAP user support
- Role-based access (admin/user)

### Server
- Minecraft server instances
- Docker container configuration
- Resource limits (memory, CPU, disk)
- Server properties and Java args

### ServerMod
- Mods/plugins installed on servers
- Support for Modrinth, CurseForge, and uploads
- Enable/disable functionality

### Backup
- Server backups
- Manual and scheduled backups
- Compression support

### Player
- Minecraft player tracking
- Ban management
- Activity tracking

### AuditLog
- User action tracking
- Full audit trail

### LDAPConfig
- LDAP/Active Directory configuration
- Singleton model

## Configuration

Configuration is managed through environment variables in `.env`:

```env
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///./data/mc_manager.db

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Docker
DOCKER_SOCKET=unix://var/run/docker.sock
MC_SERVER_NETWORK=minecraft-network

# Default Admin
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=changeme
DEFAULT_ADMIN_EMAIL=admin@localhost
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black app/

# Check linting
flake8 app/
```

### Database Migrations

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Using Gunicorn with SocketIO

```bash
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 "wsgi:app"
```

### Environment Variables

Make sure to set secure values for production:

- `SECRET_KEY` - Strong random secret key
- `JWT_SECRET_KEY` - Strong random JWT secret key
- `FLASK_ENV=production`

## Security

- Change default admin password immediately
- Use strong secret keys in production
- Enable HTTPS in production
- Configure CORS origins appropriately
- Review and update security settings regularly

## Next Steps

This backend core provides the foundation. The following still need to be implemented:

1. **Docker Integration** (Track 2)
   - Server lifecycle management
   - Container orchestration
   - Resource monitoring

2. **Frontend** (Track 3)
   - React dashboard
   - Server management UI
   - Monitoring visualizations

3. **Feature Integration** (Track 4)
   - Complete server management endpoints
   - Mod/plugin management
   - Backup/restore functionality
   - Real-time monitoring
   - WebSocket notifications

## Troubleshooting

### Database locked error

SQLite WAL mode should handle this, but if you see database locked errors:

```bash
# Check if WAL mode is enabled
sqlite3 data/mc_manager.db "PRAGMA journal_mode;"
# Should return: wal
```

### Import errors

Make sure you're in the virtual environment and have installed all dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### CORS errors

Check that `CORS_ORIGINS` in `.env` matches your frontend URL.

## License

[Your License Here]
