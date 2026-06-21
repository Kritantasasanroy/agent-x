"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Resume } from "@/lib/types";
import { PageHeader, Empty } from "@/components/ui";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);

  useEffect(() => {
    api.get<Resume[]>("/api/resumes").then(setResumes).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader title="Resumes" />
      {resumes.length === 0 ? (
        <Empty text="No tailored resumes yet. They are generated when you apply to a job." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {resumes.map((r) => (
            <div key={r.id} className="card">
              <div className="flex items-center justify-between">
                <span className="badge bg-brand-100 text-brand-700">
                  Variant {r.variant} · v{r.version}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-slate-500">
                <div>
                  <p className="text-lg font-bold text-slate-700">{r.sends}</p>sends
                </div>
                <div>
                  <p className="text-lg font-bold text-slate-700">{r.responses}</p>responses
                </div>
                <div>
                  <p className="text-lg font-bold text-slate-700">{r.interviews}</p>interviews
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <a
                  className="btn-ghost flex-1"
                  href={`${api.base}/api/resumes/${r.id}/download?fmt=pdf`}
                  target="_blank"
                  rel="noreferrer"
                >
                  PDF
                </a>
                <a
                  className="btn-ghost flex-1"
                  href={`${api.base}/api/resumes/${r.id}/download?fmt=docx`}
                  target="_blank"
                  rel="noreferrer"
                >
                  DOCX
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
