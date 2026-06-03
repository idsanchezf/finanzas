/** Tipos para usuarios y autenticacion. */

export interface User {
  id: string;
  nombre: string;
  email: string;
  avatar_url: string | null;
  tarjetas: Tarjeta[];
}

export interface Tarjeta {
  id: string;
  banco: string;
  ultimos_4_digitos: string;
  tipo: 'credito' | 'debito';
  alias: string | null;
  activa: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}
