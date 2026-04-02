export interface User {
  id: number;
  email: string;
  full_name: string;
  company_name: string | null;
  company_address: string | null;
  company_logo_url: string | null;
  phone: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  role: 'user' | 'admin';
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
  role?: 'user' | 'admin';
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ProfileUpdate {
  full_name?: string;
  company_name?: string;
  company_address?: string;
  phone?: string;
}
