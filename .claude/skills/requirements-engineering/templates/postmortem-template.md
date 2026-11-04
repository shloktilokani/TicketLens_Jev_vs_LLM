# Postmortem: <short incident title>

Date: <> · Duration: <> · Severity: <> · Author: <> · Status: Draft | Final

## Summary
One paragraph that someone outside the team can understand.

## Impact
Users affected · Requests affected · Duration of impact · Error budget consumed · Business impact

## Timeline (UTC)
| Time | Event | Evidence source |
|---|---|---|
| | First signal | |
| | Detected | |
| | Mitigation began | |
| | Service restored | |
| | Fully resolved | |

## Contributing factors
Two to five systemic factors, framed blamelessly — gaps in process, tooling, documentation, or
signals. Not "X shipped a bad change" but "a change could reach production without a canary
stage because the pipeline had no gate for this service."

## What went well
Name it explicitly so it gets repeated.

## What made this harder than necessary
Missing runbook, noisy alerts, unclear ownership, slow rollback, misleading dashboards…

## Action items
| ID | Action | Type (mitigative / preventative) | Owner | Due | Ticket |
|---|---|---|---|---|---|

## Lessons
What generalises beyond this incident.
