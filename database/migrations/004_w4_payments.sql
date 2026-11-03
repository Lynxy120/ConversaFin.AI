BEGIN;

ALTER TABLE public.orders
  ADD COLUMN IF NOT EXISTS paid_at                TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS payment_type           TEXT,
  ADD COLUMN IF NOT EXISTS midtrans_transaction_id TEXT,
  ADD COLUMN IF NOT EXISTS payment_expires_at     TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS receipt_path           TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_midtrans_order_id
  ON public.orders(midtrans_order_id) WHERE midtrans_order_id IS NOT NULL;

ALTER TABLE public.financial_records
  ADD COLUMN IF NOT EXISTS reference_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fin_source_ref
  ON public.financial_records(source, reference_id) WHERE reference_id IS NOT NULL;

COMMIT;