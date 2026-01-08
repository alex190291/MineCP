#!/usr/bin/env python
"""Test LDAP group membership for a specific user."""
import sys
from app import create_app
from app.models.ldap_config import LDAPConfig

app = create_app('development')

with app.app_context():
    config = LDAPConfig.query.get(1)

    if not config or not config.enabled:
        print('❌ LDAP is not enabled')
        sys.exit(1)

    print('Testing LDAP group membership...')
    print(f'LDAP Server: {config.server_uri}')
    print(f'User search base: {config.user_search_base}')
    print(f'Group search base: {config.group_search_base}')
    print(f'Admin group name: {config.admin_group_name}')
    print()

    # Try to connect and check a user
    username = 'najujo@nosinu-records.com'
    print(f'Checking user: {username}')
    print('NOTE: This will prompt for the user\'s password')
    print()

    import getpass
    password = getpass.getpass('Enter password: ')

    # Import the authentication function
    from app.api.auth import _ldap_authenticate

    result = _ldap_authenticate(username, password)

    if result:
        print()
        print('✅ LDAP authentication successful!')
        print(f'Username: {result.get("username")}')
        print(f'Email: {result.get("email")}')
        print(f'DN: {result.get("dn")}')
        print(f'Role: {result.get("role")}')

        if result.get('role') == 'admin':
            print()
            print('🎉 User IS in admin group!')
        else:
            print()
            print('⚠️  User is NOT in admin group')
            print('Check the logs above for details about group membership checking')
    else:
        print('❌ LDAP authentication failed')
        print('Check the logs for details')
