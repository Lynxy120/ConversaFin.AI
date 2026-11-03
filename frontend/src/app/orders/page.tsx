import { api, idr } from "@/lib/api";

type O = { id: string; customer_phone: string; total_price: string; status: string; paid_at: string | null;
           order_items: { product_name: string; quantity: number }[] };
export const dynamic = "force-dynamic";

export default async function Orders() {
  const rows = await api<O[]>("/orders?limit=50");
  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Orders</h1>
      <table className="w-full text-left text-sm">
        <thead><tr><th>ID</th><th>Phone</th><th>Items</th><th>Total</th><th>Status</th><th>Paid</th></tr></thead>
        <tbody>{rows.map((o) => (
          <tr key={o.id} className="border-t">
            <td>#{o.id.slice(0, 8).toUpperCase()}</td><td>{o.customer_phone}</td>
            <td>{o.order_items.map((i) => `${i.product_name} x${i.quantity}`).join(", ")}</td>
            <td>{idr(o.total_price)}</td><td>{o.status}</td><td>{o.paid_at?.slice(0, 16).replace("T", " ") ?? "-"}</td>
          </tr>))}</tbody>
      </table>
    </main>
  );
}