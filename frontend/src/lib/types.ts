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
export type Bucket = "unpaid" | "new" | "preparing" | "ready";
export type Fulfillment =
  | "new"
  | "preparing"
  | "ready"
  | "completed"
  | "cancelled";
export interface OrderItem {
  id: string;
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: number | string;
  subtotal: number | string;
}
export interface Order {
  id: string;
  chat_id: string;
  customer_name: string | null;
  status: "pending" | "paid" | "failed" | "cancelled" | "expired";
  fulfillment_status: Fulfillment;
  total_price: number | string;
  created_at: string;
  paid_at: string | null;
  payment_expires_at: string | null;
  fulfillment_note: string | null;
  order_items: OrderItem[];
}
export interface TaskBoard {
  counts: Record<Bucket, number>;
  items: Order[];
}

export type Severity = "high" | "medium" | "low" | "positive";
export interface Insight {
  id: string;
  severity: Severity;
  category: string;
  title: string;
  detail: string;
  action: string;
  impact: string | null;
}
export interface BestSeller {
  sku: string;
  name: string;
  units: number;
  revenue: number;
  share: number;
  prev_units: number;
  trend: number | null;
}
export interface CustomerStats {
  unique: number;
  returning: number;
  repeat_rate: number;
  returning_revenue: number;
  new_revenue: number;
  hours: number[];
  weekdays: number[];
  peak_hour: number | null;
  peak_day: string | null;
  avg_items: number;
  bundles: {
    a: string;
    b: string;
    count: number;
    lift: number;
    bundle_price: number;
  }[];
  top: { name: string; orders: number; spend: number }[];
}
export interface Insights {
  has_data: boolean;
  from: string;
  to: string;
  days: number;
  health: {
    score: number;
    label: string;
    parts: {
      key: string;
      label: string;
      value: number | null;
      score: number;
    }[];
  };
  kpis: {
    revenue: number;
    revenue_delta: number | null;
    orders: number;
    orders_delta: number | null;
    aov: number;
    aov_delta: number | null;
    income: number;
    expense: number;
    profit: number;
    margin: number | null;
    conversion_rate: number | null;
    expiry_rate: number | null;
    pending_amount: number;
    pending_count: number;
  };
  best_sellers: BestSeller[];
  slow_movers: { sku: string; name: string }[];
  customers: CustomerStats;
  recommendations: Insight[];
}

export type PocketType = "cash" | "bank" | "ewallet" | "savings";
export type TxType = "income" | "expense" | "in" | "out";
export interface Account {
  id: string;
  name: string;
  type: PocketType;
  initial_balance: number | string;
  is_default: boolean;
  is_active: boolean;
}
export interface Pocket {
  id: string;
  name: string;
  type: PocketType;
  balance: number;
  is_default: boolean;
}
export interface BudgetRow {
  category: string;
  budget: number;
  actual: number;
  pct: number | null;
  total_target?: number | null;
  saved?: number;
  goal_pct?: number | null;
  start_date?: string | null;
  target_date?: string | null;
}
export interface DebtRow {
  id: string;
  category: string;
  description: string | null;
  total_amount: number;
  paid_amount: number;
  remaining: number;
  monthly_payment: number;
  pct: number;
  status: "active" | "paid";
}
export interface Budget {
  id: string;
  month: string;
  group_type: "pemasukan" | "tagihan" | "pengeluaran_harian" | "tabungan";
  category: string;
  budget_amount: number | string;
  total_target: number | string | null;
  start_date: string | null;
  target_date: string | null;
}
export interface CashDashboard {
  month: string;
  balance: {
    total: number;
    cash: number;
    savings: number;
    debt_remaining: number;
  };
  pockets: Pocket[];
  summary: { key: string; label: string; budget: number; actual: number }[];
  sisa: { budget: number; actual: number };
  ratio: { income: number; expense: number; pct: number | null };
  groups: Record<
    "pemasukan" | "tagihan" | "pengeluaran_harian" | "tabungan",
    BudgetRow[]
  >;
  debts: DebtRow[];
}
export interface YearRow {
  key?: string;
  category?: string;
  label?: string;
  values: (number | null)[];
  total: number | null;
}
export interface Yearly {
  year: number;
  income: YearRow[];
  expense: YearRow[];
  summary: YearRow[];
}
export interface LedgerRow {
  id: string;
  type: TxType;
  transaction_date: string;
  category: string | null;
  description: string | null;
  amount: number | string;
  notes: string | null;
  group_type: string | null;
  debt_id: string | null;
  finance_accounts: { name: string; type: PocketType } | null;
}
export interface LedgerPage {
  items: LedgerRow[];
  total: number;
}
