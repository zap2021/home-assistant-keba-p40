import "./style.css";

type HttpMethod = "GET" | "POST" | "DELETE";

type Settings = {
  host: string;
  port: string;
  username: string;
  password: string;
  verifySsl: boolean;
  selectedSerial: string;
  startTokenId: string;
};

type Tokens = {
  accessToken: string;
  refreshToken: string;
};

type LogEntry = {
  timestamp: string;
  title: string;
  detail: string;
};

const defaultSettings: Settings = {
  host: "192.168.147.169",
  port: "8443",
  username: "admin",
  password: "",
  verifySsl: false,
  selectedSerial: "",
  startTokenId: "",
};

const state = {
  settings: { ...defaultSettings },
  tokens: {
    accessToken: "",
    refreshToken: "",
  } satisfies Tokens,
  busy: false,
  latestWallbox: null as unknown,
  latestWallboxes: [] as unknown[],
  latestVersion: "",
  latestSerial: "",
  logs: [] as LogEntry[],
};

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root not found");
}

render();

function render(): void {
  app.innerHTML = `
    <main class="page">
      <section class="hero">
        <div class="eyebrow">KEBA REST API · Test Client</div>
        <h1>Lokale API prüfen, bevor Home Assistant übernimmt.</h1>
        <p>Die Webanwendung spricht im Dev-Betrieb über den lokalen Vite-Forwarder mit deiner KEBA-Wallbox. Damit kannst du Login, Status-Endpunkte und schreibende Funktionen gezielt verifizieren.</p>
      </section>

      <section class="layout">
        <div class="stack">
          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h2>Verbindung</h2>
                <span>${escapeHtml(buildTargetBase())}</span>
              </div>

              <div class="grid two">
                <div class="field">
                  <label for="host">Host</label>
                  <input id="host" name="host" value="${escapeHtml(state.settings.host)}" />
                </div>
                <div class="field">
                  <label for="port">Port</label>
                  <input id="port" name="port" value="${escapeHtml(state.settings.port)}" />
                </div>
              </div>

              <div class="grid two">
                <div class="field">
                  <label for="username">Benutzername</label>
                  <input id="username" name="username" value="${escapeHtml(state.settings.username)}" />
                </div>
                <div class="field">
                  <label for="password">Passwort</label>
                  <input id="password" name="password" type="password" value="${escapeHtml(state.settings.password)}" />
                </div>
              </div>

              <label class="checkbox">
                <input id="verifySsl" name="verifySsl" type="checkbox" ${state.settings.verifySsl ? "checked" : ""} />
                SSL-Zertifikat der Wallbox prüfen
              </label>

              <div class="button-row">
                <button class="button primary" data-action="login" ${disabledAttr()}>Login testen</button>
                <button class="button" data-action="refresh" ${disabledAttr(!state.tokens.refreshToken)}>Token refresh</button>
                <button class="button ghost" data-action="version" ${disabledAttr()}>Version</button>
                <button class="button ghost" data-action="serial" ${disabledAttr()}>Seriennummer</button>
              </div>

              <div class="status-card">
                <div class="status-line"><strong>Access Token</strong><span>${state.tokens.accessToken ? maskToken(state.tokens.accessToken) : "nicht gesetzt"}</span></div>
                <div class="status-line"><strong>Refresh Token</strong><span>${state.tokens.refreshToken ? maskToken(state.tokens.refreshToken) : "nicht gesetzt"}</span></div>
                <div class="status-line"><strong>API Version</strong><span>${escapeHtml(state.latestVersion || "unbekannt")}</span></div>
                <div class="status-line"><strong>Geräte-Seriennummer</strong><span>${escapeHtml(state.latestSerial || "unbekannt")}</span></div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h2>Wallbox Funktionen</h2>
                <span>Authentifizierte Endpunkte</span>
              </div>

              <div class="field">
                <label for="selectedSerial">Wallbox-Seriennummer</label>
                <input id="selectedSerial" name="selectedSerial" value="${escapeHtml(state.settings.selectedSerial)}" placeholder="Wird nach Listenabruf automatisch gesetzt" />
              </div>

              <div class="field">
                <label for="startTokenId">Optional Token-ID für StartCharging</label>
                <input id="startTokenId" name="startTokenId" value="${escapeHtml(state.settings.startTokenId)}" placeholder="z. B. A2D80F8E" />
              </div>

              <div class="action-grid">
                <button class="button" data-action="wallboxes" ${disabledAttr()}>Wallboxes laden</button>
                <button class="button" data-action="wallbox" ${disabledAttr(!hasSerial())}>Wallbox lesen</button>
                <button class="button" data-action="startCharging" ${disabledAttr(!hasSerial())}>Start charging</button>
                <button class="button danger" data-action="stopCharging" ${disabledAttr(!hasSerial())}>Stop charging</button>
                <button class="button" data-action="availabilityOn" ${disabledAttr(!hasSerial())}>Verfügbar</button>
                <button class="button danger" data-action="availabilityOff" ${disabledAttr(!hasSerial())}>Nicht verfügbar</button>
                <button class="button" data-action="lockOn" ${disabledAttr(!hasSerial())}>Dauersperre setzen</button>
                <button class="button danger" data-action="lockOff" ${disabledAttr(!hasSerial())}>Dauersperre lösen</button>
              </div>

              <div class="hint">Schreibende Funktionen greifen direkt auf die lokale Wallbox zu. Für produktive Tests zuerst Status und Identität verifizieren.</div>
            </div>
          </article>
        </div>

        <div class="stack">
          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h3>Aktueller Status</h3>
                <span class="pill ${state.busy ? "" : state.tokens.accessToken ? "success" : ""} ${state.busy ? "" : ""}">
                  ${state.busy ? "Request läuft" : state.tokens.accessToken ? "Authentifiziert" : "Bereit"}
                </span>
              </div>

              <div class="status-card">
                <div class="status-line"><strong>Ausgewählte Wallbox</strong><span>${escapeHtml(state.settings.selectedSerial || "nicht gesetzt")}</span></div>
                <div class="status-line"><strong>Letzter Listenabruf</strong><span>${String(state.latestWallboxes.length)}</span></div>
                <div class="status-line"><strong>Letztes Objekt</strong><span>${state.latestWallbox ? "vorhanden" : "leer"}</span></div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-inner stack">
              <div class="section-title">
                <h3>Antwortprotokoll</h3>
                <button class="button ghost" data-action="clearLogs">Leeren</button>
              </div>
              <div class="terminal"><pre>${escapeHtml(formatLogs())}</pre></div>
            </div>
          </article>
        </div>
      </section>
    </main>
  `;

  bindInputs();
  bindActions();
}

function bindInputs(): void {
  const fields = ["host", "port", "username", "password", "selectedSerial", "startTokenId"] as const;

  for (const field of fields) {
    const element = document.querySelector<HTMLInputElement>(`#${field}`);
    element?.addEventListener("input", (event) => {
      const target = event.currentTarget as HTMLInputElement;
      state.settings[field] = target.value;
      render();
    });
  }

  const verifySsl = document.querySelector<HTMLInputElement>("#verifySsl");
  verifySsl?.addEventListener("change", (event) => {
    state.settings.verifySsl = (event.currentTarget as HTMLInputElement).checked;
    render();
  });
}

function bindActions(): void {
  document.querySelectorAll<HTMLButtonElement>("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.action;
      if (!action) {
        return;
      }
      await handleAction(action);
    });
  });
}

async function handleAction(action: string): Promise<void> {
  if (action === "clearLogs") {
    state.logs = [];
    render();
    return;
  }

  state.busy = true;
  render();

  try {
    switch (action) {
      case "login":
        await login();
        break;
      case "refresh":
        await refreshAccessToken();
        break;
      case "version":
        await getVersion();
        break;
      case "serial":
        await getSerial();
        break;
      case "wallboxes":
        await getWallboxes();
        break;
      case "wallbox":
        await getWallbox();
        break;
      case "startCharging":
        await startCharging();
        break;
      case "stopCharging":
        await callWallboxAction("POST", wallboxPath("/stopCharging"), undefined, "Stop charging");
        break;
      case "availabilityOn":
        await callWallboxAction("POST", wallboxPath("/changeAvailability"), { available: true }, "Availability on");
        break;
      case "availabilityOff":
        await callWallboxAction("POST", wallboxPath("/changeAvailability"), { available: false }, "Availability off");
        break;
      case "lockOn":
        await callWallboxAction("POST", wallboxPath("/permanentlyLock"), {}, "Permanent lock on");
        break;
      case "lockOff":
        await callWallboxAction("DELETE", wallboxPath("/permanentlyLock"), undefined, "Permanent lock off");
        break;
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  } catch (error) {
    pushLog(action, error instanceof Error ? error.message : String(error));
  } finally {
    state.busy = false;
    render();
  }
}

async function login(): Promise<void> {
  const response = await apiRequest<{ accessToken?: string; refreshToken?: string }>("POST", "/v2/jwt/login", {
    username: state.settings.username,
    password: state.settings.password,
  });

  state.tokens.accessToken = response.accessToken ?? "";
  state.tokens.refreshToken = response.refreshToken ?? "";
  pushLog("Login", response);
}

async function refreshAccessToken(): Promise<void> {
  const response = await apiRequest<{ accessToken?: string; refreshToken?: string }>("POST", "/v2/jwt/refresh", undefined, {
    Authorization: `Bearer ${state.tokens.refreshToken}`,
  });

  state.tokens.accessToken = response.accessToken ?? state.tokens.accessToken;
  state.tokens.refreshToken = response.refreshToken ?? state.tokens.refreshToken;
  pushLog("Refresh token", response);
}

async function getVersion(): Promise<void> {
  const response = await apiRequest<string>("GET", "/version");
  state.latestVersion = typeof response === "string" ? response : JSON.stringify(response);
  pushLog("Version", response);
}

async function getSerial(): Promise<void> {
  const response = await apiRequest<string>("GET", "/serialnumber");
  state.latestSerial = typeof response === "string" ? response : JSON.stringify(response);
  if (!state.settings.selectedSerial && typeof response === "string") {
    state.settings.selectedSerial = response;
  }
  pushLog("Serial number", response);
}

async function getWallboxes(): Promise<void> {
  const response = await authorizedRequest<{ wallboxes?: unknown[] }>("GET", "/v2/wallboxes");
  state.latestWallboxes = response.wallboxes ?? [];

  if (!state.settings.selectedSerial && state.latestWallboxes.length > 0) {
    const first = state.latestWallboxes[0] as { serialNumber?: string };
    if (first.serialNumber) {
      state.settings.selectedSerial = first.serialNumber;
    }
  }

  pushLog("Wallboxes", response);
}

async function getWallbox(): Promise<void> {
  const response = await authorizedRequest<unknown>("GET", wallboxPath());
  state.latestWallbox = response;
  pushLog("Wallbox", response);
}

async function startCharging(): Promise<void> {
  const suffix = state.settings.startTokenId
    ? `/startCharging?id=${encodeURIComponent(state.settings.startTokenId)}`
    : "/startCharging";
  await callWallboxAction("POST", wallboxPath(suffix), undefined, "Start charging");
}

async function callWallboxAction(
  method: HttpMethod,
  path: string,
  body: unknown,
  title: string,
): Promise<void> {
  const response = await authorizedRequest<unknown>(method, path, body);
  state.latestWallbox = response;
  pushLog(title, response);
}

async function authorizedRequest<T>(
  method: HttpMethod,
  path: string,
  body?: unknown,
): Promise<T> {
  if (!state.tokens.accessToken) {
    throw new Error("Kein Access Token vorhanden. Zuerst Login ausführen.");
  }

  return apiRequest<T>(method, path, body, {
    Authorization: `Bearer ${state.tokens.accessToken}`,
  });
}

async function apiRequest<T>(
  method: HttpMethod,
  path: string,
  body?: unknown,
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  const response = await fetch(`/keba-api${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "x-keba-target": buildTargetBase(),
      "x-keba-insecure": String(!state.settings.verifySsl),
      ...extraHeaders,
    },
    body: method === "GET" || body === undefined ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  const parsed = tryParseJson(text);

  if (!response.ok) {
    throw new Error(`[${response.status}] ${typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2)}`);
  }

  return parsed as T;
}

function wallboxPath(suffix = ""): string {
  if (!hasSerial()) {
    throw new Error("Keine Wallbox-Seriennummer gesetzt.");
  }
  return `/v2/wallboxes/${encodeURIComponent(state.settings.selectedSerial)}${suffix}`;
}

function buildTargetBase(): string {
  return `https://${state.settings.host}:${state.settings.port}`;
}

function hasSerial(): boolean {
  return state.settings.selectedSerial.trim().length > 0;
}

function formatLogs(): string {
  if (state.logs.length === 0) {
    return "Noch keine Requests ausgeführt.";
  }

  return state.logs
    .map((entry) => `[${entry.timestamp}] ${entry.title}\n${entry.detail}`)
    .join("\n\n");
}

function pushLog(title: string, detail: unknown): void {
  state.logs.unshift({
    timestamp: new Date().toLocaleTimeString("de-DE"),
    title,
    detail: typeof detail === "string" ? detail : JSON.stringify(detail, null, 2),
  });

  state.logs = state.logs.slice(0, 20);
}

function tryParseJson(text: string): unknown {
  const normalized = text.trim();
  if (normalized.length === 0) {
    return "";
  }

  try {
    return JSON.parse(normalized);
  } catch {
    return normalized;
  }
}

function maskToken(token: string): string {
  if (token.length <= 20) {
    return token;
  }
  return `${token.slice(0, 12)}…${token.slice(-8)}`;
}

function disabledAttr(disabled = state.busy): string {
  return disabled ? "disabled" : "";
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
