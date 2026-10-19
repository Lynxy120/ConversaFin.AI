import type { Product } from '../types/product';

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getProducts(): Promise<Product[]> {
    const res = await fetch(`${BASE}/api/v1/products`);
    if (!res.ok) throw new Error(`Failed to fetch products: ${res.status}`);
    return res.json();
}