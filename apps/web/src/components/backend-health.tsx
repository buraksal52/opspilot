"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { API_BASE_URL } from "@/lib/config";

type HealthState = "checking" | "ok" | "error";

export function BackendHealth() {
  const [state, setState] = useState<HealthState>("checking");

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE_URL}/api/v1/health`)
      .then((response) => {
        if (!response.ok) throw new Error(`Unexpected status ${response.status}`);
        return response.json();
      })
      .then((data: { status?: string }) => {
        if (!cancelled) setState(data.status === "ok" ? "ok" : "error");
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const label = state === "checking" ? "Checking..." : state === "ok" ? "Connected" : "Unreachable";
  const variant = state === "ok" ? "default" : state === "error" ? "destructive" : "secondary";

  return (
    <div className="flex items-center gap-2">
      <Badge variant={variant}>{label}</Badge>
      <span className="text-sm text-muted-foreground">
        {API_BASE_URL}/api/v1/health
      </span>
    </div>
  );
}
