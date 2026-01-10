# Security Keys Auto-Generation

## How It Works

Starting from this version, the application automatically generates secure random keys on first launch if they're not configured. This eliminates the need for manual key generation during setup.

### Auto-Generated Keys

The following keys are automatically generated if missing or set to default values:

1. **JWT_SECRET_KEY** - Used for signing JWT authentication tokens
2. **SECRET_KEY** - Used for Flask session signing and CSRF protection
3. **ENCRYPTION_KEY** - Used for encrypting sensitive data at rest (RCON passwords, LDAP credentials)

### First Launch Behavior

When you start the application for the first time (or with empty/default key values):

1. The application checks `.env` for each required key
2. If a key is missing, empty, or set to a placeholder value, it generates a cryptographically secure random value
3. The generated keys are saved to `.env` with restrictive permissions (600)
4. You'll see a message like this:

```
============================================================
🔐 SECURITY: Auto-generated secrets on first launch
============================================================
  ✓ JWT_SECRET_KEY: Generated
  ✓ SECRET_KEY: Generated
  ✓ ENCRYPTION_KEY: Generated

Secrets saved to: /data/minecraft/backend/.env
⚠️  Keep this .env file secure and do not commit it to git!
============================================================
```

### Subsequent Launches

On subsequent application starts, the saved keys from `.env` are reused. No new keys are generated.

### Security Properties

- **Cryptographic Quality**: Keys are generated using Python's `secrets` module and Fernet for maximum entropy
- **JWT_SECRET_KEY**: 64-character (256-bit) hexadecimal string
- **SECRET_KEY**: 64-character (256-bit) hexadecimal string
- **ENCRYPTION_KEY**: Fernet-compatible key (44-character base64-encoded 256-bit key)
- **File Permissions**: `.env` is automatically set to mode 600 (owner read/write only)
- **Git Protection**: `.env` is in `.gitignore` to prevent accidental commits

### Manual Key Generation (Optional)

If you prefer to generate keys before first launch, you can add them to `.env`:

```bash
# Generate JWT and Flask secret keys (64-char hex)
python -c 'import secrets; print(secrets.token_hex(32))'

# Generate encryption key (Fernet)
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Then add to `.env`:
```bash
SECRET_KEY=<generated-key>
JWT_SECRET_KEY=<generated-key>
ENCRYPTION_KEY=<generated-key>
```

### Production Deployment

For production environments:

1. **Automated Deployments**: Let the application auto-generate keys on first launch
2. **Manual Control**: Pre-generate keys and add them to environment variables before deployment
3. **Secret Management**: Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) and load via environment variables

### Environment Variables vs .env File

The application checks for keys in this order:

1. **Environment variables** (set via `export`, systemd, Docker, etc.)
2. **.env file** (loaded via python-dotenv)
3. **Auto-generation** (if not found in environment or .env)

This allows flexible deployment patterns:
- Development: Uses `.env` with auto-generated keys
- Production: Can use environment variables from orchestration platform
- Docker: Can inject via `-e` flags or compose environment

### Validation

Production mode enforces security validation:
- Blocks startup if keys are set to known insecure defaults
- Allows auto-generated keys (they're cryptographically secure)
- Warns about DEFAULT_ADMIN_PASSWORD being unchanged

### File Locations

- **wsgi.py**: Production entry point with auto-generation
- **run.py**: Development entry point with auto-generation
- **app/utils/secrets.py**: Reusable secret generation utilities
- **.env**: Generated keys are saved here
- **.env.example**: Template showing configuration structure

### Troubleshooting

**Keys keep regenerating on each start:**
- Check that `.env` file exists and has write permissions
- Verify the keys in `.env` are not empty or set to placeholder values
- Check file ownership - application needs write access to update `.env`

**Application fails to start in production:**
- This shouldn't happen with auto-generation
- If manually setting keys, ensure they're not set to default placeholder values
- Check that ENCRYPTION_KEY is properly formatted (Fernet-compatible)

**Want to rotate keys:**
1. Stop the application
2. Delete or clear the old keys from `.env`
3. Restart - new keys will be auto-generated
4. **Warning**: Rotating ENCRYPTION_KEY will make existing encrypted data unreadable

### Best Practices

✅ **DO**:
- Let the application auto-generate keys on first launch
- Keep `.env` file secure with restrictive permissions
- Back up `.env` in a secure location
- Use environment variables in container/cloud deployments

❌ **DON'T**:
- Commit `.env` to version control
- Share `.env` file publicly
- Rotate ENCRYPTION_KEY without migrating encrypted data
- Use the same keys across development and production

### Migration Path

If you have existing deployments with manually set keys:

1. **No action needed** - existing keys in `.env` will be preserved
2. Auto-generation only triggers if keys are missing/empty/defaults
3. Your production keys remain unchanged

For new deployments:

1. Simply start the application
2. Keys are auto-generated
3. Application is ready to use
