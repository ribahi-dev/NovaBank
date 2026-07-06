// Types miroir des schemas Pydantic du backend — LE contrat de l'API.
export type Role = "admin" | "director" | "advisor";

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Client {
  id: number;
  first_name: string;
  last_name: string;
  cin: string;
  phone: string | null;
  address: string | null;
  profession: string | null;
  monthly_income: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Account {
  id: number;
  account_number: string;
  account_type: "current" | "savings";
  balance: string;
  status: "active" | "blocked" | "closed";
  client_id: number;
  created_at: string;
}

export interface RiskScore {
  score: number;
  confidence_level: string;
  explanation: string;
  model_version: string;
}

export interface Transaction {
  id: number;
  transaction_type: "deposit" | "withdrawal" | "transfer";
  amount: string;
  city: string | null;
  description: string | null;
  account_id: number;
  destination_account_id: number | null;
  created_by_id: number;
  created_at: string;
  risk_score: RiskScore | null;
}

export interface Alert {
  id: number;
  alert_type: "transaction_risk" | "login_security";
  level: "low" | "medium" | "high" | "critical";
  message: string;
  status: "open" | "in_progress" | "closed";
  transaction_id: number | null;
  created_at: string;
  closed_at: string | null;
  transaction: Transaction | null;
}

export interface Kpi {
  total_clients: number;
  total_accounts: number;
  total_transactions: number;
  open_alerts: number;
  total_deposits: string;
  total_withdrawals: string;
  average_risk_score: number | null;
}

export interface TrendPoint {
  day: string;
  transaction_count: number;
  total_amount: string;
}

export interface TypeDistribution {
  transaction_type: string;
  count: number;
  total_amount: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  ip_address: string | null;
  success: boolean;
  details: string | null;
  created_at: string;
}
