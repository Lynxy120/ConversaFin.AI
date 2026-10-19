BEGIN;

CREATE OR REPLACE FUNCTION public.set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$;

-- PRODUCTS
ALTER TABLE public.products
  ADD COLUMN IF NOT EXISTS retailer_id    TEXT,
  ADD COLUMN IF NOT EXISTS description    TEXT,
  ADD COLUMN IF NOT EXISTS currency       TEXT NOT NULL DEFAULT 'IDR',
  ADD COLUMN IF NOT EXISTS is_active      BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS meta_synced_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE public.products
SET retailer_id = 'SKU-' || upper(substr(replace(id::text, '-', ''), 1, 8))
WHERE retailer_id IS NULL;

ALTER TABLE public.products ALTER COLUMN retailer_id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_retailer_id ON public.products(retailer_id);
CREATE INDEX IF NOT EXISTS idx_products_active ON public.products(is_active) WHERE is_active;

DROP TRIGGER IF EXISTS trg_products_updated_at ON public.products;
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON public.products
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ORDERS (multi-item cart: product_id becomes legacy/nullable, items live in order_items)
ALTER TABLE public.orders
  ALTER COLUMN product_id DROP NOT NULL,
  ADD COLUMN IF NOT EXISTS customer_phone    TEXT,
  ADD COLUMN IF NOT EXISTS customer_name     TEXT,
  ADD COLUMN IF NOT EXISTS wa_message_id     TEXT,
  ADD COLUMN IF NOT EXISTS catalog_id        TEXT,
  ADD COLUMN IF NOT EXISTS currency          TEXT NOT NULL DEFAULT 'IDR',
  ADD COLUMN IF NOT EXISTS customer_note     TEXT,
  ADD COLUMN IF NOT EXISTS midtrans_order_id TEXT,
  ADD COLUMN IF NOT EXISTS payment_url       TEXT,
  ADD COLUMN IF NOT EXISTS updated_at        TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_wa_message_id
  ON public.orders(wa_message_id) WHERE wa_message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON public.orders(customer_phone);

DROP TRIGGER IF EXISTS trg_orders_updated_at ON public.orders;
CREATE TRIGGER trg_orders_updated_at BEFORE UPDATE ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ORDER ITEMS
CREATE TABLE IF NOT EXISTS public.order_items (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id      UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
  product_id    UUID REFERENCES public.products(id) ON DELETE SET NULL,
  retailer_id   TEXT NOT NULL,
  product_name  TEXT NOT NULL,
  quantity      INTEGER NOT NULL CHECK (quantity > 0),
  unit_price    NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
  subtotal      NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items(order_id);
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

-- ATOMIC, IDEMPOTENT ORDER CREATION (prices are always taken from DB, never from the WA payload)
CREATE OR REPLACE FUNCTION public.create_order(
  p_customer_phone TEXT,
  p_customer_name  TEXT,
  p_wa_message_id  TEXT,
  p_catalog_id     TEXT,
  p_note           TEXT,
  p_items          JSONB
) RETURNS public.orders
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_order   public.orders;
  v_missing TEXT[];
BEGIN
  IF p_items IS NULL OR jsonb_typeof(p_items) <> 'array' OR jsonb_array_length(p_items) = 0 THEN
    RAISE EXCEPTION 'INVALID_ITEMS: empty cart';
  END IF;

  IF EXISTS (
    SELECT 1 FROM jsonb_array_elements(p_items) i
    WHERE COALESCE((i->>'quantity')::int, 0) <= 0 OR COALESCE(i->>'retailer_id', '') = ''
  ) THEN
    RAISE EXCEPTION 'INVALID_ITEMS: bad quantity or retailer_id';
  END IF;

  SELECT * INTO v_order FROM public.orders WHERE wa_message_id = p_wa_message_id;
  IF FOUND THEN RETURN v_order; END IF;

  SELECT array_agg(r.retailer_id) INTO v_missing
  FROM (SELECT DISTINCT i->>'retailer_id' AS retailer_id FROM jsonb_array_elements(p_items) i) r
  LEFT JOIN public.products p ON p.retailer_id = r.retailer_id AND p.is_active
  WHERE p.id IS NULL;

  IF v_missing IS NOT NULL THEN
    RAISE EXCEPTION 'UNKNOWN_PRODUCTS: %', array_to_string(v_missing, ',');
  END IF;

  BEGIN
    INSERT INTO public.orders
      (customer_phone, customer_name, wa_message_id, catalog_id, customer_note, quantity, total_price, status)
    SELECT p_customer_phone, p_customer_name, p_wa_message_id, p_catalog_id, p_note,
           SUM(r.quantity)::int, SUM(r.quantity * p.price), 'pending'
    FROM (SELECT i->>'retailer_id' AS retailer_id, SUM((i->>'quantity')::int) AS quantity
          FROM jsonb_array_elements(p_items) i GROUP BY 1) r
    JOIN public.products p ON p.retailer_id = r.retailer_id
    RETURNING * INTO v_order;
  EXCEPTION WHEN unique_violation THEN
    SELECT * INTO v_order FROM public.orders WHERE wa_message_id = p_wa_message_id;
    RETURN v_order;
  END;

  INSERT INTO public.order_items (order_id, product_id, retailer_id, product_name, quantity, unit_price, subtotal)
  SELECT v_order.id, p.id, p.retailer_id, p.name, r.quantity, p.price, r.quantity * p.price
  FROM (SELECT i->>'retailer_id' AS retailer_id, SUM((i->>'quantity')::int) AS quantity
        FROM jsonb_array_elements(p_items) i GROUP BY 1) r
  JOIN public.products p ON p.retailer_id = r.retailer_id;

  RETURN v_order;
END $$;

REVOKE ALL ON FUNCTION public.create_order(TEXT,TEXT,TEXT,TEXT,TEXT,JSONB) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.create_order(TEXT,TEXT,TEXT,TEXT,TEXT,JSONB) TO service_role;

COMMIT;