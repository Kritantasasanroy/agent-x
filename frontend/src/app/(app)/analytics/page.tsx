"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { Analytics } from "@/lib/types";
import { PageHeader, StatCard, Empty } from "@/components/ui";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#14b8a6"];

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Analytics | null>(null);
  const [recs, setRecs] = useState<string[]>([]);

  useEffect(() => {
    api.get<Analytics>("/api/analytics").then(setStats).catch(() => {});
    api
      .get<{ recommendations?: string[] }>("/api/analytics/recommendations")
      .then((r) => setRecs(r.recommendations || []))
      .catch(() => {});
  }, []);

  const statusData = stats
    ? Object.entries(stats.by_status).map(([name, value]) => ({ name, value }))
    : [];
  const sourceData = stats
    ? Object.entries(stats.by_source).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div>
      <PageHeader
        title="Analytics"
        action={
          <a className="btn-ghost" href={`${api.base}/api/analytics/export?fmt=csv`} target="_blank" rel="noreferrer">
            Export CSV
          </a>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total" value={stats?.total_applications ?? "—"} />
        <StatCard label="Interview rate" value={stats ? `${stats.interview_rate}%` : "—"} />
        <StatCard label="Response rate" value={stats ? `${stats.response_rate}%` : "—"} />
        <StatCard label="Offer rate" value={stats ? `${stats.offer_rate}%` : "—"} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 font-semibold text-slate-700">Applications by status</h3>
          {statusData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2ff" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="value">
                  {statusData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Empty text="No data yet." />
          )}
        </div>

        <div className="card">
          <h3 className="mb-4 font-semibold text-slate-700">Applications by source</h3>
          {sourceData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={sourceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2ff" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Empty text="No data yet." />
          )}
        </div>
      </div>

      <h3 className="mb-3 mt-8 font-semibold text-slate-700">Learning recommendations</h3>
      {recs.length === 0 ? (
        <Empty text="The learning agent runs weekly and posts tips here." />
      ) : (
        <ul className="card space-y-2">
          {recs.map((r, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-600">
              <span>💡</span>
              {r}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
