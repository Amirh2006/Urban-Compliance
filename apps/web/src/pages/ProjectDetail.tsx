import { ChangeEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Analysis, Project, ProjectFile } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

const SAMPLE_GEOMETRY = {
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
};

export function ProjectDetail() {
  const { id } = useParams();
  const projectId = Number(id);
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<Analysis | null>(null);

  async function load() {
    try {
      const p = await api.getProject(projectId);
      setProject(p);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    load();
  }, [projectId]);

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const record = await api.uploadFile(projectId, file);
      setFiles((prev) => [...prev, record]);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function processFile(fileId: number) {
    try {
      const updated = await api.processFile(fileId);
      setFiles((prev) => prev.map((f) => (f.id === fileId ? updated : f)));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function runAnalysisWithGeometry() {
    setAnalyzing(true);
    try {
      const a = await api.createAnalysis({
        project_id: projectId,
        geometry: SAMPLE_GEOMETRY,
      });
      setLastAnalysis(a);
      setAnalyses((prev) => [...prev, a]);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setAnalyzing(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
    );
  }

  if (!project) {
    return <p className="text-sm text-slate-500">در حال بارگذاری...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/projects" className="text-sm text-brand-600 hover:underline">
          ← بازگشت به پروژه‌ها
        </Link>
        <h2 className="mt-2 text-2xl font-bold text-slate-800">{project.name}</h2>
        <p className="text-sm text-slate-500">
          شناسه: {project.id} • کد پلاک: {project.parcel_code || "—"}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-lg font-semibold">فایل‌ها</h3>
          <p className="mb-3 text-xs text-slate-500">
            فرمت‌های پشتیبانی‌شده: GeoJSON، CSV
          </p>
          <input
            type="file"
            accept=".geojson,.json,.csv"
            onChange={handleUpload}
            disabled={uploading}
            className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-brand-600 file:px-3 file:py-2 file:text-white hover:file:bg-brand-700"
          />
          {uploading && (
            <p className="mt-2 text-xs text-slate-500">در حال آپلود...</p>
          )}
          {files.length > 0 && (
            <ul className="mt-4 divide-y divide-slate-100">
              {files.map((f) => (
                <li key={f.id} className="py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-800">{f.filename}</span>
                    <StatusBadge status={f.status} />
                  </div>
                  {f.error && (
                    <p className="mt-1 text-xs text-red-600">{f.error}</p>
                  )}
                  {f.detected_crs && (
                    <p className="mt-1 text-xs text-slate-500">
                      CRS: {f.detected_crs}
                    </p>
                  )}
                  {f.status === "uploaded" && (
                    <button
                      className="mt-1 text-xs text-brand-600 hover:underline"
                      onClick={() => processFile(f.id)}
                    >
                      پردازش فایل
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h3 className="mb-3 text-lg font-semibold">اجرای تحلیل</h3>
          <p className="mb-3 text-xs text-slate-500">
            یک هندسه نمونه (مربع ۱۰×۱۰ متر) اعتبارسنجی و با قواعد فعال بررسی
            می‌شود.
          </p>
          <button
            className="btn-primary"
            onClick={runAnalysisWithGeometry}
            disabled={analyzing}
          >
            {analyzing ? "در حال اجرا..." : "اجرای تحلیل نمونه"}
          </button>
          {lastAnalysis && (
            <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
              <p className="font-medium">
                وضعیت: <StatusBadge status={lastAnalysis.status} />
              </p>
              <Link
                to={`/analysis/${lastAnalysis.id}`}
                className="mt-2 inline-block text-brand-600 hover:underline"
              >
                مشاهده گزارش ←
              </Link>
            </div>
          )}
        </div>
      </div>

      {analyses.length > 0 && (
        <div className="card">
          <h3 className="mb-3 text-lg font-semibold">تحلیل‌های این پروژه</h3>
          <ul className="divide-y divide-slate-100">
            {analyses.map((a) => (
              <li
                key={a.id}
                className="flex items-center justify-between py-2 text-sm"
              >
                <span>
                  #{a.id} — <StatusBadge status={a.status} />
                </span>
                <Link
                  to={`/analysis/${a.id}`}
                  className="text-brand-600 hover:underline"
                >
                  گزارش
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}