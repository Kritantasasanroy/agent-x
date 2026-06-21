"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Message } from "@/lib/types";
import { PageHeader, StatusBadge, Empty } from "@/components/ui";

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    api.get<Message[]>("/api/messages").then(setMessages).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader title="Messages" />
      {messages.length === 0 ? (
        <Empty text="No outreach messages yet." />
      ) : (
        <div className="space-y-3">
          {messages.map((m) => (
            <div key={m.id} className="card">
              <div className="flex items-center justify-between">
                <p className="font-medium text-slate-700">{m.subject || "(no subject)"}</p>
                <div className="flex items-center gap-2">
                  <span className="badge bg-slate-100 text-slate-600">step {m.sequence_step}</span>
                  <StatusBadge status={m.status} />
                </div>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{m.body}</p>
              <p className="mt-2 text-xs text-slate-400">
                {m.channel} · {new Date(m.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
