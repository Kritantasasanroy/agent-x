"use client";

import { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-800">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  applied: "bg-blue-100 text-blue-700",
  pending: "bg-amber-100 text-amber-700",
  needs_review: "bg-orange-100 text-orange-700",
  interview: "bg-purple-100 text-purple-700",
  offer: "bg-green-100 text-green-700",
  rejected: "bg-rose-100 text-rose-700",
  failed: "bg-rose-100 text-rose-700",
  sent: "bg-blue-100 text-blue-700",
  queued: "bg-slate-100 text-slate-600",
  replied: "bg-green-100 text-green-700",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${STATUS_COLORS[status] || "bg-slate-100 text-slate-600"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75 ? "bg-green-100 text-green-700" : score >= 50 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600";
  return <span className={`badge ${color}`}>{score.toFixed(0)}</span>;
}

export function PageHeader({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex items-center justify-between">
      <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
      {action}
    </div>
  );
}

export function Empty({ text }: { text: string }) {
  return <div className="card text-center text-sm text-slate-400">{text}</div>;
}
