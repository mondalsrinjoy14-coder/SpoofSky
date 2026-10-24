type StatusTone = 'neutral' | 'caution' | 'positive'

type StatusBadgeProps = {
  children: string
  tone?: StatusTone
}

export function StatusBadge({ children, tone = 'neutral' }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${tone}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {children}
    </span>
  )
}
