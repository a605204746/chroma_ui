interface Props {
  size?: number
  className?: string
}

export default function WalnutLogo({ size = 32, className }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Drop shadow */}
      <ellipse cx="51" cy="93" rx="26" ry="5" fill="rgba(0,0,0,0.15)" />

      {/* Stem */}
      <path d="M 47 20 C 45 11 53 7 55 14" stroke="#5C3010" strokeWidth="3" fill="none" strokeLinecap="round" />

      {/* Main walnut shell body */}
      <ellipse cx="50" cy="56" rx="36" ry="32" fill="#B87530" />

      {/* Upper lighter region — gives a rounded 3D look */}
      <ellipse cx="50" cy="47" rx="33" ry="23" fill="#D4913A" />

      {/* Shine highlight */}
      <ellipse cx="36" cy="38" rx="11" ry="6.5" fill="#F2CA72" opacity="0.6" transform="rotate(-22 36 38)" />

      {/* Horizontal seam — the defining walnut feature */}
      <path d="M 16 57 C 30 48 70 48 84 57" stroke="#6B3810" strokeWidth="2.8" fill="none" strokeLinecap="round" />

      {/* Vertical center ridge (top half) */}
      <path d="M 50 24 C 52 36 52 46 50 57" stroke="#6B3810" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* Vertical center ridge (bottom half) */}
      <path d="M 50 57 C 48 68 48 76 50 88" stroke="#6B3810" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* Top-left wrinkles */}
      <path d="M 20 44 C 28 37 37 39 40 46" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M 22 33 C 31 27 40 30 43 37" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />

      {/* Top-right wrinkles */}
      <path d="M 80 44 C 72 37 63 39 60 46" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M 78 33 C 69 27 60 30 57 37" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />

      {/* Bottom-left wrinkle */}
      <path d="M 20 71 C 28 78 38 75 40 67" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />

      {/* Bottom-right wrinkle */}
      <path d="M 80 71 C 72 78 62 75 60 67" stroke="#6B3810" strokeWidth="1.6" fill="none" strokeLinecap="round" />

      {/* Outer border */}
      <ellipse cx="50" cy="56" rx="36" ry="32" fill="none" stroke="#5C2A0A" strokeWidth="2.5" />
    </svg>
  )
}
