"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Job } from "@/lib/types";
import { PageHeader, ScoreBadge, Empty } from "@/components/ui";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [minScore, setMinScore] = useState(0);
  const [company, setCompany] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    const params = new URLSearchParams();
    if (minScore) params.set("min_score", String(minScore));
    if (company) params.set("company", company);
    setJobs(await api.get<Job[]>(`/api/jobs?${params.toString()}`));
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function apply(jobId: string) {
    setBusy(jobId);
    try {
      await api.post("/api/applications", { job_id: jobId, auto_submit: true });
      alert("Application queued. Track it on the Applications page.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageHeader title="Jobs" />
      <div className="card mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="label">Min match score</label>
          <input
            className="input w-32"
            type="number"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
          />
        </div>
        <div>
          <label className="label">Company</label>
          <input className="input w-48" value={company} onChange={(e) => setCompany(e.target.value)} />
        </div>
        <button className="btn" onClick={load}>
          Filter
        </button>
      </div>

      {jobs.length === 0 ? (
        <Empty text="No jobs found. Run discovery from the Dashboard." />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50">
              <tr>
                <th className="th">Score</th>
                <th className="th">Title</th>
                <th className="th">Company</th>
                <th className="th">Location</th>
                <th className="th">Source</th>
                <th className="th"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {jobs.map((j) => (
                <tr key={j.id} className="hover:bg-slate-50">
                  <td className="td">
                    <ScoreBadge score={j.match_score} />
                  </td>
                  <td className="td font-medium">{j.title}</td>
                  <td className="td">{j.company}</td>
                  <td className="td">{j.remote ? "Remote" : j.location || "—"}</td>
                  <td className="td text-slate-500">{j.source}</td>
                  <td className="td">
                    <button
                      className="btn-ghost"
                      disabled={busy === j.id}
                      onClick={() => apply(j.id)}
                    >
                      {busy === j.id ? "…" : "Apply"}
                    </button>
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
