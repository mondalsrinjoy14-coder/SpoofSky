import { StatusBadge } from './StatusBadge'
import { AircraftExplorer } from '../features/AircraftExplorer'

const navigation = [
  { label: 'Workspace', active: true },
  { label: 'Datasets', active: false, note: 'Planned' },
  { label: 'Detection', active: false, note: 'Results next' },
]

const evidenceStages = [
  { title: 'Raw observations', detail: 'Source records retained', state: 'Awaiting input' },
  { title: 'Data quality', detail: 'Validation and quality flags', state: 'Ingestion foundation' },
  { title: 'Detected anomalies', detail: 'Explainable detector evidence', state: 'Investigation queue' },
  { title: 'Suspected events', detail: 'Spatial and temporal grouping', state: 'Cautious grouping' },
]

function RadarMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 32 32" role="img" aria-label="SpoofSky mark">
      <circle cx="16" cy="16" r="11" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M16 5v22M5 16h22M8.2 8.2l15.6 15.6" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.55" />
      <circle cx="16" cy="16" r="3" fill="currentColor" />
    </svg>
  )
}

function Navigation() {
  return (
    <nav className="primary-nav" aria-label="Primary navigation">
      {navigation.map((item) => (
        <div
          className={`primary-nav__item${item.active ? ' primary-nav__item--active' : ''}`}
          key={item.label}
          aria-current={item.active ? 'page' : undefined}
        >
          <span>{item.label}</span>
          {item.note && <span className="primary-nav__note">{item.note}</span>}
        </div>
      ))}
    </nav>
  )
}

function EvidenceChain() {
  return (
    <section className="panel panel--evidence" aria-labelledby="evidence-title">
      <div className="panel__header">
        <div>
          <span className="eyebrow">Processing model</span>
          <h2 id="evidence-title">Evidence chain</h2>
        </div>
        <span className="panel__index">01 / 04</span>
      </div>
      <div className="evidence-list">
        {evidenceStages.map((stage, index) => (
          <div className="evidence-row" key={stage.title}>
            <span className="evidence-row__index">0{index + 1}</span>
            <div className="evidence-row__copy">
              <strong>{stage.title}</strong>
              <span>{stage.detail}</span>
            </div>
            <span className="evidence-row__state">{stage.state}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#workspace" aria-label="SpoofSky workspace">
          <RadarMark />
          <span className="brand__name">SpoofSky</span>
          <span className="brand__descriptor">Navigation intelligence</span>
        </a>
        <Navigation />
        <div className="topbar__meta">
          <StatusBadge tone="positive">Local workspace</StatusBadge>
          <span className="topbar__version">Stage 5</span>
        </div>
      </header>

      <main id="workspace" className="main-content">
        <section className="page-intro" aria-labelledby="page-title">
          <div>
            <span className="eyebrow">Analysis workspace</span>
            <h1 id="page-title">Ground truth before inference.</h1>
            <p>
              A controlled workspace for examining aircraft-tracking observations without
              overstating what the data can prove.
            </p>
          </div>
          <div className="page-intro__status">
            <span className="page-intro__status-label">Workspace state</span>
            <StatusBadge tone="caution">Simulated source</StatusBadge>
          </div>
        </section>

        <section className="notice" aria-label="Current workspace notice">
          <span className="notice__bar" aria-hidden="true" />
          <div>
            <strong>Explorer is source-bound.</strong>
            <p>
               The map below renders stored observations returned by the backend. The current
               source is simulated and historical; no live feed is configured.
            </p>
          </div>
           <span className="notice__code">S5 / INVESTIGATION</span>
        </section>

        <AircraftExplorer />

        <section className="lower-grid" aria-label="Evidence and operating notes">
          <EvidenceChain />
          <section className="panel notes-panel" aria-labelledby="notes-title">
            <div className="panel__header">
              <div>
                <span className="eyebrow">Operating boundary</span>
                <h2 id="notes-title">Analyst notes</h2>
              </div>
              <span className="panel__index">READ FIRST</span>
            </div>
            <ul className="notes-list">
              <li>An aircraft-tracking anomaly cannot prove GPS spoofing or jamming.</li>
              <li>Derived events will retain detector evidence, thresholds, and uncertainty.</li>
              <li>Independent verification is a separate status from an inferred event.</li>
            </ul>
            <div className="notes-panel__footer">
              <span className="notes-panel__marker" aria-hidden="true">i</span>
              <span>Research tool · not a certified aviation safety system</span>
            </div>
          </section>
        </section>
      </main>

      <footer className="footer">
        <span>SPOOFSKY / LOCAL RESEARCH ENVIRONMENT</span>
        <span>Source status: simulated fixture · no live feed</span>
      </footer>
    </div>
  )
}
