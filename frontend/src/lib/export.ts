import { api, qs } from "@/lib/api";
import { catLabel } from "@/lib/format";
import type { FinanceRecord, Page } from "@/lib/types";

export interface RecordFilters {
  from: string;
  to: string;
  domain: string;
  type: string;
  category: string;
  q: string;
}

export async function fetchAll(
  f: RecordFilters,
  cap = 5000,
): Promise<FinanceRecord[]> {
  const out: FinanceRecord[] = [];
  for (let offset = 0; offset < cap; offset += 1000) {
    const p = await api<Page<FinanceRecord>>(
      `/finance/records${qs({ ...f, limit: 1000, offset })}`,
    );
    out.push(...p.items);
    if (out.length >= p.total || p.items.length < 1000) break;
  }
  return out;
}

const totals = (rows: FinanceRecord[]) => {
  const income = rows
    .filter((r) => r.type === "income")
    .reduce((s, r) => s + Number(r.amount), 0);
  const expense = rows
    .filter((r) => r.type === "expense")
    .reduce((s, r) => s + Number(r.amount), 0);
  return { income, expense, net: income - expense };
};
const cap1 = (s: string) => s[0].toUpperCase() + s.slice(1);

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function exportXlsx(rows: FinanceRecord[], f: RecordFilters) {
  const mod = await import("exceljs");
  const Workbook =
    mod.Workbook ??
    (mod as unknown as { default: typeof mod }).default.Workbook;
  const wb = new Workbook();
  wb.creator = "KasirChat.AI";
  const ws = wb.addWorksheet("Transactions", {
    views: [{ state: "frozen", ySplit: 1 }],
  });
  ws.columns = [
    {
      header: "Date",
      key: "date",
      width: 14,
      style: { numFmt: "dd mmm yyyy" },
    },
    { header: "Type", key: "type", width: 11 },
    { header: "Domain", key: "domain", width: 11 },
    { header: "Category", key: "category", width: 16 },
    { header: "Description", key: "description", width: 42 },
    { header: "Merchant", key: "merchant", width: 24 },
    {
      header: "Amount (IDR)",
      key: "amount",
      width: 18,
      style: { numFmt: "#,##0" },
    },
    { header: "Source", key: "source", width: 12 },
  ];
  const head = ws.getRow(1);
  head.height = 22;
  head.eachCell((c) => {
    c.font = { bold: true, color: { argb: "FFFFFFFF" } };
    c.fill = {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: "FF0EA5E9" },
    };
    c.alignment = { vertical: "middle" };
  });
  for (const r of rows) {
    const row = ws.addRow({
      date: new Date(`${r.transaction_date}T00:00:00Z`),
      type: cap1(r.type),
      domain: cap1(r.domain),
      category: catLabel(r.category),
      description: r.description ?? "",
      merchant: r.merchant ?? "",
      amount: Number(r.amount),
      source: r.source,
    });
    row.getCell("amount").font = {
      color: { argb: r.type === "income" ? "FF10B981" : "FFEF4444" },
    };
  }
  ws.autoFilter = { from: "A1", to: `H${rows.length + 1}` };

  const t = totals(rows);
  ws.addRow([]);
  for (const [label, v] of [
    ["Total income", t.income],
    ["Total expense", t.expense],
    ["Net", t.net],
  ] as const) {
    const r = ws.addRow({ description: label, amount: v });
    r.font = { bold: true };
  }
  const buf = await wb.xlsx.writeBuffer();
  save(
    new Blob([buf], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }),
    `transactions_${f.from}_${f.to}.xlsx`,
  );
}

export async function exportPdf(rows: FinanceRecord[], f: RecordFilters) {
  const { jsPDF } = await import("jspdf");
  const autoTable = (await import("jspdf-autotable")).default;
  const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
  const clean = (s?: string | null) =>
    (s ?? "").replace(/[^\u0020-\u00FF]/g, "").trim() || "-"; // core PDF fonts: Latin-1 only
  const rp = (n: number) =>
    `${n < 0 ? "-" : ""}Rp ${Math.abs(Math.round(n)).toLocaleString("id-ID")}`;
  const t = totals(rows);

  doc
    .setFont("helvetica", "bold")
    .setFontSize(16)
    .setTextColor(14, 165, 233)
    .text("KasirChat.AI - Transaction Report", 40, 44);
  doc
    .setFont("helvetica", "normal")
    .setFontSize(10)
    .setTextColor(100, 116, 139);
  const filt = [
    f.domain && `Domain: ${f.domain}`,
    f.type && `Type: ${f.type}`,
    f.category && `Category: ${catLabel(f.category)}`,
    f.q && `Search: ${clean(f.q)}`,
  ]
    .filter(Boolean)
    .join("  |  ");
  doc.text(`Period: ${f.from} to ${f.to}${filt ? `  |  ${filt}` : ""}`, 40, 62);
  doc
    .setTextColor(15, 23, 42)
    .setFont("helvetica", "bold")
    .text(
      `Income ${rp(t.income)}    Expense ${rp(t.expense)}    Net ${rp(t.net)}    (${rows.length} rows)`,
      40,
      80,
    );

  autoTable(doc, {
    startY: 96,
    margin: { left: 40, right: 40, bottom: 40 },
    head: [
      [
        "Date",
        "Type",
        "Domain",
        "Category",
        "Description",
        "Merchant",
        "Amount",
        "Source",
      ],
    ],
    body: rows.map((r) => [
      r.transaction_date,
      cap1(r.type),
      cap1(r.domain),
      catLabel(r.category),
      clean(r.description),
      clean(r.merchant),
      rp(Number(r.amount)),
      r.source,
    ]),
    styles: { fontSize: 8.5, cellPadding: 4, textColor: [15, 23, 42] },
    headStyles: {
      fillColor: [14, 165, 233],
      textColor: 255,
      fontStyle: "bold",
    },
    alternateRowStyles: { fillColor: [240, 249, 255] },
    columnStyles: {
      0: { cellWidth: 62 },
      1: { cellWidth: 52 },
      2: { cellWidth: 56 },
      3: { cellWidth: 80 },
      5: { cellWidth: 110 },
      6: { cellWidth: 92, halign: "right" },
      7: { cellWidth: 56 },
    },
    didParseCell: (d) => {
      if (d.section === "body" && d.column.index === 6) {
        d.cell.styles.textColor =
          (d.row.raw as string[])[1] === "Income"
            ? [16, 185, 129]
            : [239, 68, 68];
        d.cell.styles.fontStyle = "bold";
      }
    },
  });

  const n = doc.getNumberOfPages();
  for (let i = 1; i <= n; i++) {
    doc
      .setPage(i)
      .setFont("helvetica", "normal")
      .setFontSize(8)
      .setTextColor(100, 116, 139);
    doc.text(`Page ${i} / ${n}`, 802, 575, { align: "right" });
  }
  doc.save(`transactions_${f.from}_${f.to}.pdf`);
}
