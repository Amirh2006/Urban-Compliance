import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "داشبورد" },
  { to: "/projects", label: "پروژه‌ها" },
  { to: "/analysis/new", label: "تحلیل جدید" },
  { to: "/rules", label: "قواعد" },
  { to: "/knowledge", label: "آرشیو دانش" },
];

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50" dir="rtl">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 font-bold text-white">
              U
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800">
                Urban Compliance AI
              </h1>
              <p className="text-xs text-slate-500">
                بررسی اولیه انطباق ملک با ضوابط شهرداری
              </p>
            </div>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>

      <footer className="mx-auto max-w-6xl px-6 pb-6 pt-2 text-center text-xs text-slate-400">
        این ابزار کمک‌تصمیم فنی است و تأییدیه رسمی شهرداری صادر نمی‌کند.
      </footer>
    </div>
  );
}