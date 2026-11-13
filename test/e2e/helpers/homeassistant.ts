/**
 * Talks to the Home Assistant that `test/e2e/docker-compose.yml` provides.
 *
 * The suite owns that instance: it starts from the tracked configuration in
 * `test/e2e/ha-config`, onboards it through the API and sets up a real bergfex
 * config entry itself, so a fresh clone needs nothing but Docker. Everything the
 * specs write goes into dashboards of their own.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
export const E2E_DIR = resolve(here, '..');
const COMPOSE_FILE = resolve(E2E_DIR, 'docker-compose.yml');
const COMPOSE_OVERRIDE = resolve(E2E_DIR, 'docker-compose.override.yml');
const TOKEN_FILE = resolve(E2E_DIR, '.auth.json');

/** Read from the compose file so the suite cannot drift from the environment. */
function portFromCompose(): string {
  const compose = readFileSync(COMPOSE_FILE, 'utf8');
  const match = compose.match(/'(\d+):8123'/) ?? compose.match(/"(\d+):8123"/);
  if (!match) throw new Error('No published Home Assistant port found in test/e2e/docker-compose.yml');
  return match[1];
}

export const PORT = process.env.HA_E2E_PORT ?? portFromCompose();
export const BASE_URL = `http://127.0.0.1:${PORT}`;
export const USERNAME = process.env.HA_E2E_USER ?? 'admin';
export const PASSWORD = process.env.HA_E2E_PASSWORD ?? 'password';

/** The resort the suite configures: the first one on the (fixture) Austrian overview. */
const RESORT = { language: 'at', type: 'alpine', country: 'Österreich', path: '/annaberg-lammertal/schneebericht/' };

/** Brings the e2e compose environment up if it is not running. */
export function ensureRunning(): void {
  const files = ['-f', COMPOSE_FILE];
  // Docker only merges an override automatically next to the default file name,
  // so a local one (CA bundle behind a proxy) is added by hand.
  if (existsSync(COMPOSE_OVERRIDE)) files.push('-f', COMPOSE_OVERRIDE);
  execFileSync('docker', ['compose', ...files, 'up', '-d'], { stdio: 'inherit' });
}

export async function waitForFrontend(timeoutMs = 300_000): Promise<void> {
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

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const CLIENT_ID = `${BASE_URL}/`;

async function postJson<T>(path: string, body: unknown, token?: string): Promise<{ status: number; body: T }> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  return { status: res.status, body: (text ? JSON.parse(text) : {}) as T };
}

/** Trades an authorization code for an access token, the way the frontend does. */
async function exchangeCode(code: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'authorization_code', code, client_id: CLIENT_ID }),
  });
  if (!res.ok) throw new Error(`token exchange failed: ${res.status} ${await res.text()}`);
  return ((await res.json()) as { access_token: string }).access_token;
}

/** Signs in with the suite's user over the login flow; null when it does not exist (yet). */
async function passwordLogin(): Promise<string | null> {
  const flow = await postJson<{ flow_id?: string }>('/auth/login_flow', {
    client_id: CLIENT_ID,
    handler: ['homeassistant', null],
    redirect_uri: CLIENT_ID,
  });
  if (!flow.body.flow_id) return null;
  const step = await postJson<{ type?: string; result?: string }>(`/auth/login_flow/${flow.body.flow_id}`, {
    username: USERNAME,
    password: PASSWORD,
    client_id: CLIENT_ID,
  });
  return step.body.type === 'create_entry' && step.body.result ? exchangeCode(step.body.result) : null;
}

/**
 * Makes sure Home Assistant has a user the suite can sign in as.
 *
 * A fresh instance has no user and sits in onboarding, which the frontend would
 * walk a person through; here the same steps are taken over the API. An
 * instance that is already onboarded (a second local run, whose `.storage`
 * survives in `ha-config`) is left alone. The onboarding endpoint answers 404
 * once it is done - and also while Home Assistant is still starting - so a 404
 * counts as "done" only when the suite's user can actually sign in.
 */
export async function ensureOnboarded(timeoutMs = 120_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const status = await fetch(`${BASE_URL}/api/onboarding`).catch(() => null);
    if (status?.ok) {
      const steps = (await status.json()) as { step: string; done: boolean }[];
      const pending = steps.filter((entry) => !entry.done).map((entry) => entry.step);
      if (pending.length === 0) return;
      if (!pending.includes('user')) {
        throw new Error(
          `Onboarding is half done (pending: ${pending.join(', ')}). Delete test/e2e/ha-config/.storage and start again.`,
        );
      }
      const created = await postJson<{ auth_code?: string }>('/api/onboarding/users', {
        client_id: CLIENT_ID,
        name: 'E2E Admin',
        username: USERNAME,
        password: PASSWORD,
        language: 'en',
      });
      if (!created.body.auth_code) throw new Error(`creating the e2e user failed: ${created.status}`);
      const token = await exchangeCode(created.body.auth_code);
      for (const step of ['core_config', 'analytics']) {
        const res = await postJson(`/api/onboarding/${step}`, {}, token);
        if (res.status !== 200) throw new Error(`onboarding step ${step} failed: ${res.status}`);
      }
      const integration = await postJson(
        '/api/onboarding/integration',
        { client_id: CLIENT_ID, redirect_uri: CLIENT_ID },
        token,
      );
      if (integration.status !== 200) throw new Error(`onboarding step integration failed: ${integration.status}`);
      return;
    }
    if ((await passwordLogin().catch(() => null)) !== null) return;
    await sleep(2000);
  }
  throw new Error(
    `Home Assistant is neither in onboarding nor accepts ${USERNAME}/${PASSWORD} at ${BASE_URL}. ` +
      'If ha-config/.storage holds an instance with other credentials, delete it or set HA_E2E_USER / HA_E2E_PASSWORD.',
  );
}

/**
 * Adds a bergfex config entry unless the instance already has one, and waits
 * until it has registered its sensors. The card resolves a resort through the
 * entity registry, so every spec that draws a resort needs this entry, and the
 * only honest way to get one is the integration's own config flow. bergfex itself
 * is answered from fixtures inside the container (see stub/sitecustomize.py).
 */
export async function ensureResortConfigured(timeoutMs = 180_000): Promise<void> {
  const token = readTokens().access_token;
  const get = async <T>(path: string): Promise<T> => {
    const res = await fetch(`${BASE_URL}${path}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return (await res.json()) as T;
  };

  const entries = await get<unknown[]>('/api/config/config_entries/entry?domain=bergfex');
  if (entries.length === 0) {
    type Flow = { type: string; flow_id: string; step_id?: string; errors?: Record<string, string>; reason?: string };
    let flow = (
      await postJson<Flow>(
        '/api/config/config_entries/flow',
        { handler: 'bergfex', show_advanced_options: false },
        token,
      )
    ).body;
    const answers: Record<string, Record<string, string>> = {
      user: { language: RESORT.language },
      type: { type: RESORT.type },
      country: { country: RESORT.country },
      ski_area_list_alpine: { ski_area: RESORT.path },
    };
    for (let guard = 0; flow.type === 'form' && guard < 8; guard++) {
      const answer = answers[flow.step_id ?? ''];
      if (!answer) throw new Error(`config flow asked for an unknown step: ${flow.step_id}`);
      if (flow.errors && Object.keys(flow.errors).length > 0) {
        throw new Error(
          `config flow step ${flow.step_id} reported ${JSON.stringify(flow.errors)} - did the container's bergfex stub load (PYTHONPATH=/stub)?`,
        );
      }
      flow = (await postJson<Flow>(`/api/config/config_entries/flow/${flow.flow_id}`, answer, token)).body;
    }
    if (flow.type !== 'create_entry') {
      throw new Error(`config flow ended with ${flow.type} ${flow.reason ?? JSON.stringify(flow.errors ?? {})}`);
    }
  }

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await findResortDevice();
      return;
    } catch {
      await sleep(3000);
    }
  }
  throw new Error(
    'The bergfex entry registered no resort device in time - did its first poll fail? Check the Home Assistant log.',
  );
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
