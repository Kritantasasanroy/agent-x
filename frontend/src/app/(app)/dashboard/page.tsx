"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Analytics, Application } from "@/lib/types";
import { PageHeader, StatCard, StatusBadge, Empty } from "@/components/ui";

export default function DashboardPage() {
  const [stats, setStats] = useState<Analytics | null>(null);
  const [recent, setRecent] = useState<Application[]>([]);
  const [msg, setMsg] = useState("");

  async function load() {
    try {
      setStats(await api.get<Analytics>("/api/analytics"));
      setRecent(await api.get<Application[]>("/api/applications"));
    } catch {
      /* handled by api wrapper */
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function discover() {
    setMsg("Queuing discovery…");
    await api.post("/api/jobs/discover");
    setMsg("Discovery started — new jobs appear within a few minutes.");
  }

  return (
    <div>
      <PageHeader
        title="Dashboard"
        action={
          <button className="btn" onClick={discover}>
            🔍 Run discovery now
          </button>
        }
      />
      {msg && <p className="mb-4 text-sm text-brand-600">{msg}</p>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Applications today" value={stats?.applications_today ?? "—"} />
        <StatCard label="This week" value={stats?.applications_week ?? "—"} />
        <StatCard
          label="Interview rate"
          value={stats ? `${stats.interview_rate}%` : "—"}
        />
        <StatCard label="Offer rate" value={stats ? `${stats.offer_rate}%` : "—"} />
        <StatCard
          label="Response rate"
          value={stats ? `${stats.response_rate}%` : "—"}
          hint="recruiter outreach"
        />
        <StatCard label="Total applications" value={stats?.total_applications ?? "—"} />
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold text-slate-700">Recent applications</h2>
      {recent.length === 0 ? (
        <Empty text="No applications yet. Set your profile, then run discovery." />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50">
              <tr>
                <th className="th">Status</th>
                <th className="th">Created</th>
                <th className="th">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent.slice(0, 8).map((a) => (
                <tr key={a.id}>
                  <td className="td">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="td">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="td text-slate-500">
                    {a.needs_review_reason || a.confirmation || a.error || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
