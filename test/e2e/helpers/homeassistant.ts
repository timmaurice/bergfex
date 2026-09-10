/**
 * Talks to the Home Assistant the repository's docker-compose already provides.
 *
 * The suite deliberately reuses that instance instead of booting one of its
 * own: it is already onboarded and carries real entities, which is what makes
 * an end-to-end assertion worth more than a mock. Everything the suite writes
 * goes into a dashboard of its own, so the manual playground stays intact.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
export const E2E_DIR = resolve(here, '..');
const REPO_ROOT = resolve(E2E_DIR, '../..');
const TOKEN_FILE = resolve(E2E_DIR, '.auth.json');

/** Read from the compose file so the suite cannot drift from the environment. */
function portFromCompose(): string {
  const compose = readFileSync(resolve(REPO_ROOT, 'docker-compose.yml'), 'utf8');
  const match = compose.match(/'(\d+):8123'/) ?? compose.match(/"(\d+):8123"/);
  if (!match) throw new Error('No published Home Assistant port found in docker-compose.yml');
  return match[1];
}

export const PORT = process.env.HA_E2E_PORT ?? portFromCompose();
export const BASE_URL = `http://127.0.0.1:${PORT}`;
export const USERNAME = process.env.HA_E2E_USER ?? 'admin';
export const PASSWORD = process.env.HA_E2E_PASSWORD ?? 'password';

/** Brings the repository's own compose environment up if it is not running. */
export function ensureRunning(): void {
  execFileSync('docker', ['compose', 'up', '-d'], { cwd: REPO_ROOT, stdio: 'inherit' });
}

export async function waitForFrontend(timeoutMs = 180_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      // Not /api/onboarding: that endpoint is gone once onboarding is done.
      const res = await fetch(`${BASE_URL}/manifest.json`);
      if (res.ok) return;
    } catch {
      // not listening yet
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error(`Home Assistant did not answer at ${BASE_URL} within ${timeoutMs}ms`);
}

export interface Tokens {
  access_token: string;
}

export function saveTokens(tokens: Tokens): void {
  writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2));
}

export function readTokens(): Tokens {
  if (!existsSync(TOKEN_FILE)) throw new Error('No token file - did global setup run?');
  return JSON.parse(readFileSync(TOKEN_FILE, 'utf8')) as Tokens;
}

/**
 * Sends one command over the websocket API and returns its result. Node ships a
 * WebSocket client, so this needs no dependency, and it is the same API the
 * frontend itself speaks.
 */
export async function callWebsocket<T = unknown>(message: Record<string, unknown>): Promise<T> {
  const token = readTokens().access_token;
  const socket = new WebSocket(`ws://127.0.0.1:${PORT}/api/websocket`);

  return new Promise<T>((resolve_, reject) => {
    const fail = (reason: string) => {
      socket.close();
      reject(new Error(reason));
    };
    const timer = setTimeout(() => fail('websocket timed out'), 30_000);

    socket.addEventListener('error', () => fail('websocket error'));
    socket.addEventListener('message', (event) => {
      const payload = JSON.parse(String(event.data)) as Record<string, unknown>;
      switch (payload.type) {
        case 'auth_required':
          socket.send(JSON.stringify({ type: 'auth', access_token: token }));
          return;
        case 'auth_invalid':
          clearTimeout(timer);
          fail('websocket authentication was refused');
          return;
        case 'auth_ok':
          socket.send(JSON.stringify({ id: 1, ...message }));
          return;
        case 'result': {
          clearTimeout(timer);
          socket.close();
          if (payload.success) resolve_(payload.result as T);
          else reject(new Error(`websocket command failed: ${JSON.stringify(payload.error)}`));
        }
      }
    });
  });
}

/** Puts a state on the bus, the way any client would. */
export async function setState(
  entityId: string,
  state: string,
  attributes: Record<string, unknown> = {},
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/states/${entityId}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${readTokens().access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ state, attributes }),
  });
  if (!res.ok) throw new Error(`setting ${entityId} failed: ${res.status} ${await res.text()}`);
}

export async function removeState(entityId: string): Promise<void> {
  await fetch(`${BASE_URL}/api/states/${entityId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${readTokens().access_token}` },
  });
}

/**
 * Gives the caller its own dashboard.
 *
 * Every spec file asks for a different name, so specs can run in parallel
 * without fighting over one dashboard - and none of them touches whatever the
 * manual test instance has on its own dashboards.
 */
export async function useDashboard(name: string, config: Record<string, unknown>): Promise<string> {
  const urlPath = `e2e-${name}`;
  const dashboards = await callWebsocket<{ url_path: string }[]>({
    type: 'lovelace/dashboards/list',
  });
  if (!dashboards.some((dashboard) => dashboard.url_path === urlPath)) {
    await callWebsocket({
      type: 'lovelace/dashboards/create',
      url_path: urlPath,
      title: `E2E ${name}`,
      mode: 'storage',
      show_in_sidebar: false,
    });
  }
  await callWebsocket({ type: 'lovelace/config/save', url_path: urlPath, config });
  return urlPath;
}

/** The Lovelace resources Home Assistant has persisted. */
export async function resources(): Promise<{ id: string; url: string }[]> {
  return callWebsocket({ type: 'lovelace/resources' });
}

/** One entry of Home Assistant's entity registry. */
export interface RegistryEntry {
  entity_id: string;
  device_id: string | null;
  platform: string;
  config_entry_id: string | null;
}

export async function entityRegistry(): Promise<RegistryEntry[]> {
  return callWebsocket({ type: 'config/entity_registry/list' });
}

/**
 * Picks a resort the running instance really has.
 *
 * The card resolves a resort through `hass.entities[...].device_id`, so it only
 * ever sees entities that live in the entity registry - a state pushed in over
 * the REST API alone is invisible to it. Rather than hard-coding whatever this
 * particular playground happens to hold, the suite looks up a bergfex device and
 * then overwrites that device's states with values it controls.
 */
export async function findResortDevice(): Promise<{
  deviceId: string;
  slug: string;
  configEntryId: string | null;
  statusEntity: string;
}> {
  const registry = await entityRegistry();
  const status = registry.find(
    (entry) =>
      entry.platform === 'bergfex' &&
      entry.device_id !== null &&
      /^sensor\..+_status$/.test(entry.entity_id) &&
      !entry.entity_id.endsWith('_operation_status'),
  );
  if (!status) throw new Error('The bergfex integration has no resort device in this instance');
  return {
    deviceId: status.device_id as string,
    slug: status.entity_id.replace(/^sensor\.(.+)_status$/, '$1'),
    configEntryId: status.config_entry_id,
    statusEntity: status.entity_id,
  };
}

/** Name the device registry carries, which is what the card paints as the title. */
export async function deviceName(deviceId: string): Promise<string> {
  const devices = await callWebsocket<{ id: string; name: string; name_by_user: string | null }[]>({
    type: 'config/device_registry/list',
  });
  const device = devices.find((entry) => entry.id === deviceId);
  if (!device) throw new Error(`No device ${deviceId}`);
  return device.name_by_user ?? device.name;
}

/**
 * Hands the resort back to the integration.
 *
 * The suite writes over the states of real entities, so it reloads their config
 * entry afterwards and the coordinator's own values return - the playground is
 * left the way it was found.
 */
export async function reloadConfigEntry(entryId: string): Promise<void> {
  await fetch(`${BASE_URL}/api/services/homeassistant/reload_config_entry`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${readTokens().access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ entry_id: entryId }),
  });
}
