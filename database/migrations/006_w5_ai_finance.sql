BEGIN;

ALTER TABLE public.financial_records
  ADD COLUMN IF NOT EXISTS transaction_date DATE NOT NULL DEFAULT ((now() AT TIME ZONE 'Asia/Jakarta')::date),
  ADD COLUMN IF NOT EXISTS merchant   TEXT,
  ADD COLUMN IF NOT EXISTS input_type TEXT CHECK (input_type IN ('text','audio','image','manual','system')),
  ADD COLUMN IF NOT EXISTS confidence NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
  ADD COLUMN IF NOT EXISTS raw_input  TEXT,
  ADD COLUMN IF NOT EXISTS created_by TEXT,
  ADD COLUMN IF NOT EXISTS reference_id TEXT;

-- Partial unique indexes cannot be used by ON CONFLICT (source, reference_id).
-- A full unique index still allows many NULL reference_ids.
DROP INDEX IF EXISTS public.uq_fin_ref;
DROP INDEX IF EXISTS public.uq_fin_source_ref;
CREATE UNIQUE INDEX IF NOT EXISTS uq_fin_source_ref_full ON public.financial_records(source, reference_id);

CREATE INDEX IF NOT EXISTS idx_fin_domain_type_date
  ON public.financial_records(domain, type, transaction_date DESC);

COMMIT;