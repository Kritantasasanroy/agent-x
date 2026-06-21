"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Application } from "@/lib/types";
import { PageHeader, StatusBadge, Empty } from "@/components/ui";

const STATUSES = ["pending", "needs_review", "applied", "interview", "offer", "rejected"];

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [filter, setFilter] = useState("");

  async function load() {
    const q = filter ? `?status=${filter}` : "";
    setApps(await api.get<Application[]>(`/api/applications${q}`));
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function setStatus(id: string, status: string) {
    await api.patch(`/api/applications/${id}/status?status=${status}`);
    load();
  }

  return (
    <div>
      <PageHeader title="Applications" />
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          className={`badge ${!filter ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-600"}`}
          onClick={() => setFilter("")}
        >
          all
        </button>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={`badge ${filter === s ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-600"}`}
            onClick={() => setFilter(s)}
          >
            {s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {apps.length === 0 ? (
        <Empty text="No applications match this filter." />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50">
              <tr>
                <th className="th">Status</th>
                <th className="th">Created</th>
                <th className="th">Submitted</th>
                <th className="th">Note</th>
                <th className="th">Move to</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {apps.map((a) => (
                <tr key={a.id}>
                  <td className="td">
                    <StatusBadge status={a.status} />
                  </td>
                  <td className="td">{new Date(a.created_at).toLocaleDateString()}</td>
                  <td className="td">
                    {a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="td text-slate-500">
                    {a.needs_review_reason || a.confirmation || a.error || "—"}
                  </td>
                  <td className="td">
                    <select
                      className="input w-36"
                      value={a.status}
                      onChange={(e) => setStatus(a.id, e.target.value)}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
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
