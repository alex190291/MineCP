export type UserRole = 'admin' | 'user' | 'bootstrap';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
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
