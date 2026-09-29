export default function Logo({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2563eb" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#g)" />
      <path d="M11 13h18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H19l-5 4v-4h-3a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z" fill="#fff" />
      <circle cx="16" cy="19.5" r="1.6" fill="#4f46e5" />
      <circle cx="21" cy="19.5" r="1.6" fill="#4f46e5" />
      <circle cx="26" cy="19.5" r="1.6" fill="#4f46e5" />
    </svg>
  );
}