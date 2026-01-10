export interface Role {
  id: string;
  name: string;
  description?: string;
  is_system: boolean;
  permissions: string[];
}

export interface Permission {
  id: string;
  name: string;
  description?: string;
}

export interface ServerRoleAssignment {
  user_id: string;
  role_id: string;
  role_name?: string | null;
}

export interface LdapGroup {
  dn: string;
  name: string;
}

export interface LdapGroupAssignment {
  group_dn: string;
  group_name?: string | null;
  role_id: string;
  role_name?: string | null;
}
