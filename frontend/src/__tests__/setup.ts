import "@testing-library/jest-dom/vitest";

// Mock IntersectionObserver for jsdom (not available in test environment)
(global as any).IntersectionObserver = class IntersectionObserver {
  root = null;
  rootMargin = "";
  thresholds = [];
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
};