import { Link } from "react-router-dom";

export default function EmptyState({
  title,
  hint,
  actionLabel,
  actionTo,
  children,
}: {
  title: string;
  hint?: string;
  actionLabel?: string;
  actionTo?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-neutral-300 dark:border-neutral-700 p-8 text-center">
      <p className="text-lg font-semibold">{title}</p>
      {hint && <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">{hint}</p>}
      {actionLabel && actionTo && (
        <Link
          to={actionTo}
          className="mt-4 inline-flex items-center rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-600"
        >
          {actionLabel}
        </Link>
      )}
      {children}
    </div>
  );
}
