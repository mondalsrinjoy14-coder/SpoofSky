import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('SpoofSky application shell', () => {
  it('renders the truthful Stage 1 workspace state', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Ground truth before inference.' })).toBeVisible()
    expect(screen.getByText('Simulated source')).toBeVisible()
    expect(screen.queryByText('Analysis pipeline not implemented')).not.toBeInTheDocument()
    expect(screen.getByText(/The current source is simulated and historical/)).toBeVisible()
  })

  it('exposes the product boundary without suggesting a confirmed incident', () => {
    render(<App />)

    expect(screen.getAllByText('An aircraft-tracking anomaly cannot prove GPS spoofing or jamming.')).toHaveLength(1)
    expect(screen.getAllByText('Independent verification is a separate status from an inferred event.')).toHaveLength(1)
  })
})
