# SpoofSky

SpoofSky is a local-first aircraft navigation anomaly analysis platform. It distinguishes raw observations, data-quality problems, detected anomalies, suspected events, and independently verified incidents.

## Stage 1–2 development commands

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs on the Vite development server and renders the Stage 2 analysis shell. The UI remains read-only and does not claim that live tracking data is connected.

Checks:

```powershell
npm run test
npm run typecheck
npm run build
```

### Backend

Use the `py` launcher on this Windows environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
py -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend checks:

```powershell
py -m pytest backend\tests -q
```

The backend exposes a safe health/status surface and a local simulated-fixture ingestion endpoint. Detection analysis and frontend API integration are planned for the next stage.
