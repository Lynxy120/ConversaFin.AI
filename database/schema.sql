-- PRODUCTS
CREATE TABLE IF NOT EXISTS public.products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    price       NUMERIC(14,2) NOT NULL CHECK (price >= 0),
    image_url   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ORDERS
CREATE TABLE IF NOT EXISTS public.orders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id   UUID NOT NULL REFERENCES public.products(id) ON DELETE RESTRICT,
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    total_price  NUMERIC(14,2) NOT NULL CHECK (total_price >= 0),
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','paid','failed','cancelled','expired')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- FINANCIAL RECORDS
CREATE TABLE IF NOT EXISTS public.financial_records (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type         TEXT NOT NULL CHECK (type IN ('income','expense')),
    domain       TEXT NOT NULL CHECK (domain IN ('business','personal')),
    amount       NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    category     TEXT,
    description  TEXT,
    source       TEXT NOT NULL DEFAULT 'manual',  -- manual | whatsapp | midtrans | ai
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_orders_product_id     ON public.orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_status         ON public.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at     ON public.orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fin_type_domain       ON public.financial_records(type, domain);
CREATE INDEX IF NOT EXISTS idx_fin_created_at        ON public.financial_records(created_at DESC);

-- RLS (backend uses service-role key, which bypasses RLS; blocks anon access)
ALTER TABLE public.products          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_records ENABLE ROW LEVEL SECURITY;

-- SEED (optional)
INSERT INTO public.products (name, price, image_url)
VALUES ('Sample Product', 25000, NULL);