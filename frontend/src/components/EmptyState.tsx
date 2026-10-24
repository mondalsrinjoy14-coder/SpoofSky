type EmptyStateProps = {
  label: string
  title: string
  description: string
}

export function EmptyState({ label, title, description }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-state__label">{label}</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  )
}
