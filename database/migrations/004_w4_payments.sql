begin;
alter table public.orders
  add column if not exists midtrans_order_id text,
  add column if not exists midtrans_transaction_id text,
  add column if not exists payment_url text,
  add column if not exists payment_type text,
  add column if not exists payment_expires_at timestamptz,
  add column if not exists paid_at timestamptz,
  add column if not exists receipt_path text;
create unique index if not exists uq_orders_mid on public.orders(midtrans_order_id) where midtrans_order_id is not null;

create table if not exists public.financial_records (
  id           uuid primary key default gen_random_uuid(),
  type         text not null check (type in ('income','expense')),
  domain       text not null check (domain in ('business','personal')),
  amount       numeric(14,2) not null check (amount >= 0),
  category     text,
  description  text,
  source       text not null default 'manual',
  reference_id text,
  created_at   timestamptz not null default now()
);
create unique index if not exists uq_fin_source_ref on public.financial_records(source, reference_id);  -- idempotency (NULLs allowed)
alter table public.financial_records enable row level security;

insert into storage.buckets (id, name, public) values ('receipts','receipts',false) on conflict (id) do nothing;
commit;