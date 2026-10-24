type AlertTone = 'info' | 'warning' | 'error'

type AlertProps = {
  tone?: AlertTone
  title: string
  children: string
}

export function Alert({ tone = 'info', title, children }: AlertProps) {
  return (
    <section className={`alert alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      <p>{children}</p>
    </section>
  )
}
