begin;

create table if not exists public.finance_accounts (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  type text not null check (type in ('cash','bank','ewallet','savings')),
  initial_balance numeric(14,2) not null default 0,
  is_default boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
create unique index if not exists uq_fin_acc_name on public.finance_accounts (lower(name));
create unique index if not exists uq_fin_acc_default on public.finance_accounts (is_default) where is_default;
insert into public.finance_accounts (name, type, is_default) values ('Cash', 'cash', true) on conflict do nothing;

create table if not exists public.finance_debts (
  id uuid primary key default gen_random_uuid(),
  category text not null,
  description text,
  total_amount numeric(14,2) not null check (total_amount > 0),
  paid_amount numeric(14,2) not null default 0 check (paid_amount >= 0),
  monthly_payment numeric(14,2) not null default 0 check (monthly_payment >= 0),
  status text not null default 'active' check (status in ('active','paid')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.finance_budgets (
  id uuid primary key default gen_random_uuid(),
  month text not null default 'default' check (month = 'default' or month ~ '^\d{4}-(0[1-9]|1[0-2])$'),
  group_type text not null check (group_type in ('pemasukan','tagihan','pengeluaran_harian','tabungan')),
  category text not null,
  budget_amount numeric(14,2) not null default 0 check (budget_amount >= 0),
  total_target numeric(14,2),
  start_date date,
  target_date date,
  created_at timestamptz not null default now(),
  unique (month, group_type, category)
);

alter table public.finance_accounts enable row level security;
alter table public.finance_debts    enable row level security;
alter table public.finance_budgets  enable row level security;

-- financial_records: drop old CHECKs on type/source, then widen
do $$
declare c record;
begin
  for c in select conname from pg_constraint
           where conrelid = 'public.financial_records'::regclass and contype = 'c'
             and pg_get_constraintdef(oid) ~ '\m(type|source)\M'
  loop
    execute format('alter table public.financial_records drop constraint %I', c.conname);
  end loop;
end $$;
alter table public.financial_records add constraint financial_records_type_check check (type in ('income','expense','in','out'));

alter table public.financial_records
  add column if not exists account_id uuid references public.finance_accounts(id) on delete set null,
  add column if not exists debt_id uuid references public.finance_debts(id) on delete set null,
  add column if not exists notes text,
  add column if not exists group_type text
    check (group_type in ('pemasukan','tagihan','pengeluaran_harian','tabungan','hutang'));

update public.financial_records
   set group_type = case type when 'income' then 'pemasukan' when 'expense' then 'pengeluaran_harian' end
 where group_type is null and type in ('income','expense');
update public.financial_records set account_id = (select id from public.finance_accounts where is_default)
 where account_id is null;

create or replace function public.fin_defaults() returns trigger language plpgsql as $$
begin
  if new.group_type is null then
    new.group_type := case new.type when 'income' then 'pemasukan' when 'expense' then 'pengeluaran_harian' else null end;
  end if;
  if new.account_id is null then
    select id into new.account_id from public.finance_accounts where is_default limit 1;
  end if;
  return new;
end $$;
drop trigger if exists trg_fin_defaults on public.financial_records;
create trigger trg_fin_defaults before insert on public.financial_records
  for each row execute function public.fin_defaults();

create index if not exists idx_fin_account on public.financial_records(account_id);
create index if not exists idx_fin_group_date on public.financial_records(group_type, transaction_date desc);

-- month x type x group x category (no account detail, keeps row count small)
create or replace function public.finance_flows(p_from date, p_to date)
returns table (month text, type text, group_type text, category text, is_savings boolean, total numeric)
language sql stable security definer set search_path = public as $$
  select to_char(r.transaction_date, 'YYYY-MM'), r.type, r.group_type,
         lower(coalesce(nullif(trim(r.category), ''), 'lainnya')),
         coalesce(a.type = 'savings', false), sum(r.amount)
  from public.financial_records r left join public.finance_accounts a on a.id = r.account_id
  where r.transaction_date between p_from and p_to
  group by 1, 2, 3, 4, 5
$$;

-- all-time per account: balances and savings-goal progress
create or replace function public.finance_balance_flows()
returns table (account_id uuid, type text, group_type text, category text, total numeric)
language sql stable security definer set search_path = public as $$
  select r.account_id, r.type, r.group_type,
         lower(coalesce(nullif(trim(r.category), ''), 'lainnya')), sum(r.amount)
  from public.financial_records r where r.account_id is not null
  group by 1, 2, 3, 4
$$;

-- net movement of non-savings pockets before a date (opening cash for the yearly matrix)
create or replace function public.finance_net_before(p_before date)
returns numeric language sql stable security definer set search_path = public as $$
  select coalesce(sum(case when r.type in ('income','in') then r.amount else -r.amount end), 0)
  from public.financial_records r left join public.finance_accounts a on a.id = r.account_id
  where r.transaction_date < p_before and coalesce(a.type, 'cash') <> 'savings'
$$;

-- atomic debt payment: ledger row + paid_amount in one transaction
create or replace function public.finance_pay_debt(p_debt uuid, p_amount numeric, p_account uuid, p_date date, p_notes text)
returns public.finance_debts language plpgsql security definer set search_path = public as $$
declare d public.finance_debts;
begin
  select * into d from public.finance_debts where id = p_debt for update;
  if not found then raise exception 'debt_not_found' using errcode = 'P0002'; end if;
  if p_amount <= 0 or p_amount > d.total_amount - d.paid_amount then
    raise exception 'invalid_amount' using errcode = '22023';
  end if;
  insert into public.financial_records
    (type, domain, amount, category, description, source, group_type, account_id, transaction_date, notes, debt_id)
  values ('expense', 'personal', p_amount, lower(d.category),
          'Pembayaran hutang: ' || coalesce(d.description, d.category), 'web', 'hutang',
          coalesce(p_account, (select id from public.finance_accounts where is_default)), p_date, p_notes, p_debt);
  update public.finance_debts
     set paid_amount = paid_amount + p_amount,
         status = case when paid_amount + p_amount >= total_amount then 'paid' else 'active' end,
         updated_at = now()
   where id = p_debt returning * into d;
  return d;
end $$;

revoke all on function public.finance_flows(date, date), public.finance_balance_flows(),
  public.finance_net_before(date), public.finance_pay_debt(uuid, numeric, uuid, date, text)
  from public, anon, authenticated;
grant execute on function public.finance_flows(date, date), public.finance_balance_flows(),
  public.finance_net_before(date), public.finance_pay_debt(uuid, numeric, uuid, date, text)
  to service_role;

commit;