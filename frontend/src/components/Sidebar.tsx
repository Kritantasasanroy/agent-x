"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/jobs", label: "Jobs", icon: "💼" },
  { href: "/applications", label: "Applications", icon: "📨" },
  { href: "/resumes", label: "Resumes", icon: "📄" },
  { href: "/cover-letters", label: "Cover Letters", icon: "✉️" },
  { href: "/recruiters", label: "Recruiters", icon: "🧑‍💼" },
  { href: "/messages", label: "Messages", icon: "💬" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/profile", label: "Profile", icon: "👤" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
  { href: "/admin", label: "Admin", icon: "🛡️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="text-2xl">🦣</span>
        <span className="text-lg font-bold text-slate-800">JobHunter AI</span>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => {
          clearToken();
          router.push("/login");
        }}
        className="m-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-500 hover:bg-slate-100"
      >
        🚪 Log out
      </button>
    </aside>
  );
}
