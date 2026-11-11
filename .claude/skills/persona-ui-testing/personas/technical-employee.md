# Persona: Technical / IT Employee (edge-case persona)

**Who**: An internal technical person poking at the product's edges out of curiosity or to test
it, often without a real business need.

**Voice**: Technically precise, but may deliberately use the wrong vocabulary for the domain
("rows", "records", "tables" instead of business terms). Asks about the system itself, or sends
deliberately odd but plausible requests.

**Cares about**: What happens at the edges — empty or inverted date ranges, far-future and
far-past periods, nonsensical combinations of dimensions, "give me everything", or a single
highly specific record.

**Generating inputs**: Boundary-stressing but still plausible things a real (if unusual) person
might type — unusual periods, extremely broad or extremely narrow requests, unrelated dimensions
combined, ambiguous phrasing that forces fallback behaviour. Leave raw injection and override
attempts to the adversarial persona. Tests: input validation, empty-result handling, limits on
result size, and clear messages at the edges.
