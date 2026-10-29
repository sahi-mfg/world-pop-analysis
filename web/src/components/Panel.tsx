export default function Panel({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-card border border-border bg-surface ${className}`}>
      {title && (
        <header className="flex items-start justify-between gap-4 px-card-pad pt-4">
          <div>
            <h2 className="type-section">{title}</h2>
            {subtitle && <p className="mt-0.5 type-small text-muted">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function ErrorNotice({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="rounded-card bg-error-tint px-card-pad py-4">
      <p className="type-label text-error">Couldn't load population data for this area.</p>
      <p className="mt-1 max-w-3xl type-small break-words text-ink">{message}</p>
      <button onClick={onRetry} className="mt-2 type-label text-ink underline underline-offset-2">
        Try again
      </button>
    </div>
  );
}
