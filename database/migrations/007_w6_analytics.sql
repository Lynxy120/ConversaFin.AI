BEGIN;

CREATE OR REPLACE FUNCTION public.finance_timeseries(p_from date, p_to date, p_domain text DEFAULT NULL)
RETURNS TABLE(day date, income numeric, expense numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT g.d::date,
         COALESCE(SUM(f.amount) FILTER (WHERE f.type = 'income'), 0),
         COALESCE(SUM(f.amount) FILTER (WHERE f.type = 'expense'), 0)
  FROM generate_series(p_from::timestamp, p_to::timestamp, interval '1 day') AS g(d)
  LEFT JOIN public.financial_records f
    ON f.transaction_date = g.d::date AND (p_domain IS NULL OR f.domain = p_domain)
  GROUP BY g.d ORDER BY g.d;
$$;

CREATE OR REPLACE FUNCTION public.finance_by_category(p_from date, p_to date, p_domain text DEFAULT NULL)
RETURNS TABLE(category text, type text, total numeric, n bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT COALESCE(f.category, 'other'), f.type, SUM(f.amount), COUNT(*)
  FROM public.financial_records f
  WHERE f.transaction_date BETWEEN p_from AND p_to AND (p_domain IS NULL OR f.domain = p_domain)
  GROUP BY 1, 2 ORDER BY 3 DESC;
$$;

REVOKE ALL ON FUNCTION public.finance_timeseries(date,date,text), public.finance_by_category(date,date,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.finance_timeseries(date,date,text), public.finance_by_category(date,date,text) TO service_role;

COMMIT;