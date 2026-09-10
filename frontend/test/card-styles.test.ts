// @vitest-environment node
/**
 * Layout rules the card cannot do without at 400px, the width a Lovelace
 * sidebar column actually gets.
 *
 * These are asserted against the compiled stylesheet rather than a rendered
 * page because jsdom does no layout at all: it would report every one of these
 * as passing whether the declaration is there or not.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import * as sass from 'sass';

const css = sass.compileString(readFileSync(resolve(process.cwd(), 'frontend/src/styles/card.styles.scss'), 'utf8'), {
  style: 'expanded',
}).css;

/** The declarations of the first rule whose selector list contains `selector`. */
const block = (selector: string): string => {
  const match = css.match(new RegExp(`(^|})[^{}]*(?<![\\w-])${selector}(?![\\w-])[^{}]*\\{([^}]*)\\}`, 'm'));
  expect(match, `no rule for ${selector}`).not.toBeNull();
  return match![2];
};

describe('card.styles.scss at 400px', () => {
  it('keeps the status badge on one line', () => {
    // "SUMMER SEASON" wrapped into a two-storey badge and dragged the header
    // out of alignment with the resort name beside it.
    expect(block('\\.resort-status')).toMatch(/white-space:\s*nowrap/);
  });

  it('lets a detail item shrink into its grid column', () => {
    // A hard-coded width: calc(100% - 32px) assumed the icon is exactly 32px
    // and still refused to shrink below its content, so a label such as
    // "Slopes (Total)" escaped from under its progress bar.
    const rule = block('\\.detail-item-value');
    expect(rule).toMatch(/min-width:\s*0/);
    expect(rule).not.toMatch(/width:\s*calc\(100% - 32px\)/);
  });

  it('keeps a detail label inside its column', () => {
    const rule = block('\\.detail-item-label');
    expect(rule).toMatch(/overflow-wrap:\s*anywhere/);
    expect(rule).toMatch(/max-width:\s*100%/);
  });

  it('breaks a long unbroken title instead of letting it leave the card', () => {
    // Nothing in the file set a wrapping rule at all, so a resort name without
    // spaces ran off the right edge.
    expect(block('\\.card-content')).toMatch(/overflow-wrap:\s*anywhere/);
    expect(block('\\.resort-name')).toMatch(/min-width:\s*0/);
  });
});
