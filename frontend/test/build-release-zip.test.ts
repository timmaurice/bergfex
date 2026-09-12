// @vitest-environment node
import { describe, expect, it } from 'vitest';
// @ts-expect-error - plain ESM build script, no type declarations
import { isExcluded, EXCLUDED_DIRS, EXCLUDED_NAMES } from '../../scripts/build-release-zip.mjs';

describe('release archive contents', () => {
  it.each([
    'manifest.json',
    '__init__.py',
    'bergfex-card.js',
    'parser.py',
    'translations/de.json',
    'translations/pl.json',
  ])('ships %s', (path) => {
    expect(isExcluded(path)).toBe(false);
  });

  it.each([
    'tests/test_parser.py',
    'tests/fixtures/hintertux.html',
    '__pycache__/parser.cpython-314.pyc',
    'tests/__pycache__/test_parser.cpython-314.pyc',
    '.pytest_cache/CACHEDIR.TAG',
    '.DS_Store',
    'translations/.DS_Store',
    'parser.pyc',
    'home-assistant.log',
  ])('never ships %s', (path) => {
    expect(isExcluded(path)).toBe(true);
  });

  it('excludes a directory itself, not just what is inside it', () => {
    for (const directory of EXCLUDED_DIRS) {
      expect(isExcluded(directory)).toBe(true);
    }
  });

  it('does not exclude files that merely start with an excluded name', () => {
    // `tests` is excluded, `test_helpers.py` and `testing.py` are not.
    expect(isExcluded('test_helpers.py')).toBe(false);
    expect(isExcluded('testing.py')).toBe(false);
    expect(isExcluded('tests_are_elsewhere.py')).toBe(false);
  });

  it('does not exclude a legitimate file whose name contains an excluded one', () => {
    expect(isExcluded('my_tests_helper.py')).toBe(false);
    expect(EXCLUDED_NAMES.has('.DS_Store')).toBe(true);
  });
});
