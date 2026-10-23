import { FormEvent, useEffect, useState } from "react";
import { api, KnowledgeSearchHit, KnowledgeSource } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function Knowledge() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<KnowledgeSearchHit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);

  async function refresh() {
    try {
      setSources(await api.listSources());
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createSource(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setCreating(true);
    try {
      await api.createSource({ title: title.trim() });
      setTitle("");
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  }

  async function uploadDoc(sourceId: number, file: File) {
    try {
      await api.uploadDocument(sourceId, file);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function search(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    try {
      setHits(await api.searchKnowledge(query.trim()));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">آرشیو دانش</h2>
        <p className="text-sm text-slate-500">
          اسناد PDF ضوابط را بارگذاری و در متن آن‌ها جست‌وجو کنید.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      <form onSubmit={createSource} className="card flex gap-2">
        <input
          className="input"
          placeholder="عنوان سند جدید (مثلاً: ضوابط منطقه ۶)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <button className="btn-primary" disabled={creating}>
          {creating ? "..." : "افزودن"}
        </button>
      </form>

      <div className="card">
        <h3 className="mb-3 text-lg font-semibold">اسناد ثبت‌شده</h3>
        {sources.length === 0 ? (
          <p className="text-sm text-slate-500">هنوز سندی ثبت نشده است.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {sources.map((s) => (
              <li key={s.id} className="py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-800">{s.title}</p>
                    <p className="text-xs text-slate-500">
                      شناسه: {s.id} • نسخه: {s.version} • صفحات: {s.page_count}
                    </p>
                  </div>
                  <StatusBadge status={s.extraction_status} />
                </div>
                {s.extraction_error && (
                  <p className="mt-1 text-xs text-red-600">{s.extraction_error}</p>
                )}
                <div className="mt-2">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) uploadDoc(s.id, file);
                      e.target.value = "";
                    }}
                    className="text-xs file:mr-2 file:rounded file:border-0 file:bg-slate-200 file:px-2 file:py-1"
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card">
        <h3 className="mb-3 text-lg font-semibold">جست‌وجو</h3>
        <form onSubmit={search} className="flex gap-2">
          <input
            className="input"
            placeholder="عبارت مورد نظر..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn-primary">جست‌وجو</button>
        </form>
        {hits.length > 0 && (
          <ul className="mt-4 space-y-2">
            {hits.map((h) => (
              <li
                key={h.chunk_id}
                className="rounded-lg border border-slate-200 p-3 text-sm"
              >
                <p className="text-xs text-slate-500">
                  {h.source_title} • صفحه {h.page_number}
                </p>
                <p className="mt-1 text-slate-700" dir="rtl">
                  {h.snippet}
                </p>
              </li>
            ))}
          </ul>
        )}
        {hits.length === 0 && query && (
          <p className="mt-3 text-sm text-slate-500">نتیجه‌ای یافت نشد.</p>
        )}
      </div>
    </div>
  );
}