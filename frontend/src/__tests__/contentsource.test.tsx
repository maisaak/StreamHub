import { describe, expect, it } from "vitest";
import { chooseBestSource } from "@/pages/ContentDetail";
import type { Source } from "@/types";

function src(pid: string, extra: Partial<Source> = {}): Source {
  return {
    provider_id: pid,
    provider_name: pid,
    brand_color: "#000",
    logo_url: "",
    external_url: `https://${pid}.example/${pid}`,
    deep_link: null,
    price: null,
    is_subscription: false,
    quality: "HD",
    connected: false,
    rank: 0,
    ...extra,
  };
}

describe("source selection", () => {
  it("returns ranked-first source (backend order)", () => {
    const sources = [
      src("ivi", { is_subscription: true, connected: true }),
      src("okko", { price: 299 }),
    ];
    expect(chooseBestSource(sources)?.provider_id).toBe("ivi");
  });

  it("returns null for empty list", () => {
    expect(chooseBestSource([])).toBeNull();
  });
});
