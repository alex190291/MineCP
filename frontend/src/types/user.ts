export type UserRole = 'admin' | 'user' | 'bootstrap' | 'operator' | 'viewer';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole | string;  // role name (computed from role_id)
  role_id?: string;  // foreign key to roles table
  is_ldap_user: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
  require_password_change?: boolean;
}
