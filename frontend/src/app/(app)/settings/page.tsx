"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui";

interface Me {
  email: string;
  full_name: string;
  role: string;
  automation_paused: boolean;
}

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    api.get<Me>("/api/auth/me").then(setMe).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader title="Settings" />
      <div className="card mb-4 max-w-lg">
        <h3 className="mb-3 font-semibold text-slate-700">Account</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-500">Email</dt>
            <dd className="font-medium">{me?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Role</dt>
            <dd className="font-medium">{me?.role}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Automation</dt>
            <dd className="font-medium">{me?.automation_paused ? "Paused" : "Active"}</dd>
          </div>
        </dl>
      </div>

      <div className="card max-w-lg">
        <h3 className="mb-2 font-semibold text-slate-700">About</h3>
        <p className="text-sm text-slate-500">
          API base: <code>{api.base}</code>
        </p>
        <p className="mt-2 text-sm text-slate-500">
          LLM keys and SMTP credentials are configured server-side via environment variables
          or the admin secrets endpoint — never stored in the browser.
        </p>
      </div>
    </div>
  );
}
