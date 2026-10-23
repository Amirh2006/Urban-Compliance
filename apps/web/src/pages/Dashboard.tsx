import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Project, Rule } from "../api/client";

export function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listProjects(), api.listRules()])
      .then(([p, r]) => {
        setProjects(p);
        setRules(r);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">داشبورد</h2>
        <p className="text-sm text-slate-500">
          خلاصه‌ای از وضعیت سامانه و اقدامات سریع.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="پروژه‌ها" value={projects.length} />
        <StatCard label="قواعد ثبت‌شده" value={rules.length} />
        <StatCard
          label="قواعد تأییدشده"
          value={rules.filter((r) => r.is_verified).length}
        />
        <StatCard
          label="قواعد فعال"
          value={rules.filter((r) => r.is_active).length}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-lg font-semibold text-slate-800">اقدامات سریع</h3>
          <div className="flex flex-col gap-2">
            <Link to="/projects" className="btn-primary">
              مشاهده و ایجاد پروژه
            </Link>
            <Link to="/analysis/new" className="btn-secondary">
              اجرای تحلیل جدید
            </Link>
            <Link to="/knowledge" className="btn-secondary">
              جست‌وجو در آرشیو دانش
            </Link>
          </div>
        </div>

        <div className="card">
          <h3 className="mb-3 text-lg font-semibold text-slate-800">
            آخرین پروژه‌ها
          </h3>
          {loading ? (
            <p className="text-sm text-slate-500">در حال بارگذاری...</p>
          ) : projects.length === 0 ? (
            <p className="text-sm text-slate-500">هنوز پروژه‌ای ثبت نشده است.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {projects.slice(0, 5).map((p) => (
                <li key={p.id} className="py-2">
                  <Link
                    to={`/projects/${p.id}`}
                    className="flex items-center justify-between text-sm hover:text-brand-700"
                  >
                    <span className="font-medium text-slate-800">{p.name}</span>
                    <span className="text-xs text-slate-400">#{p.id}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-800">{value}</p>
    </div>
  );
}