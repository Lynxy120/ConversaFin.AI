export type Domain = "business" | "personal";
export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  price: number | string;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
}
export interface FinanceRecord {
  id: string;
  type: "income" | "expense";
  domain: Domain;
  amount: number;
  category: string | null;
  description: string | null;
  merchant: string | null;
  transaction_date: string;
  source: string;
  input_type: string | null;
  confidence: number | null;
  created_at: string;
}
export interface Summary {
  from: string;
  to: string;
  income: number;
  expense: number;
  profit: number;
  pending_orders: number;
  series: { day: string; income: number; expense: number }[];
  categories: { category: string; type: string; total: number; n: number }[];
}
export interface Page<T> {
  items: T[];
  total: number;
}
