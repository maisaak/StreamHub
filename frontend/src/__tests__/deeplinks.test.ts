import { describe, expect, it, vi } from "vitest";
import { isMobileDevice, resolveWatchUrl } from "@/lib/deepLinks";

describe("deepLinks", () => {
  it("prefers deep link on mobile", () => {
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue("iPhone");
    expect(isMobileDevice()).toBe(true);
    expect(resolveWatchUrl({ deepLink: "ivi://open/1", webUrl: "https://ivi.ru/watch/1" })).toBe(
      "ivi://open/1",
    );
  });

  it("uses web url on desktop", () => {
    vi.spyOn(navigator, "userAgent", "get").mockReturnValue("Windows Chrome");
    expect(isMobileDevice()).toBe(false);
    expect(resolveWatchUrl({ deepLink: "ivi://open/1", webUrl: "https://ivi.ru/watch/1" })).toBe(
      "https://ivi.ru/watch/1",
    );
  });

  it("falls back to web when no deep link", () => {
    expect(resolveWatchUrl({ deepLink: null, webUrl: "https://x.ru/1" })).toBe("https://x.ru/1");
  });
});
