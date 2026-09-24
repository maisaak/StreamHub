import { cn } from "@/lib/utils";

const INITIALS: Record<string, string> = {
  kinopoisk: "КП",
  ivi: "ivi",
  okko: "Okko",
  youtube: "YT",
  rutube: "Ru",
  wink: "Wink",
  start: "ST",
  premier: "PR",
};

export default function ProviderBadge({
  id,
  name,
  color,
  size = "md",
  dimmed = false,
  className,
}: {
  id: string;
  name: string;
  color: string;
  size?: "sm" | "md" | "lg";
  dimmed?: boolean;
  className?: string;
}) {
  const sizes = {
    sm: "h-5 min-w-5 px-1 text-[10px]",
    md: "h-6 min-w-6 px-1.5 text-xs",
    lg: "h-10 min-w-10 px-3 text-base",
  };
  return (
    <span
      title={name}
      aria-label={name}
      className={cn(
        "inline-flex items-center justify-center rounded-md font-bold text-white shrink-0",
        sizes[size],
        dimmed && "opacity-40 saturate-50",
        className,
      )}
      style={{ backgroundColor: color }}
    >
      {INITIALS[id] ?? name.slice(0, 2).toUpperCase()}
    </span>
  );
}
