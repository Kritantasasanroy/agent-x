"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CoverLetter } from "@/lib/types";
import { PageHeader, Empty } from "@/components/ui";

export default function CoverLettersPage() {
  const [letters, setLetters] = useState<CoverLetter[]>([]);

  useEffect(() => {
    api.get<CoverLetter[]>("/api/cover-letters").then(setLetters).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader title="Cover Letters" />
      {letters.length === 0 ? (
        <Empty text="No cover letters yet. They are generated when you apply to a job." />
      ) : (
        <div className="space-y-4">
          {letters.map((c) => (
            <div key={c.id} className="card">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  {new Date(c.created_at).toLocaleString()}
                </span>
                <div className="flex gap-2">
                  <a
                    className="btn-ghost"
                    href={`${api.base}/api/cover-letters/${c.id}/download?fmt=pdf`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PDF
                  </a>
                  <a
                    className="btn-ghost"
                    href={`${api.base}/api/cover-letters/${c.id}/download?fmt=docx`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    DOCX
                  </a>
                </div>
              </div>
              <p className="whitespace-pre-wrap text-sm text-slate-600">
                {c.content.slice(0, 600)}
                {c.content.length > 600 ? "…" : ""}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
