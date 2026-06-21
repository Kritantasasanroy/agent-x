"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Profile } from "@/lib/types";
import { PageHeader } from "@/components/ui";

const EMPTY: Profile = {
  master_resume: "",
  phone: "",
  location: "",
  linkedin_url: "",
  github_url: "",
  portfolio_url: "",
  skills: [],
  preferred_roles: [],
  preferred_locations: [],
  min_salary: 0,
  remote_only: false,
  years_experience: 0,
};

export default function ProfilePage() {
  const [p, setP] = useState<Profile>(EMPTY);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get<Profile>("/api/profile").then((d) => setP({ ...EMPTY, ...d })).catch(() => {});
  }, []);

  function csv(v: string[]) {
    return v.join(", ");
  }
  function toArr(s: string) {
    return s.split(",").map((x) => x.trim()).filter(Boolean);
  }

  async function save() {
    await api.put("/api/profile", p);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      <PageHeader
        title="Profile"
        action={
          <button className="btn" onClick={save}>
            {saved ? "Saved ✓" : "Save profile"}
          </button>
        }
      />
      <p className="mb-4 text-sm text-slate-500">
        This master profile drives every agent. The more complete it is, the better the
        matching, resumes, and outreach.
      </p>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card lg:col-span-2">
          <label className="label">Master resume (plain text)</label>
          <textarea
            className="input h-48"
            value={p.master_resume}
            onChange={(e) => setP({ ...p, master_resume: e.target.value })}
          />
        </div>

        {(
          [
            ["phone", "Phone"],
            ["location", "Location"],
            ["linkedin_url", "LinkedIn URL"],
            ["github_url", "GitHub URL"],
            ["portfolio_url", "Portfolio URL"],
          ] as const
        ).map(([key, label]) => (
          <div className="card" key={key}>
            <label className="label">{label}</label>
            <input
              className="input"
              value={(p as unknown as Record<string, string>)[key] ?? ""}
              onChange={(e) => setP({ ...p, [key]: e.target.value })}
            />
          </div>
        ))}

        <div className="card">
          <label className="label">Years of experience</label>
          <input
            className="input"
            type="number"
            value={p.years_experience}
            onChange={(e) => setP({ ...p, years_experience: Number(e.target.value) })}
          />
        </div>

        <div className="card lg:col-span-2">
          <label className="label">Skills (comma-separated)</label>
          <input
            className="input"
            value={csv(p.skills)}
            onChange={(e) => setP({ ...p, skills: toArr(e.target.value) })}
          />
        </div>
        <div className="card">
          <label className="label">Preferred roles (comma-separated)</label>
          <input
            className="input"
            value={csv(p.preferred_roles)}
            onChange={(e) => setP({ ...p, preferred_roles: toArr(e.target.value) })}
          />
        </div>
        <div className="card">
          <label className="label">Preferred locations (comma-separated)</label>
          <input
            className="input"
            value={csv(p.preferred_locations)}
            onChange={(e) => setP({ ...p, preferred_locations: toArr(e.target.value) })}
          />
        </div>
        <div className="card">
          <label className="label">Minimum salary</label>
          <input
            className="input"
            type="number"
            value={p.min_salary}
            onChange={(e) => setP({ ...p, min_salary: Number(e.target.value) })}
          />
        </div>
        <div className="card flex items-center gap-3">
          <input
            id="remote"
            type="checkbox"
            checked={p.remote_only}
            onChange={(e) => setP({ ...p, remote_only: e.target.checked })}
          />
          <label htmlFor="remote" className="text-sm font-medium text-slate-600">
            Remote only
          </label>
        </div>
      </div>
    </div>
  );
}
