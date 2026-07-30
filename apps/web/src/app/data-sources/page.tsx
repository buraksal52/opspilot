"use client";

import { useCallback, useEffect, useState, type ChangeEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL } from "@/lib/config";
import { authHeaders, getWorkspaceId, setWorkspaceId } from "@/lib/auth";

type DataSource = {
  id: string;
  workspace_id: string;
  name: string;
  source_type: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
};

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  READY: "default",
  UPLOADED: "secondary",
  PROCESSING: "secondary",
  FAILED: "destructive",
  DELETED: "outline",
};

export default function DataSourcesPage() {
  // Lazy initializer (not an effect+setState) so reading localStorage on
  // mount doesn't trip react-hooks/set-state-in-effect.
  const [workspaceId, setWorkspaceIdState] = useState<string>(() => getWorkspaceId() ?? "");
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDataSources = useCallback(async (currentWorkspaceId: string) => {
    if (!currentWorkspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workspaces/${currentWorkspaceId}/data-sources`, {
        headers: authHeaders(),
      });
      if (!response.ok) throw new Error(`Failed to load data sources (${response.status})`);
      setDataSources(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // react-hooks/set-state-in-effect flags any effect that (transitively)
    // calls a setState setter, including standard fetch-on-dependency-change
    // data loading — there is no effect-based way to trigger this refetch
    // that the rule accepts short of a full data-fetching library, which is
    // disproportionate for this internal page.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (workspaceId) void loadDataSources(workspaceId);
  }, [workspaceId, loadDataSources]);

  function handleWorkspaceIdChange(value: string) {
    setWorkspaceIdState(value);
    setWorkspaceId(value);
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !workspaceId) return;

    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}/data-sources/upload`, {
        method: "POST",
        headers: authHeaders(),
        body: formData,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error?.message ?? `Upload failed (${response.status})`);
      }
      await loadDataSources(workspaceId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/data-sources/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!response.ok && response.status !== 204) throw new Error(`Failed to delete (${response.status})`);
      await loadDataSources(workspaceId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Data Sources</h1>
        <p className="text-muted-foreground">Upload CSV, PDF, Markdown, or plain-text files for this workspace.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Workspace</CardTitle>
          <CardDescription>
            Paste a workspace id you already have access to (workspace creation isn&apos;t exposed via API/UI yet).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <input
            type="text"
            placeholder="Workspace ID"
            value={workspaceId}
            onChange={(event) => handleWorkspaceIdChange(event.target.value)}
            className="h-9 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upload</CardTitle>
          <CardDescription>Supported: .csv, .pdf, .md, .txt</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <input
            type="file"
            accept=".csv,.pdf,.md,.markdown,.txt"
            disabled={!workspaceId || uploading}
            onChange={handleUpload}
            className="text-sm"
          />
          {uploading && <span className="text-sm text-muted-foreground">Uploading...</span>}
        </CardContent>
      </Card>

      {error && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Uploaded Sources</CardTitle>
          <CardDescription>{loading ? "Loading..." : `${dataSources.length} source(s)`}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {dataSources.length === 0 && !loading && (
            <p className="text-sm text-muted-foreground">No data sources uploaded yet.</p>
          )}
          {dataSources.map((dataSource) => (
            <div
              key={dataSource.id}
              className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2"
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-medium">{dataSource.name}</span>
                <span className="text-xs text-muted-foreground">
                  {dataSource.source_type} · {dataSource.original_filename} ·{" "}
                  {(dataSource.file_size_bytes / 1024).toFixed(1)} KB
                </span>
                {dataSource.error_message && (
                  <span className="text-xs text-destructive">{dataSource.error_message}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={STATUS_VARIANT[dataSource.status] ?? "secondary"}>{dataSource.status}</Badge>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(dataSource.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
