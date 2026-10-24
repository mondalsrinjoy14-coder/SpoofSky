# SpoofSky fixture datasets

Files in this directory are deterministic development inputs. They are not live data and must remain labelled with `provenance_kind: "simulated"` and `is_demo: true` in the source manifest.

`demo_observations.json` contains valid records plus a duplicate and an out-of-order record so the ingestion report demonstrates both accepted observations and explicit quality findings.
