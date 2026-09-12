#!/usr/bin/env node
/**
 * Builds the HACS release archive.
 *
 * HACS extracts `bergfex.zip` straight into the user's `custom_components/bergfex/`,
 * so whatever lands in here lands on every installation. Test fixtures, caches and
 * bytecode compiled against the release runner's Python have no business being there.
 *
 * Run it directly to inspect what a release would ship:
 *   node scripts/build-release-zip.mjs --dry-run
 */

import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, rmSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SOURCE_DIR = join(ROOT, 'custom_components', 'bergfex');
const OUTPUT = join(ROOT, 'bergfex.zip');

/** Without these the integration does not work at all. */
const REQUIRED_ENTRIES = ['manifest.json', '__init__.py', 'bergfex-card.js'];

export const EXCLUDED_DIRS = new Set(['tests', '__pycache__', '.pytest_cache', 'node_modules', '.git']);
export const EXCLUDED_NAMES = new Set(['.DS_Store', 'Thumbs.db', 'desktop.ini']);
export const EXCLUDED_EXTENSIONS = ['.pyc', '.pyo', '.log'];

/**
 * Decide whether a path relative to the component directory ships to users.
 * Kept pure and exported so the rules can be tested without touching the disk.
 */
export function isExcluded(relativePath) {
  const segments = relativePath.split('/');
  if (segments.slice(0, -1).some((segment) => EXCLUDED_DIRS.has(segment))) return true;

  const name = segments[segments.length - 1];
  if (EXCLUDED_DIRS.has(name)) return true;
  if (EXCLUDED_NAMES.has(name)) return true;
  return EXCLUDED_EXTENSIONS.some((extension) => name.endsWith(extension));
}

function collectFiles(directory, prefix = '') {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (isExcluded(relativePath)) continue;
    if (entry.isDirectory()) {
      files.push(...collectFiles(join(directory, entry.name), relativePath));
    } else if (entry.isFile()) {
      files.push(relativePath);
    }
  }
  return files;
}

function fail(message) {
  // GitHub renders ::error:: as an annotation on the run; harmless locally.
  console.error(`::error::${message}`);
  process.exit(1);
}

/**
 * HACS reads the version from the manifest, not from the tag. If the two disagree
 * the store offers an update that installs something else, so refuse to build.
 */
function checkManifestVersion(expectedVersion) {
  const manifestPath = join(SOURCE_DIR, 'manifest.json');
  const { version } = JSON.parse(readFileSync(manifestPath, 'utf8'));

  if (!version) fail('manifest.json has no version field.');
  if (!expectedVersion) {
    console.log(`   manifest version : ${version} (no tag to compare against)`);
    return version;
  }

  const tag = expectedVersion.replace(/^v/, '');
  if (version !== tag) {
    fail(`manifest.json says version "${version}" but the release tag is "${tag}". Bump the manifest before tagging.`);
  }
  console.log(`   manifest version : ${version} (matches tag)`);
  return version;
}

function formatSize(bytes) {
  return bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} K` : `${(bytes / 1024 / 1024).toFixed(1)} M`;
}

function buildArchive(files) {
  rmSync(OUTPUT, { force: true });
  try {
    // -X drops platform extra fields; -@ takes the file list on stdin so the
    // include rules live here rather than in a wall of shell -x patterns.
    execFileSync('zip', ['-X', '-q', '-@', OUTPUT], {
      cwd: SOURCE_DIR,
      input: files.join('\n'),
    });
  } catch (error) {
    if (error.code === 'ENOENT') fail('The `zip` command is not available on this machine.');
    throw error;
  }
}

/** Read the archive back rather than trusting what we meant to put in it. */
function verifyArchive(expectedFiles) {
  const entries = execFileSync('unzip', ['-Z1', OUTPUT], { encoding: 'utf8' })
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((entry) => !entry.endsWith('/'));

  const missing = REQUIRED_ENTRIES.filter((required) => !entries.includes(required));
  if (missing.length) {
    fail(`bergfex.zip is missing required ${missing.length === 1 ? 'file' : 'files'}: ${missing.join(', ')}`);
  }

  const leaked = entries.filter((entry) => isExcluded(entry));
  if (leaked.length) {
    fail(`bergfex.zip contains files that must never ship: ${leaked.join(', ')}`);
  }

  const unexpected = entries.filter((entry) => !expectedFiles.includes(entry));
  if (unexpected.length) {
    fail(`bergfex.zip contains unexpected entries: ${unexpected.join(', ')}`);
  }

  return entries;
}

function main() {
  const dryRun = process.argv.includes('--dry-run');
  const expectedVersion = process.env.VERSION ?? process.argv.find((arg) => arg.startsWith('--version='))?.slice(10);

  if (!existsSync(SOURCE_DIR)) fail(`Component directory not found: ${SOURCE_DIR}`);

  console.log('Building HACS release archive');
  checkManifestVersion(expectedVersion);

  const files = collectFiles(SOURCE_DIR);
  if (!files.length) fail('No files matched — refusing to build an empty archive.');

  const skipped = collectSkipped(SOURCE_DIR);
  console.log(`   files included   : ${files.length}`);
  if (skipped.length) console.log(`   files excluded   : ${skipped.length}`);

  if (dryRun) {
    console.log('\nWould ship:');
    for (const file of files) console.log(`   ${file}`);
    if (skipped.length) {
      console.log('\nWould skip:');
      for (const file of skipped) console.log(`   ${file}`);
    }
    return;
  }

  buildArchive(files);
  const entries = verifyArchive(files);

  console.log(`   archive          : bergfex.zip (${formatSize(statSync(OUTPUT).size)}, ${entries.length} entries)`);
  console.log('\nContents:');
  for (const entry of entries) console.log(`   ${entry}`);
}

/** Only used for the summary, so it does not need to be fast. */
function collectSkipped(directory, prefix = '') {
  const skipped = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (isExcluded(relativePath)) {
      skipped.push(entry.isDirectory() ? `${relativePath}/` : relativePath);
      continue;
    }
    if (entry.isDirectory()) skipped.push(...collectSkipped(join(directory, entry.name), relativePath));
  }
  return skipped;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
