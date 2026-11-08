import { ReceiptText } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata = { title: "Transactions" };

export default function Transactions() {
  return (
    <>
      <h1 className="mb-6 text-2xl font-extrabold">Transactions</h1>
      <EmptyState
        icon={ReceiptText}
        title="No transactions yet"
        description="Send a voice note or receipt photo to your WhatsApp bot to record one."
      />
    </>
  );
}
