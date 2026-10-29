/** The product mark: a measured rectangle on the map grid. */
export default function Mark({ className = "size-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" className={className} aria-hidden="true">
      <rect x="1" y="1" width="18" height="18" rx="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <rect x="7" y="5" width="9" height="8" className="fill-primary" />
    </svg>
  );
}
