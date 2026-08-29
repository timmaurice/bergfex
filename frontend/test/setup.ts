import { vi, type Mock } from 'vitest';
import type { LovelaceCard } from '../src/types';
// Mock ResizeObserver for the JSDOM environment
const ResizeObserverMock = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));
vi.stubGlobal('ResizeObserver', ResizeObserverMock);
// Mock for Home Assistant helpers
interface TestWindow extends Window {
  loadCardHelpers: Mock;
}

// Guarded so suites that opt into the node environment can share this setup file.
if (typeof window !== 'undefined') {
  window.customCards = [];

  const testWindow = window as unknown as TestWindow;
  testWindow.loadCardHelpers = vi.fn().mockResolvedValue({
    createCardElement: vi.fn().mockResolvedValue({
      constructor: { getConfigElement: vi.fn().mockResolvedValue(undefined) },
    } as unknown as LovelaceCard),
  });
}
