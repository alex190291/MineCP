import { ServerType } from '@/types/server';

export const SERVER_TYPES: { value: ServerType; label: string; description: string }[] = [
  {
    value: 'vanilla',
    label: 'Vanilla',
    description: 'Official Minecraft server',
  },
  {
    value: 'paper',
    label: 'Paper',
    description: 'High-performance fork with plugin support',
  },
  {
    value: 'forge',
    label: 'Forge',
    description: 'Modding platform for Minecraft',
  },
  {
    value: 'fabric',
    label: 'Fabric',
    description: 'Lightweight modding framework',
  },
  {
    value: 'purpur',
    label: 'Purpur',
    description: 'Feature-rich Paper fork',
  },
  {
    value: 'spigot',
    label: 'Spigot',
    description: 'Popular plugin-based server',
  },
];

export const MINECRAFT_VERSIONS = [
  '1.21.11',
  '1.21.10',
  '1.21.9',
  '1.21.8',
  '1.21.7',
  '1.21.6',
  '1.21.5',
  '1.21.4',
  '1.21.3',
  '1.21.2',
  '1.21.1',
  '1.21',
  '1.20.6',
  '1.20.5',
  '1.20.4',
  '1.20.3',
  '1.20.2',
  '1.20.1',
  '1.20',
  '1.19.4',
  '1.19.3',
  '1.19.2',
  '1.19.1',
  '1.19',
  '1.18.2',
  '1.18.1',
  '1.18',
  '1.17.1',
  '1.16.5',
];

export const DEFAULT_SERVER_PROPERTIES = {
  max_players: 20,
  difficulty: 'normal',
  gamemode: 'survival',
  pvp: true,
  allow_nether: true,
  enable_command_block: false,
  spawn_protection: 16,
  view_distance: 10,
  motd: 'A Minecraft Server',
};

export const STATUS_COLORS = {
  running: 'bg-green-500',
  stopped: 'bg-gray-500',
  starting: 'bg-amber-500',
  stopping: 'bg-orange-500',
  error: 'bg-red-500',
};

export const STATUS_LABELS = {
  running: 'Running',
  stopped: 'Stopped',
  starting: 'Starting',
  stopping: 'Stopping',
  error: 'Error',
};
