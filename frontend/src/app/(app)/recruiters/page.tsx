"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Recruiter } from "@/lib/types";
import { PageHeader, Empty } from "@/components/ui";

const BLANK = { name: "", title: "", company: "", email: "", linkedin_url: "", source: "manual" };

export default function RecruitersPage() {
  const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
  const [form, setForm] = useState({ ...BLANK });

  async function load() {
    setRecruiters(await api.get<Recruiter[]>("/api/recruiters"));
  }
  useEffect(() => {
    load().catch(() => {});
  }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/api/recruiters", { id: "", ...form });
    setForm({ ...BLANK });
    load();
  }

  async function outreach(id: string) {
    await api.post(`/api/recruiters/${id}/outreach`);
    alert("Outreach sequence started (initial + 7d + 14d follow-ups).");
  }

  return (
    <div>
      <PageHeader title="Recruiters" />
      <form onSubmit={add} className="card mb-6 grid grid-cols-2 gap-3 md:grid-cols-3">
        {(["name", "title", "company", "email", "linkedin_url"] as const).map((f) => (
          <div key={f}>
            <label className="label capitalize">{f.replace("_", " ")}</label>
            <input
              className="input"
              value={(form as Record<string, string>)[f]}
              onChange={(e) => setForm({ ...form, [f]: e.target.value })}
            />
          </div>
        ))}
        <div className="flex items-end">
          <button className="btn w-full">Add recruiter</button>
        </div>
      </form>

      {recruiters.length === 0 ? (
        <Empty text="No recruiters yet. Add one above to start outreach." />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50">
              <tr>
                <th className="th">Name</th>
                <th className="th">Company</th>
                <th className="th">Email</th>
                <th className="th"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recruiters.map((r) => (
                <tr key={r.id}>
                  <td className="td font-medium">
                    {r.name} <span className="text-slate-400">{r.title}</span>
                  </td>
                  <td className="td">{r.company}</td>
                  <td className="td text-slate-500">{r.email || "—"}</td>
                  <td className="td">
                    <button className="btn-ghost" onClick={() => outreach(r.id)}>
                      Start outreach
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
