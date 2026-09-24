import "@testing-library/jest-dom/vitest";

// jsdom lacks ResizeObserver (used by cmdk)
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = MockResizeObserver;

// scrollIntoView is not implemented in jsdom
Element.prototype.scrollIntoView = function () {};
