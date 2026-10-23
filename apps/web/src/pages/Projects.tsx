import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, Project } from "../api/client";

export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [parcelCode, setParcelCode] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function refresh() {
    setLoading(true);
    try {
      const data = await api.listProjects();
      setProjects(data);
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
    setSubmitting(true);
    try {
      const created = await api.createProject({
        name,
        parcel_code: parcelCode || undefined,
        description: description || undefined,
      });
      setName("");
      setParcelCode("");
      setDescription("");
      setShowForm(false);
      navigate(`/projects/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">پروژه‌ها</h2>
          <p className="text-sm text-slate-500">
            فهرست تمام پروژه‌های بررسی ملک.
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "انصراف" : "پروژه جدید"}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <div>
            <label className="label">نام پروژه</label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="مثال: بررسی پلاک ۱۲۳"
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">کد پلاک (اختیاری)</label>
              <input
                className="input"
                value={parcelCode}
                onChange={(e) => setParcelCode(e.target.value)}
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
            {submitting ? "در حال ایجاد..." : "ایجاد پروژه"}
          </button>
        </form>
      )}

      <div className="card overflow-hidden p-0">
        {loading ? (
          <p className="p-6 text-sm text-slate-500">در حال بارگذاری...</p>
        ) : projects.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">هنوز پروژه‌ای ثبت نشده است.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-head">شناسه</th>
                <th className="table-head">نام</th>
                <th className="table-head">کد پلاک</th>
                <th className="table-head">تاریخ ایجاد</th>
                <th className="table-head"></th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="table-cell">{p.id}</td>
                  <td className="table-cell font-medium">{p.name}</td>
                  <td className="table-cell">{p.parcel_code || "—"}</td>
                  <td className="table-cell">
                    {new Date(p.created_at).toLocaleDateString("fa-IR")}
                  </td>
                  <td className="table-cell">
                    <Link
                      to={`/projects/${p.id}`}
                      className="text-sm text-brand-600 hover:underline"
                    >
                      مشاهده
                    </Link>
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