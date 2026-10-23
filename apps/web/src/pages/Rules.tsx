import { FormEvent, useEffect, useState } from "react";
import { api, Rule } from "../api/client";

const RULE_KINDS = [
  { value: "min_area", label: "حداقل مساحت (m²)" },
  { value: "max_area", label: "حداکثر مساحت (m²)" },
  { value: "min_perimeter", label: "حداقل محیط (m)" },
];

const kindLabels: Record<string, string> = {
  min_area: "حداقل مساحت",
  max_area: "حداکثر مساحت",
  min_perimeter: "حداقل محیط",
};

export function Rules() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("min_area");
  const [threshold, setThreshold] = useState("");
  const [sourceReference, setSourceReference] = useState("");
  const [documentNumber, setDocumentNumber] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setRules(await api.listRules());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const numericThreshold = Number(threshold);
    if (!Number.isFinite(numericThreshold)) {
      setError("آستانه باید عدد باشد.");
      return;
    }

    setSubmitting(true);
    try {
      await api.createRule({
        code: code.trim(),
        title: title.trim(),
        kind,
        threshold: numericThreshold,
        source_reference: sourceReference.trim() || undefined,
        document_number: documentNumber.trim() || undefined,
        version: version.trim() || "1.0.0",
        description: description.trim() || undefined,
      });
      setCode("");
      setTitle("");
      setKind("min_area");
      setThreshold("");
      setSourceReference("");
      setDocumentNumber("");
      setVersion("1.0.0");
      setDescription("");
      setShowForm(false);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function verifyRule(id: number) {
    try {
      await api.verifyRule(id);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function deactivateRule(id: number) {
    try {
      await api.deactivateRule(id);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">قواعد شهرداری</h2>
          <p className="text-sm text-slate-500">
            قواعد داده‌محور با مرجع قانونی و نسخه. تا زمانی که تأیید نشده باشند،
            در تحلیل‌ها اعمال نمی‌شوند.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "انصراف" : "قاعده جدید"}
        </button>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
        <strong>توجه:</strong> قاعده تأییدنشده (بدون تیک «تأییدشده») در تحلیل‌ها
        نتیجه <em>needs_review</em> تولید می‌کند و به‌عنوان معتبر اعمال نمی‌شود.
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">کد قاعده (یکتا)</label>
              <input
                className="input"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="MIN_AREA_100"
                required
                dir="ltr"
              />
            </div>
            <div>
              <label className="label">عنوان</label>
              <input
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="حداقل مساحت قطعه"
                required
              />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">نوع</label>
              <select
                className="input"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                {RULE_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">آستانه (عدد)</label>
              <input
                className="input"
                type="number"
                step="any"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                required
                dir="ltr"
              />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">مرجع قانونی (اختیاری)</label>
              <input
                className="input"
                value={sourceReference}
                onChange={(e) => setSourceReference(e.target.value)}
                placeholder="ماده ۱۲ آیین‌نامه..."
              />
            </div>
            <div>
              <label className="label">شماره سند (اختیاری)</label>
              <input
                className="input"
                value={documentNumber}
                onChange={(e) => setDocumentNumber(e.target.value)}
                placeholder="۱۲۳۴۵/ت"
                dir="ltr"
              />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">نسخه</label>
              <input
                className="input"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                dir="ltr"
              />
            </div>
            <div>
              <label className="label">توضیحات (اختیاری)</label>
              <input
                className="input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "در حال ایجاد..." : "ایجاد قاعده"}
          </button>
        </form>
      )}

      <div className="card overflow-hidden p-0">
        {loading ? (
          <p className="p-6 text-sm text-slate-500">در حال بارگذاری...</p>
        ) : rules.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">
            هنوز قاعده‌ای ثبت نشده است. با دکمه «قاعده جدید» شروع کنید.
          </p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-head">کد</th>
                <th className="table-head">عنوان</th>
                <th className="table-head">نوع</th>
                <th className="table-head">آستانه</th>
                <th className="table-head">وضعیت</th>
                <th className="table-head">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="table-cell font-mono text-xs">{r.code}</td>
                  <td className="table-cell">{r.title}</td>
                  <td className="table-cell">{kindLabels[r.kind] || r.kind}</td>
                  <td className="table-cell">{r.threshold}</td>
                  <td className="table-cell">
                    <div className="flex flex-wrap gap-1">
                      {r.is_active ? (
                        <span className="inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                          فعال
                        </span>
                      ) : (
                        <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                          غیرفعال
                        </span>
                      )}
                      {r.is_verified ? (
                        <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                          تأییدشده
                        </span>
                      ) : (
                        <span className="inline-block rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                          تأییدنشده
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex flex-wrap gap-2">
                      {!r.is_verified && (
                        <button
                          className="text-xs text-brand-600 hover:underline"
                          onClick={() => verifyRule(r.id)}
                        >
                          تأیید
                        </button>
                      )}
                      {r.is_active && (
                        <button
                          className="text-xs text-red-600 hover:underline"
                          onClick={() => deactivateRule(r.id)}
                        >
                          غیرفعال‌سازی
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}