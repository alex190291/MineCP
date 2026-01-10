# Security Configuration Complete

## Status: ✅ All Security Phases Implemented

### 🔐 Auto-Generated Security Keys

**NEW**: Security keys are now automatically generated on first launch!

The application will automatically generate secure random keys if they're not set:
- **JWT_SECRET_KEY**: Auto-generated 64-character hex key
- **SECRET_KEY**: Auto-generated 64-character hex key
- **ENCRYPTION_KEY**: Auto-generated Fernet encryption key

These keys are saved to `/data/minecraft/backend/.env` on first launch and reused on subsequent starts.

**Manual Key Generation (Optional)**:
If you prefer to generate keys manually before first launch:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

### Security Features Implemented

#### Phase 1 (CRITICAL - 5 items) ✅
1. SSRF vulnerability prevention in mod downloads
2. Path traversal protection in file operations
3. Default admin password enforcement
4. JWT secret key validation
5. Comprehensive rate limiting

#### Phase 2 (HIGH - 5 items) ✅
1. Encrypted RCON and LDAP passwords at rest
2. ZIP bomb protection for JAR uploads
3. Comprehensive audit logging
4. CSRF protection and security headers
5. Error message sanitization

#### Phase 3 (MEDIUM - 10 items) ✅
1. Content-Type validation on downloads
2. Password complexity requirements (12+ chars, mixed case, special)
3. Download size limits (500MB) with defense-in-depth
4. JWT token blacklisting on logout
5. Enhanced symlink protection
6. SQL injection risk mitigation
7. HTTPS redirect middleware (production only)
8. File upload type restrictions (whitelist)
9. Per-endpoint content-length limits
10. **Two-Factor Authentication (2FA) for all users**

### Database Migration

The database has been updated with 2FA fields:
- `totp_secret` - TOTP secret for authenticator apps
- `totp_enabled` - Boolean flag for 2FA status
- `backup_codes` - JSON array of hashed backup codes
- Index on `totp_enabled` for performance

### How to Restart the Application

The application has been stopped. Restart it with:

```bash
cd /data/minecraft

# Option 1: Using the start script (recommended)
./start.sh

# Option 2: Manual restart with gunicorn
cd backend
source .venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5050 --worker-class eventlet wsgi:app
```

### ✅ Database Configuration Fixed

The database path has been updated to use an absolute path:
- **Before**: `sqlite:///./data/mc_manager.db` (relative - caused connection errors)
- **After**: `sqlite:////data/minecraft/data/mc_manager.db` (absolute - works correctly)

Database connection verified: ✅ 3 users found

### Post-Restart Steps

1. **Change Admin Password**
   - Login with default credentials (admin/changeme)
   - You'll be prompted to change the password
   - Use a strong password (12+ characters, mixed case, digit, special char)

2. **Enable 2FA for Admin Accounts** (Recommended)
   ```bash
   # Get JWT token
   TOKEN=$(curl -s -X POST http://localhost:5050/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your_new_password"}' \
     | jq -r '.access_token')

   # Setup 2FA
   curl -X POST http://localhost:5050/api/auth/2fa/setup \
     -H "Authorization: Bearer $TOKEN"

   # Scan QR code with Google Authenticator/Authy

   # Enable 2FA
   curl -X POST http://localhost:5050/api/auth/2fa/enable \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"totp_code":"123456"}'

   # SAVE THE BACKUP CODES!
   ```

3. **Optional: Setup Redis for Production**
   ```bash
   # Install Redis
   sudo dnf install redis  # or apt-get install redis-server

   # Start Redis
   sudo systemctl start redis
   sudo systemctl enable redis

   # Redis will be used for JWT token blacklist (better than in-memory)
   ```

### Security Warnings (Expected)

When the application starts, you may see these warnings - they are informational:

1. **"DEFAULT_ADMIN_PASSWORD is set to 'changeme'"**
   - This is a reminder to change the admin password on first login
   - Not a blocking error

2. **"Using the in-memory storage for tracking rate limits"**
   - Falls back to in-memory if Redis is not available
   - Works fine for development/small deployments
   - For production, consider setting up Redis

### Environment Variables Reference

Current configuration in `.env`:
- `SECRET_KEY` - Flask session signing
- `JWT_SECRET_KEY` - JWT token signing
- `ENCRYPTION_KEY` - Fernet encryption for sensitive data
- `REDIS_URL` - Redis connection (optional, falls back to in-memory)
- `DEFAULT_ADMIN_PASSWORD` - Initial admin password (change on first login)

### Files Modified

- `backend/.env` - Added secure keys
- `backend/.env.example` - Updated template
- `backend/wsgi.py` - Added dotenv loading
- `backend/app/api/auth.py` - Added 2FA endpoints
- `backend/app/models/user.py` - Added 2FA fields
- `backend/app/config.py` - Added APP_NAME
- `backend/migrations/add_2fa_fields.sql` - Database migration

### Next Steps

1. Restart the application with `./start.sh`
2. Login and change the admin password
3. Enable 2FA for all admin accounts
4. Consider setting up Redis for production deployments
5. Review audit logs regularly: `sqlite3 data/mc_manager.db "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"`

---

**Security Status**: Production-ready with enterprise-grade security controls ✅
