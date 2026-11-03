import { api, idr } from "@/lib/api";

type P = { id: string; sku: string; name: string; price: string; is_active: boolean };
export const dynamic = "force-dynamic";

export default async function Products() {
  const items = await api<P[]>("/products?limit=10");
  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Products (WA list: max 10)</h1>
      <table className="w-full text-left text-sm">
        <thead><tr><th>SKU</th><th>Name</th><th>Price</th></tr></thead>
        <tbody>{items.map((p) => (<tr key={p.id} className="border-t"><td>{p.sku}</td><td>{p.name}</td><td>{idr(p.price)}</td></tr>))}</tbody>
      </table>
    </main>
  );
}