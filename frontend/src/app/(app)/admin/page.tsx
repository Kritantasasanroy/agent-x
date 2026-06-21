"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader, Empty } from "@/components/ui";

interface Rule {
  id: string;
  company: string;
  kind: string;
}
interface Audit {
  id: string;
  actor: string;
  action: string;
  target: string;
  created_at: string;
}

export default function AdminPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [company, setCompany] = useState("");
  const [kind, setKind] = useState("blacklist");
  const [threshold, setThreshold] = useState(75);
  const [maxApps, setMaxApps] = useState(50);
  const [err, setErr] = useState("");

  async function load() {
    try {
      setRules(await api.get<Rule[]>("/api/admin/company-rules"));
      setAudit(await api.get<Audit[]>("/api/admin/audit-logs"));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Admin access required");
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function pause(paused: boolean) {
    await api.post(paused ? "/api/admin/pause" : "/api/admin/resume");
    alert(paused ? "All automation paused." : "Automation resumed.");
  }
  async function addRule() {
    await api.post("/api/admin/company-rules", { company, kind });
    setCompany("");
    load();
  }
  async function delRule(c: string) {
    await api.del(`/api/admin/company-rules/${encodeURIComponent(c)}`);
    load();
  }
  async function saveConfig() {
    await api.post("/api/admin/config", {
      match_threshold: threshold,
      max_applications_per_day: maxApps,
    });
    alert("Config saved.");
  }

  if (err) return <Empty text={err} />;

  return (
    <div>
      <PageHeader
        title="Admin"
        action={
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={() => pause(true)}>
              ⏸ Pause all
            </button>
            <button className="btn" onClick={() => pause(false)}>
              ▶ Resume
            </button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold text-slate-700">Limits</h3>
          <label className="label">Match threshold (0–100)</label>
          <input
            className="input mb-3"
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
          <label className="label">Max applications / day</label>
          <input
            className="input mb-3"
            type="number"
            value={maxApps}
            onChange={(e) => setMaxApps(Number(e.target.value))}
          />
          <button className="btn" onClick={saveConfig}>
            Save config
          </button>
        </div>

        <div className="card">
          <h3 className="mb-3 font-semibold text-slate-700">Company rules</h3>
          <div className="mb-3 flex gap-2">
            <input
              className="input"
              placeholder="Company name"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
            />
            <select className="input w-36" value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="blacklist">blacklist</option>
              <option value="whitelist">whitelist</option>
            </select>
            <button className="btn" onClick={addRule}>
              Add
            </button>
          </div>
          {rules.length === 0 ? (
            <p className="text-sm text-slate-400">No rules.</p>
          ) : (
            <ul className="space-y-1">
              {rules.map((r) => (
                <li key={r.id} className="flex items-center justify-between text-sm">
                  <span>
                    <span className="badge bg-slate-100 text-slate-600">{r.kind}</span>{" "}
                    {r.company}
                  </span>
                  <button className="text-rose-500" onClick={() => delRule(r.company)}>
                    remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <h3 className="mb-3 mt-8 font-semibold text-slate-700">Audit log</h3>
      <div className="card max-h-96 overflow-y-auto p-0">
        <table className="min-w-full divide-y divide-slate-100">
          <thead className="sticky top-0 bg-slate-50">
            <tr>
              <th className="th">Time</th>
              <th className="th">Actor</th>
              <th className="th">Action</th>
              <th className="th">Target</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {audit.map((a) => (
              <tr key={a.id}>
                <td className="td text-slate-400">{new Date(a.created_at).toLocaleString()}</td>
                <td className="td">{a.actor}</td>
                <td className="td font-medium">{a.action}</td>
                <td className="td text-slate-500">{a.target || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
