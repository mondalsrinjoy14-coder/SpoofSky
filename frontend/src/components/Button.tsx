import type { ButtonHTMLAttributes } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: 'primary' | 'quiet'
}

export function Button({ tone = 'primary', className = '', ...props }: ButtonProps) {
  return <button className={`button button--${tone} ${className}`.trim()} {...props} />
}
