export interface LDAPConfig {
  id: number;
  enabled: boolean;
  server_uri?: string | null;
  bind_dn?: string | null;
  bind_password?: string | null;
  user_search_base?: string | null;
  user_search_filter?: string | null;
  group_search_base?: string | null;
  group_search_filter?: string | null;
  updated_at?: string | null;
}

export interface LDAPTestPayload {
  server_uri: string;
  bind_dn: string;
  bind_password: string;
}
