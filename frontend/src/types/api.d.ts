export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface Pratica {
  id: number;
  numero: string;
  oggetto: string;
  stato: 'aperta' | 'chiusa' | 'sospesa';
  data_apertura: string;
  data_chiusura?: string;
  cliente?: {
    id: number;
    nome: string;
    cognome: string;
  };
}

export interface DashboardStats {
  pratiche_attive: number;
  pratiche_chiuse: number;
  documenti_count: number;
  scadenze_oggi: number;
  pratiche_per_mese: {
    mese: string;
    count: number;
  }[];
}
