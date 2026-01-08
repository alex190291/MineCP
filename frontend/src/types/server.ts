export type ServerType = 'vanilla' | 'paper' | 'forge' | 'fabric' | 'purpur' | 'spigot';
export type ServerStatus = 'stopped' | 'starting' | 'running' | 'stopping' | 'error';

export interface Server {
  id: string;
  name: string;
  type: ServerType;
  version: string;
  status: ServerStatus;
  container_id?: string;
  container_name: string;
  host_port: number;
  memory_limit: number;
  cpu_limit: number;
  disk_limit?: number;
  java_args?: string;
  server_properties?: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ServerMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_usage: number;
  memory_limit: number;
  memory_percent: number;
  network_rx: number;
  network_tx: number;
  online_players: number;
  player_names: string[];
}

export interface CreateServerData {
  name: string;
  type: ServerType;
  version: string;
  memory_limit: number;
  cpu_limit: number;
  host_port: number;
  server_properties?: Record<string, any>;
  java_args?: string;
}
