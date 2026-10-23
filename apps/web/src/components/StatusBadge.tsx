interface Props {
  status: string;
}

const colors: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-700",
  partial: "bg-amber-100 text-amber-700",
  needs_review: "bg-orange-100 text-orange-700",
  failed: "bg-red-100 text-red-700",
  not_applicable: "bg-slate-100 text-slate-600",
  parsed: "bg-blue-100 text-blue-700",
  uploaded: "bg-slate-100 text-slate-600",
  pending: "bg-slate-100 text-slate-600",
  unsupported: "bg-slate-200 text-slate-600",
  running: "bg-blue-100 text-blue-700",
};

const labels: Record<string, string> = {
  verified: "تأییدشده",
  partial: "جزئی",
  needs_review: "نیازمند بررسی",
  failed: "شکست",
  not_applicable: "بی‌ربط",
  parsed: "پردازش‌شده",
  uploaded: "آپلودشده",
  pending: "در انتظار",
  unsupported: "پشتیبانی‌نشده",
  running: "در حال اجرا",
};

export function StatusBadge({ status }: Props) {
  const cls = colors[status] || "bg-slate-100 text-slate-700";
  const label = labels[status] || status;
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}