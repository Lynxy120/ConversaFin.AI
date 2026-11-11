create extension if not exists pgcrypto;

create or replace function public.set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

create table if not exists public.products (
  id          uuid primary key default gen_random_uuid(),
  sku         text not null unique,
  name        text not null,
  description text,
  price       numeric(14,2) not null check (price >= 0),
  image_url   text,
  is_active   boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
drop trigger if exists trg_products_upd on public.products;
create trigger trg_products_upd before update on public.products
  for each row execute function public.set_updated_at();
create index if not exists idx_products_active on public.products(is_active, created_at);
alter table public.products enable row level security;