# Definition of Done

Applies to every item, on top of that item's own acceptance criteria. An item that meets its
acceptance criteria but fails this list is not shippable.

**Verification**
- [ ] Each acceptance criterion has a passing automated test, traced by ID
- [ ] Each unwanted-behaviour requirement has a negative test
- [ ] Coverage meets the risk-based target; mutation checked on critical logic
- [ ] Test was observed failing before the change and passing after

**Review and scanning**
- [ ] Reviewed and approved by someone (or a fresh context) that did not write it
- [ ] Formatter, linters, type checker, SAST, SCA, and secret scan all pass
- [ ] No new critical/high security findings without a documented, accepted risk

**Operability**
- [ ] Logs/metrics/traces sufficient to diagnose a failure of this change
- [ ] Performance checked against realistic data volumes
- [ ] Accessibility checked where user-facing

**Change safety**
- [ ] Migration reversible and rehearsed on production-sized data
- [ ] Backward compatibility preserved, or a deprecation plan published
- [ ] Feature flag in place if risk warrants, with an owner and an expiry date
- [ ] Rollback steps written down

**Records**
- [ ] Docs updated: API reference, changelog, runbook, folder READMEs, ADR if significant
- [ ] Spec amended wherever reality diverged from it
- [ ] Assumption log reviewed; anything unresolved escalated
- [ ] No debug artefacts, skipped tests, commented-out code, or placeholder TODOs
