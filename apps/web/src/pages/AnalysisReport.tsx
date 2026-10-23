import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Report } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function AnalysisReport() {
  const { id } = useParams();
  const analysisId = Number(id);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getReport(analysisId)
      .then(setReport)
      .catch((e) => setError(e.message));
  }, [analysisId]);

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
    );
  }

  if (!report) {
    return <p className="text-sm text-slate-500">در حال بارگذاری...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/projects" className="text-sm text-brand-600 hover:underline">
          ← بازگشت به پروژه‌ها
        </Link>
        <h2 className="mt-2 text-2xl font-bold text-slate-800">
          گزارش تحلیل #{report.analysis.id}
        </h2>
        <p className="text-sm text-slate-500">
          {report.project.name} • {new Date(report.generated_at).toLocaleString("fa-IR")}
        </p>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
        <strong>سلب مسئولیت:</strong> {report.disclaimer}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard label="وضعیت کلی" value={<StatusBadge status={report.summary.overall_status} />} />
        <SummaryCard label="تعداد آزمون" value={report.summary.test_count} />
        <SummaryCard label="تأییدشده" value={report.summary.verified_count} />
        <SummaryCard label="شکست" value={report.summary.failed_count} />
      </div>

      <div className="card">
        <h3 className="mb-3 text-lg font-semibold">آزمون‌های هندسی</h3>
        {report.tests.length === 0 ? (
          <p className="text-sm text-slate-500">آزمونی ثبت نشده است.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-head">آزمون</th>
                <th className="table-head">وضعیت</th>
                <th className="table-head">مساحت (m²)</th>
                <th className="table-head">محیط (m)</th>
                <th className="table-head">CRS</th>
              </tr>
            </thead>
            <tbody>
              {report.tests.map((t, i) => (
                <tr key={i}>
                  <td className="table-cell">{t.name}</td>
                  <td className="table-cell"><StatusBadge status={t.status} /></td>
                  <td className="table-cell">{t.area_m2 ?? "—"}</td>
                  <td className="table-cell">{t.perimeter_m ?? "—"}</td>
                  <td className="table-cell font-mono text-xs">{t.crs || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3 className="mb-3 text-lg font-semibold">قواعد اعمال‌شده</h3>
        {report.rules_applied.length === 0 ? (
          <p className="text-sm text-slate-500">
            هیچ قاعده‌ای در سامانه ثبت نشده بود.
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-head">کد</th>
                <th className="table-head">نوع</th>
                <th className="table-head">وضعیت</th>
                <th className="table-head">آستانه</th>
                <th className="table-head">مقدار</th>
                <th className="table-head">مرجع</th>
              </tr>
            </thead>
            <tbody>
              {report.rules_applied.map((r, i) => (
                <tr key={i}>
                  <td className="table-cell">{r.rule_code}</td>
                  <td className="table-cell">{r.kind}</td>
                  <td className="table-cell"><StatusBadge status={r.status} /></td>
                  <td className="table-cell">{r.threshold ?? "—"}</td>
                  <td className="table-cell">{r.actual ?? "—"}</td>
                  <td className="table-cell text-xs">{r.source_reference || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {report.warnings.length > 0 && (
        <div className="card">
          <h3 className="mb-2 text-lg font-semibold">هشدارها</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-amber-700">
            {report.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h3 className="mb-2 text-lg font-semibold">محدودیت‌ها</h3>
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
          {report.limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <div className="mt-1 text-lg font-bold text-slate-800">{value}</div>
    </div>
  );
}