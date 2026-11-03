BEGIN;

CREATE OR REPLACE FUNCTION public.set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END $$;

-- PRODUCTS
CREATE TABLE IF NOT EXISTS public.products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  price NUMERIC(14,2) NOT NULL CHECK (price >= 0),
  image_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.products
  ADD COLUMN IF NOT EXISTS sku TEXT,
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
UPDATE public.products SET sku = 'SKU-' || upper(substr(replace(id::text,'-',''),1,8)) WHERE sku IS NULL;
ALTER TABLE public.products ALTER COLUMN sku SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_sku ON public.products(sku);
DROP TRIGGER IF EXISTS trg_products_upd ON public.products;
CREATE TRIGGER trg_products_upd BEFORE UPDATE ON public.products FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ORDERS
CREATE TABLE IF NOT EXISTS public.orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  total_price NUMERIC(14,2) NOT NULL CHECK (total_price >= 0),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','paid','failed','cancelled','expired')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.orders
  ALTER COLUMN product_id DROP NOT NULL,
  ADD COLUMN IF NOT EXISTS customer_phone TEXT,
  ADD COLUMN IF NOT EXISTS customer_name TEXT,
  ADD COLUMN IF NOT EXISTS wa_message_id TEXT,
  ADD COLUMN IF NOT EXISTS midtrans_order_id TEXT,
  ADD COLUMN IF NOT EXISTS midtrans_transaction_id TEXT,
  ADD COLUMN IF NOT EXISTS payment_url TEXT,
  ADD COLUMN IF NOT EXISTS payment_type TEXT,
  ADD COLUMN IF NOT EXISTS payment_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS receipt_path TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_wamid ON public.orders(wa_message_id) WHERE wa_message_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_mid ON public.orders(midtrans_order_id) WHERE midtrans_order_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_phone ON public.orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);
DROP TRIGGER IF EXISTS trg_orders_upd ON public.orders;
CREATE TRIGGER trg_orders_upd BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ORDER ITEMS (price snapshot)
CREATE TABLE IF NOT EXISTS public.order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
  product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
  sku TEXT NOT NULL,
  product_name TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(14,2) NOT NULL,
  subtotal NUMERIC(14,2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_items_order ON public.order_items(order_id);

-- CART (list messages select 1 row per tap, so the cart is server-side state)
CREATE TABLE IF NOT EXISTS public.cart_items (
  customer_phone TEXT NOT NULL,
  product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (customer_phone, product_id)
);

-- FINANCIAL RECORDS (idempotency key)
CREATE TABLE IF NOT EXISTS public.financial_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('income','expense')),
  domain TEXT NOT NULL CHECK (domain IN ('business','personal')),
  amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
  category TEXT, description TEXT,
  source TEXT NOT NULL DEFAULT 'manual',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.financial_records ADD COLUMN IF NOT EXISTS reference_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fin_ref ON public.financial_records(source, reference_id) WHERE reference_id IS NOT NULL;

-- RPC: add 1 unit (atomic upsert)
CREATE OR REPLACE FUNCTION public.add_to_cart(p_phone TEXT, p_sku TEXT) RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v_pid UUID; v_qty INTEGER;
BEGIN
  SELECT id INTO v_pid FROM products WHERE sku = p_sku AND is_active;
  IF v_pid IS NULL THEN RAISE EXCEPTION 'UNKNOWN_PRODUCT'; END IF;
  INSERT INTO cart_items(customer_phone, product_id, quantity) VALUES (p_phone, v_pid, 1)
  ON CONFLICT (customer_phone, product_id)
  DO UPDATE SET quantity = LEAST(cart_items.quantity + 1, 99), updated_at = now()
  RETURNING quantity INTO v_qty;
  RETURN v_qty;
END $$;

-- RPC: cart -> order (DB prices only, idempotent per WA message id, clears cart)
CREATE OR REPLACE FUNCTION public.checkout_cart(p_phone TEXT, p_name TEXT, p_wa_message_id TEXT)
RETURNS public.orders LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE v public.orders;
BEGIN
  SELECT * INTO v FROM orders WHERE wa_message_id = p_wa_message_id;
  IF FOUND THEN RETURN v; END IF;
  PERFORM 1 FROM cart_items c JOIN products p ON p.id = c.product_id AND p.is_active
    WHERE c.customer_phone = p_phone FOR UPDATE OF c;
  IF NOT FOUND THEN RAISE EXCEPTION 'EMPTY_CART'; END IF;
  INSERT INTO orders(customer_phone, customer_name, wa_message_id, quantity, total_price, status)
  SELECT p_phone, p_name, p_wa_message_id, SUM(c.quantity), SUM(c.quantity * p.price), 'pending'
  FROM cart_items c JOIN products p ON p.id = c.product_id AND p.is_active
  WHERE c.customer_phone = p_phone RETURNING * INTO v;
  INSERT INTO order_items(order_id, product_id, sku, product_name, quantity, unit_price, subtotal)
  SELECT v.id, p.id, p.sku, p.name, c.quantity, p.price, c.quantity * p.price
  FROM cart_items c JOIN products p ON p.id = c.product_id AND p.is_active
  WHERE c.customer_phone = p_phone;
  DELETE FROM cart_items WHERE customer_phone = p_phone;
  RETURN v;
END $$;

REVOKE ALL ON FUNCTION public.add_to_cart(TEXT,TEXT), public.checkout_cart(TEXT,TEXT,TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.add_to_cart(TEXT,TEXT), public.checkout_cart(TEXT,TEXT,TEXT) TO service_role;

ALTER TABLE public.products, public.orders, public.order_items, public.cart_items, public.financial_records ENABLE ROW LEVEL SECURITY;

INSERT INTO storage.buckets (id, name, public) VALUES ('receipts','receipts',false), ('product-images','product-images',true)
ON CONFLICT (id) DO NOTHING;

COMMIT;