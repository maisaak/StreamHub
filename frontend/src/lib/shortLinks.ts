export async function shareContent(opts: {
  title: string;
  text: string;
  url: string;
}): Promise<"shared" | "copied"> {
  const nav = navigator as Navigator & {
    share?: (data: { title: string; text: string; url: string }) => Promise<void>;
  };
  if (nav.share && /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent)) {
    try {
      await nav.share({ title: opts.title, text: opts.text, url: opts.url });
      return "shared";
    } catch {
      // user cancelled -> fall through to copy
    }
  }
  await navigator.clipboard.writeText(opts.url);
  return "copied";
}
