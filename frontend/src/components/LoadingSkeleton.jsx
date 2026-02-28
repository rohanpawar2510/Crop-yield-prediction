export default function LoadingSkeleton({ rows = 3, className = '' }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="shimmer h-4 w-full" style={{ width: `${100 - i * 10}%` }} />
      ))}
    </div>
  );
}
