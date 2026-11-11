begin;

create table if not exists public.orders (
  id            uuid primary key default gen_random_uuid(),
  chat_id       text not null,
  customer_name text,
  source_ref    text unique,
  quantity      integer not null check (quantity > 0),
  total_price   numeric(14,2) not null check (total_price >= 0),
  status        text not null default 'pending' check (status in ('pending','paid','failed','cancelled','expired')),
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_orders_chat   on public.orders(chat_id);
create index if not exists idx_orders_status on public.orders(status, created_at desc);
drop trigger if exists trg_orders_upd on public.orders;
create trigger trg_orders_upd before update on public.orders for each row execute function public.set_updated_at();

create table if not exists public.order_items (
  id           uuid primary key default gen_random_uuid(),
  order_id     uuid not null references public.orders(id) on delete cascade,
  product_id   uuid references public.products(id) on delete set null,
  sku          text not null,
  product_name text not null,
  quantity     integer not null check (quantity > 0),
  unit_price   numeric(14,2) not null,
  subtotal     numeric(14,2) not null,
  created_at   timestamptz not null default now()
);
create index if not exists idx_items_order on public.order_items(order_id);

create table if not exists public.cart_items (
  chat_id    text not null,
  product_id uuid not null references public.products(id) on delete cascade,
  quantity   integer not null check (quantity > 0),
  updated_at timestamptz not null default now(),
  primary key (chat_id, product_id)
);

create or replace function public.add_to_cart(p_chat text, p_product uuid) returns integer
language plpgsql security definer set search_path = public as $$
declare v_qty integer;
begin
  if not exists (select 1 from products where id = p_product and is_active) then raise exception 'UNKNOWN_PRODUCT'; end if;
  insert into cart_items(chat_id, product_id, quantity) values (p_chat, p_product, 1)
  on conflict (chat_id, product_id) do update set quantity = least(cart_items.quantity + 1, 99), updated_at = now()
  returning quantity into v_qty;
  return v_qty;
end $$;

-- cart -> order: DB prices only, idempotent per source_ref, clears cart
create or replace function public.checkout_cart(p_chat text, p_name text, p_ref text) returns public.orders
language plpgsql security definer set search_path = public as $$
declare v public.orders;
begin
  select * into v from orders where source_ref = p_ref;
  if found then return v; end if;
  perform 1 from cart_items c join products p on p.id = c.product_id and p.is_active where c.chat_id = p_chat for update of c;
  if not found then raise exception 'EMPTY_CART'; end if;
  insert into orders(chat_id, customer_name, source_ref, quantity, total_price)
  select p_chat, p_name, p_ref, sum(c.quantity), sum(c.quantity * p.price)
  from cart_items c join products p on p.id = c.product_id and p.is_active where c.chat_id = p_chat returning * into v;
  insert into order_items(order_id, product_id, sku, product_name, quantity, unit_price, subtotal)
  select v.id, p.id, p.sku, p.name, c.quantity, p.price, c.quantity * p.price
  from cart_items c join products p on p.id = c.product_id and p.is_active where c.chat_id = p_chat;
  delete from cart_items where chat_id = p_chat;
  return v;
end $$;

revoke all on function public.add_to_cart(text,uuid), public.checkout_cart(text,text,text) from public, anon, authenticated;
grant execute on function public.add_to_cart(text,uuid), public.checkout_cart(text,text,text) to service_role;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.cart_items enable row level security;

commit;