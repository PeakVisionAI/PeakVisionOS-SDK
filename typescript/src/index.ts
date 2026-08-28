export interface Agent {
  name: string;
  [key: string]: unknown;
}

export interface Run {
  run_id: string;
  agent: string;
  status?: string;
  [key: string]: unknown;
}

export class GatewayError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "GatewayError";
    this.status = status;
  }
}

export interface AgentOSOptions {
  endpoint?: string;
  token?: string;
  timeoutMs?: number;
  fetch?: typeof globalThis.fetch;
}

function environment(name: string): string | undefined {
  // Keep the package usable in browsers and Node without requiring @types/node.
  const runtime = globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  };
  return runtime.process?.env?.[name];
}

/** Remote AgentOS control-plane client. Primitive calls remain local-only. */
export class AgentOS {
  private readonly endpoint: string;
  private readonly token: string;
  private readonly timeoutMs: number;
  private readonly fetcher: typeof globalThis.fetch;

  constructor(options: AgentOSOptions = {}) {
    const endpoint = options.endpoint ?? environment("AGENTOS_ENDPOINT");
    if (!endpoint || !/^https?:\/\//.test(endpoint)) {
      throw new TypeError("endpoint must use http:// or https://");
    }
    this.endpoint = endpoint.replace(/\/$/, "");
    this.token = options.token ?? environment("AGENTOS_TOKEN") ?? "";
    this.timeoutMs = options.timeoutMs ?? 15000;
    this.fetcher = options.fetch ?? globalThis.fetch;
    if (!this.fetcher) throw new TypeError("fetch is required (use Node 18+ or pass options.fetch)");
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    if (init.body) headers.set("Content-Type", "application/json");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.fetcher(`${this.endpoint}/${path.replace(/^\//, "")}`, { ...init, headers, signal: controller.signal });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new GatewayError(`Gateway HTTP ${response.status}: ${body.error ?? "request failed"}`, response.status);
      return body as T;
    } catch (error) {
      if (error instanceof GatewayError) throw error;
      throw new GatewayError(`Gateway unavailable: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      clearTimeout(timer);
    }
  }

  health(): Promise<{ ok: boolean; [key: string]: unknown }> { return this.request("health"); }
  async agents(): Promise<Agent[]> { return (await this.request<{ agents: Agent[] }>("agents")).agents ?? []; }
  async runs(workspaceId?: string): Promise<Run[]> {
    const query = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
    return (await this.request<{ runs: Run[] }>(`runs${query}`)).runs ?? [];
  }
  createRun(agent: string, taskId = "", workspaceId = "", manifestDigest = ""): Promise<Run> {
    return this.request("runs", { method: "POST", body: JSON.stringify({ agent, task_id: taskId, workspace_id: workspaceId, manifest_digest: manifestDigest }) });
  }
  stopRun(runId: string): Promise<Record<string, unknown>> { return this.request(`runs/${encodeURIComponent(runId)}/stop`, { method: "POST" }); }
  logs(agent: string): Promise<{ logs?: string; [key: string]: unknown }> { return this.request(`agents/${encodeURIComponent(agent)}/logs`); }
  async events(limit = 200, after = 0): Promise<Record<string, unknown>[]> {
    return (await this.request<{ events: Record<string, unknown>[] }>(`events?limit=${limit}&after=${after}`)).events ?? [];
  }
}
