import { useEffect, useState } from "react";
import { getProducts } from "../services/api";
import type { Product } from "../types/product";

const idr = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });

export default function Products() {
  const [items, setItems] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProducts().then(setItems).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p>Error: {error}</p>;

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr><th>Image</th><th>SKU</th><th>Name</th><th>Price</th><th>Meta Sync</th></tr>
      </thead>
      <tbody>
        {items.map((p) => (
          <tr key={p.id}>
            <td>{p.image_url && <img src={p.image_url} alt={p.name} width={48} height={48} />}</td>
            <td>{p.retailer_id}</td>
            <td>{p.name}</td>
            <td>{idr.format(Number(p.price))}</td>
            <td>{p.meta_synced_at ? "synced" : "pending"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}