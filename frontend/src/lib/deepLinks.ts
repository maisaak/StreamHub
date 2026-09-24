/** Deep-link resolution: native app scheme on mobile, web URL on desktop. */

export function isMobileDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
}

export function resolveWatchUrl(opts: {
  deepLink: string | null;
  webUrl: string;
  preferApp?: boolean;
}): string {
  const { deepLink, webUrl, preferApp } = opts;
  const wantApp = preferApp ?? isMobileDevice();
  if (wantApp && deepLink) return deepLink;
  return webUrl;
}

export function tryOpen(url: string): boolean {
  try {
    const w = window.open(url, "_blank", "noopener,noreferrer");
    return w !== null;
  } catch {
    return false;
  }
}
