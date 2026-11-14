begin;

alter table public.products add column if not exists image_path text;

alter table public.orders
  add column if not exists fulfillment_status text not null default 'new'
    check (fulfillment_status in ('new','preparing','ready','completed','cancelled')),
  add column if not exists fulfillment_note text,
  add column if not exists fulfilled_at timestamptz;
create index if not exists idx_orders_fulfillment on public.orders(status, fulfillment_status, created_at);

-- Backfill: paid orders older than 2 days are treated as already fulfilled so the board starts clean.
-- Adjust the interval (or remove) if you have real unfulfilled orders.
update public.orders set fulfillment_status = 'completed', fulfilled_at = coalesce(paid_at, created_at)
 where status = 'paid' and created_at < now() - interval '2 days';

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('product-images', 'product-images', true, 5242880, array['image/webp'])
on conflict (id) do update set public = true, file_size_limit = 5242880, allowed_mime_types = array['image/webp'];

commit;