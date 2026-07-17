export default function ConfidenceGauge({ score, level }) {
  const clampedScore = Math.max(0, Math.min(100, score || 0))

  const color =
    level === 'high'     ? '#38ef7d' :
    level === 'moderate' ? '#f5a623' : '#f5576c'

  const gradientId = `gauge-grad-${level}`

  // SVG arc calculation
  const radius = 70
  const strokeWidth = 12
  const circumference = Math.PI * radius   // half circle
  const filled = (clampedScore / 100) * circumference

  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <svg width="180" height="100" viewBox="0 0 180 100">
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={color} stopOpacity="0.4" />
              <stop offset="100%" stopColor={color} />
            </linearGradient>
          </defs>

          {/* Background arc */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Filled arc */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />

          {/* Glow */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke={color}
            strokeWidth={2}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            opacity="0.3"
            filter="blur(2px)"
          />
        </svg>

        {/* Score text */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 32, fontWeight: 800, color, lineHeight: 1 }}>
            {clampedScore.toFixed(1)}
            <span style={{ fontSize: 16, fontWeight: 400 }}>%</span>
          </div>
        </div>
      </div>

      {/* Level badge */}
      <div style={{ marginTop: 12 }}>
        <span className={`badge badge-${level}`}>
          {level === 'high' ? '✅ High Confidence' :
           level === 'moderate' ? '⚠️ Moderate' : '🔴 Needs Review'}
        </span>
      </div>
    </div>
  )
}
