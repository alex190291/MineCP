#!/usr/bin/env python
"""Fix RCON port in database to match container mapping."""
from app import create_app, db
from app.models.server import Server
import docker

app = create_app('development')
with app.app_context():
    server = Server.query.first()
    if not server:
        print('No servers found')
        exit(0)

    client = docker.from_env()
    container = client.containers.get(server.container_id)

    # Get actual port mappings
    ports = container.attrs['NetworkSettings']['Ports']

    print('Container port mappings:')
    for internal, mappings in ports.items():
        if mappings:
            host_port = mappings[0]['HostPort']
            print(f'  {internal} -> localhost:{host_port}')

            # Update database if RCON port is wrong
            if '25575/tcp' == internal:
                print(f'\nDatabase RCON port: {server.rcon_port}')
                print(f'Actual RCON host port: {host_port}')

                if str(server.rcon_port) != host_port:
                    print(f'\nUpdating database to use correct RCON port...')
                    server.rcon_port = int(host_port)
                    db.session.commit()
                    print(f'✅ Updated server.rcon_port to {host_port}')
                else:
                    print('✅ RCON port is already correct')
