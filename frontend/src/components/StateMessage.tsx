type StateMessageProps = {
  title: string
  description: string
  kind?: 'loading' | 'error'
}

export function StateMessage({ title, description, kind = 'loading' }: StateMessageProps) {
  return (
    <div className={`state-message state-message--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <span className="state-message__indicator" aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  )
}
