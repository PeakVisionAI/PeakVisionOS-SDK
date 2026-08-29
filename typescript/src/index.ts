export interface Agent {
  name: string;
  status?: AgentStatus;
  primitives?: string[];
}

export type AgentStatus = "active" | "inactive" | "starting" | "stopped" | string;
export type RunStatus = "created" | "queued" | "running" | "completed" | "failed" | "cancelled" | "stopped" | string;

export interface Run {
  run_id: string;
  agent: string;
  status?: RunStatus;
  exit_code?: number | null;
}

export interface Workspace {
  workspace_id: string;
  name: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

export interface Task {
  task_id: string;
  workspace_id: string;
  title: string;
  description?: string;
  agent?: string;
  status?: string;
  metadata?: Record<string, unknown>;
}

export interface RunEvent {
  event_id?: number;
  type: string;
  run_id?: string;
  task_id?: string;
  timestamp?: number;
  payload?: Record<string, unknown>;
}

export interface GatewayNode {
  node_id: string;
  name: string;
  online?: boolean;
  capabilities?: Record<string, unknown>;
}

export class GatewayError extends Error {
  readonly status?: number;
  readonly code: string;
  readonly retryable: boolean;
  readonly requestId?: string;
  readonly details?: unknown;
  readonly retryAfter?: number;
  readonly cause?: unknown;

  constructor(message: string, status?: number, options: {
    code?: string; retryable?: boolean; requestId?: string; details?: unknown;
    retryAfter?: number; cause?: unknown;
  } = {}) {
    super(message);
    this.name = "GatewayError";
    this.status = status;
    this.code = options.code ?? "gateway_error";
    this.retryable = options.retryable ?? false;
    this.requestId = options.requestId;
    this.details = options.details;
    this.retryAfter = options.retryAfter;
    this.cause = options.cause;
  }
}

export interface RequestOptions { signal?: AbortSignal; }

export interface AgentOSOptions {
  endpoint?: string;
  token?: string;
  timeoutMs?: number;
  fetch?: typeof globalThis.fetch;
  retry?: RetryOptions;
}

export interface RetryOptions {
  maxAttempts?: number;
  backoffMs?: number;
  maxBackoffMs?: number;
  retryStatuses?: number[];
  retryPostWithIdempotencyKey?: boolean;
}

function environment(name: string): string | undefined {
  // Keep the package usable in browsers and Node without requiring @types/node.
  const runtime = globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  };
  return runtime.process?.env?.[name];
}

/** Remote PeakVisionOS control-plane client. Primitive calls remain local-only. */
export class AgentOS {
  private readonly endpoint: string;
  private readonly token: string;
  private readonly timeoutMs: number;
  private readonly fetcher: typeof globalThis.fetch;
  private readonly retry: Required<RetryOptions>;

  constructor(options: AgentOSOptions = {}) {
    const endpoint = options.endpoint ?? environment("PVOS_ENDPOINT") ?? environment("AGENTOS_ENDPOINT");
    if (!endpoint || !/^https?:\/\//.test(endpoint)) {
      throw new TypeError("endpoint must use http:// or https://");
    }
    this.endpoint = endpoint.replace(/\/$/, "");
    this.token = options.token ?? environment("PVOS_TOKEN") ?? environment("AGENTOS_TOKEN") ?? "";
    this.timeoutMs = options.timeoutMs ?? 15000;
    this.fetcher = options.fetch ?? globalThis.fetch;
    if (!this.fetcher) throw new TypeError("fetch is required (use Node 18+ or pass options.fetch)");
    this.retry = {
      maxAttempts: options.retry?.maxAttempts ?? 3,
      backoffMs: options.retry?.backoffMs ?? 250,
      maxBackoffMs: options.retry?.maxBackoffMs ?? 4000,
      retryStatuses: options.retry?.retryStatuses ?? [408, 425, 429, 500, 502, 503, 504],
      retryPostWithIdempotencyKey: options.retry?.retryPostWithIdempotencyKey ?? true,
    };
    if (this.retry.maxAttempts < 1 || this.retry.backoffMs < 0 || this.retry.maxBackoffMs < 0) {
      throw new TypeError("invalid retry options");
    }
  }

  protected async request<T>(path: string, init: RequestInit = {}, requestOptions: RequestOptions = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    if (init.body) headers.set("Content-Type", "application/json");
    const method = (init.method ?? "GET").toUpperCase();
    const idempotent = method === "GET" || method === "HEAD" || method === "OPTIONS" ||
      (headers.has("Idempotency-Key") && this.retry.retryPostWithIdempotencyKey);
    const attempts = idempotent ? this.retry.maxAttempts : 1;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      const abort = () => controller.abort();
      if (requestOptions.signal?.aborted) controller.abort();
      requestOptions.signal?.addEventListener("abort", abort, { once: true });
      try {
        const response = await this.fetcher(`${this.endpoint}/${path.replace(/^\//, "")}`, { ...init, headers, signal: controller.signal });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          const retryable = this.retry.retryStatuses.includes(response.status);
          if (retryable && attempt + 1 < attempts) {
            await this.delay(attempt);
            continue;
          }
          const error = body?.error;
          const message = typeof error === "object" && error !== null ? String(error.message ?? "request failed") : String(error ?? "request failed");
          const retryAfterValue = typeof error === "object" && error !== null ? Number(error.retry_after) : undefined;
          throw new GatewayError(message, response.status, {
            code: typeof error === "object" && error !== null ? String(error.code ?? "http_error") : "http_error",
            retryable,
            requestId: response.headers.get("X-Request-Id") ?? undefined,
            details: typeof error === "object" && error !== null ? error.details : undefined,
            retryAfter: Number.isFinite(retryAfterValue) ? retryAfterValue : undefined,
          });
        }
        return body as T;
      } catch (error) {
        if (error instanceof GatewayError) throw error;
        if (requestOptions.signal?.aborted) {
          throw new GatewayError("Request aborted", undefined, { code: "aborted", retryable: false, cause: error });
        }
        if (attempt + 1 < attempts) {
          await this.delay(attempt);
          continue;
        }
        throw new GatewayError(`Gateway unavailable: ${error instanceof Error ? error.message : String(error)}`, undefined, { code: "transport_error", retryable: true, cause: error });
      } finally {
        clearTimeout(timer);
        requestOptions.signal?.removeEventListener("abort", abort);
      }
    }
    throw new GatewayError("Gateway request exhausted retry policy", undefined);
  }

  private delay(attempt: number): Promise<void> {
    const delay = Math.min(this.retry.backoffMs * (2 ** attempt), this.retry.maxBackoffMs);
    return delay ? new Promise((resolve) => setTimeout(resolve, delay)) : Promise.resolve();
  }

  health(options?: RequestOptions): Promise<{ ok: boolean; [key: string]: unknown }> { return this.request("health", {}, options); }
  async agents(options?: RequestOptions): Promise<Agent[]> { return (await this.request<{ agents: Agent[] }>("agents", {}, options)).agents ?? []; }
  async workspaces(options?: RequestOptions): Promise<Workspace[]> { return (await this.request<{ workspaces: Workspace[] }>("workspaces", {}, options)).workspaces ?? []; }
  createWorkspace(name: string, options?: RequestOptions): Promise<Workspace> {
    if (!name.trim()) throw new TypeError("name is required");
    return this.request("workspaces", { method: "POST", body: JSON.stringify({ name: name.trim() }) }, options);
  }
  async tasks(workspaceId?: string, options?: RequestOptions): Promise<Task[]> {
    const query = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
    return (await this.request<{ tasks: Task[] }>(`tasks${query}`, {}, options)).tasks ?? [];
  }
  createTask(workspaceId: string, title: string, description = "", agent = "", options?: RequestOptions): Promise<Task> {
    if (!workspaceId.trim() || !title.trim()) throw new TypeError("workspaceId and title are required");
    return this.request("tasks", { method: "POST", body: JSON.stringify({ workspace_id: workspaceId.trim(), title: title.trim(), description, agent }) }, options);
  }
  async runs(workspaceId?: string, options?: RequestOptions): Promise<Run[]> {
    const query = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
    return (await this.request<{ runs: Run[] }>(`runs${query}`, {}, options)).runs ?? [];
  }
  createRun(agent: string, taskId = "", workspaceId = "", manifestDigest = "", idempotencyKey?: string, options?: RequestOptions): Promise<Run> {
    if (!agent.trim()) throw new TypeError("agent is required");
    const headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined;
    return this.request("runs", { method: "POST", headers, body: JSON.stringify({ agent: agent.trim(), task_id: taskId, workspace_id: workspaceId, manifest_digest: manifestDigest }) }, options);
  }
  run(runId: string, options?: RequestOptions): Promise<Run> {
    if (!runId) throw new TypeError("runId is required");
    return this.request(`runs/${encodeURIComponent(runId)}`, {}, options);
  }
  stopRun(runId: string, options?: RequestOptions): Promise<Record<string, unknown>> { return this.request(`runs/${encodeURIComponent(runId)}/stop`, { method: "POST" }, options); }
  logs(agent: string, options?: RequestOptions): Promise<{ logs?: string; [key: string]: unknown }> { return this.request(`agents/${encodeURIComponent(agent)}/logs`, {}, options); }
  async eventsPage(limit = 200, after = 0, options?: RequestOptions): Promise<{ events: RunEvent[]; after?: number }> {
    if (!Number.isInteger(limit) || limit < 1 || limit > 1000 || !Number.isInteger(after) || after < 0) throw new TypeError("invalid event pagination");
    return this.request(`events?limit=${limit}&after=${after}`, {}, options);
  }
  async events(limit = 200, after = 0, options?: RequestOptions): Promise<RunEvent[]> {
    return (await this.eventsPage(limit, after, options)).events ?? [];
  }
  async *iterEvents(after = 0, limit = 200, maxPages?: number, options?: RequestOptions): AsyncGenerator<RunEvent> {
    let cursor = after;
    let pages = 0;
    while (maxPages === undefined || pages < maxPages) {
      const page = await this.eventsPage(limit, cursor, options);
      const items = page.events ?? [];
      if (!items.length) return;
      for (const event of items) yield event;
      const ids = items.map((event) => event.event_id).filter((id): id is number => Number.isInteger(id));
      const next = ids.length ? Math.max(...ids) : cursor;
      if (next <= cursor) return;
      cursor = next;
      pages += 1;
    }
  }
}

/** Product-named alias. Existing AgentOS imports remain compatible. */
export class PeakVisionOS extends AgentOS {}

/** Gateway registry client for node management and snapshots. */
export class RemoteGateway extends AgentOS {
  async nodes(options?: RequestOptions): Promise<GatewayNode[]> { return (await this.request<{ nodes: GatewayNode[] }>("nodes", {}, options)).nodes ?? []; }
  registerNode(nodeId: string, name: string, baseUrl: string, token: string, capabilities: Record<string, unknown> = {}, options?: RequestOptions): Promise<GatewayNode> {
    if (!nodeId.trim() || !name.trim() || !baseUrl.trim() || !token) throw new TypeError("nodeId, name, baseUrl and token are required");
    return this.request("nodes", { method: "POST", body: JSON.stringify({ node_id: nodeId, name, base_url: baseUrl, token, capabilities }) }, options);
  }
  rotateNodeToken(nodeId: string, token: string, options?: RequestOptions): Promise<Record<string, unknown>> {
    if (!nodeId || !token) throw new TypeError("nodeId and token are required");
    return this.request(`nodes/${encodeURIComponent(nodeId)}/token`, { method: "POST", body: JSON.stringify({ token }) }, options);
  }
  snapshot(nodeId: string, options?: RequestOptions): Promise<Record<string, unknown>> {
    if (!nodeId) throw new TypeError("nodeId is required");
    return this.request(`nodes/${encodeURIComponent(nodeId)}/snapshot`, {}, options);
  }
}
