# Minecraft Server Manager

Web-based platform for managing multiple Minecraft servers with Docker containers.

## Features

- **Server Management**: Create, start, stop, and monitor multiple Minecraft servers
- **Mod Management**: Upload, download, and install mods from Modrinth/CurseForge
- **Player Administration**: Ban, kick, OP players via RCON
- **Server Configuration**: Visual editor for server.properties
- **Backup System**: Create, download, and restore server backups
- **Real-time Monitoring**: Live metrics and WebSocket updates
- **User Management**: JWT authentication with role-based access

## Tech Stack

**Backend**: Flask, SQLite, Docker SDK, Flask-SocketIO
**Frontend**: React 18, TypeScript, TailwindCSS, React Query

## Quick Start

### Prerequisites
- Docker
- Python 3.12+
- Node.js 16+

### Run

```bash
./start.sh
```

Open http://localhost:5050

Default login: `admin` / `changeme`

## License

MIT License
