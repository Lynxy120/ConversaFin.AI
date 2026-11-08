import { Package } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { Fab } from "@/components/ui/fab";

export const metadata = { title: "Catalog" };

export default function Catalog() {
  return (
    <>
      <h1 className="mb-6 text-2xl font-extrabold">Catalog</h1>
      <EmptyState
        icon={Package}
        title="No products yet"
        description="Add your best-sellers now!"
      />
      <Fab label="Add product" />
    </>
  );
}
