export interface Product {
  id: string;
  retailer_id: string;
  name: string;
  description: string | null;
  price: string;
  currency: string;
  image_url: string | null;
  is_active: boolean;
  meta_synced_at: string | null;
  created_at: Date;
}