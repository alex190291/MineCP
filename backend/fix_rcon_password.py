#!/usr/bin/env python
"""Fix RCON password in database."""
from app import create_app, db
from app.models.server import Server

app = create_app('development')
with app.app_context():
    server = Server.query.first()
    correct_password = 'gmFbFy0Qu-glEErRRkHfoA'

    print(f'Database RCON password: {server.rcon_password}')
    print(f'Container RCON password: {correct_password}')

    if server.rcon_password != correct_password:
        print('\nPasswords do not match! Updating database...')
        server.rcon_password = correct_password
        db.session.commit()
        print('✅ Updated RCON password in database')
    else:
        print('✅ Passwords already match')
