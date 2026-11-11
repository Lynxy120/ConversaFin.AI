begin;
alter table public.financial_records
  add column if not exists transaction_date date not null default ((now() at time zone 'Asia/Jakarta')::date),
  add column if not exists merchant text,
  add column if not exists input_type text check (input_type in ('text','audio','image','manual','system')),
  add column if not exists confidence numeric(3,2) check (confidence between 0 and 1),
  add column if not exists raw_input text,
  add column if not exists created_by text;
create index if not exists idx_fin_domain_type_date on public.financial_records(domain, type, transaction_date desc);
commit;