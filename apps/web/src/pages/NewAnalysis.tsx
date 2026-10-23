import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Project } from "../api/client";

export function NewAnalysis() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | "">("");
  const [geometryText, setGeometryText] = useState(
    JSON.stringify(
      {
        type: "Polygon",
        coordinates: [
          [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10],
            [0, 0],
          ],
        ],
        crs: "EPSG:3857",
      },
      null,
      2
    )
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.listProjects().then(setProjects).catch((e) => setError(e.message));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!projectId) {
      setError("یک پروژه انتخاب کنید.");
      return;
    }
    let geometry;
    try {
      geometry = JSON.parse(geometryText);
    } catch {
      setError("هندسه GeoJSON معتبر نیست.");
      return;
    }
    setSubmitting(true);
    try {
      const analysis = await api.createAnalysis({
        project_id: Number(projectId),
        geometry,
      });
      navigate(`/analysis/${analysis.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">تحلیل جدید</h2>
        <p className="text-sm text-slate-500">
          پروژه را انتخاب و هندسه GeoJSON قطعه را وارد کنید.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="label">پروژه</label>
          <select
            className="input"
            value={projectId}
            onChange={(e) =>
              setProjectId(e.target.value ? Number(e.target.value) : "")
            }
            required
          >
            <option value="">— انتخاب کنید —</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} (#{p.id})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">هندسه (GeoJSON)</label>
          <textarea
            className="input h-64 font-mono text-xs"
            dir="ltr"
            value={geometryText}
            onChange={(e) => setGeometryText(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-500">
            اگر CRS مشخص نشود، مساحت محاسبه نمی‌شود.
          </p>
        </div>

        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? "در حال اجرا..." : "اجرای تحلیل"}
        </button>
      </form>
    </div>
  );
}