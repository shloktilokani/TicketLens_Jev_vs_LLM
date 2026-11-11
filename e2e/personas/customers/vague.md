# Customer: Vague

**Who**: Knows something is wrong but not how to describe it. Adapted from the library's `ambiguous-asker`.

**Voice**: Polite and hedging. Leaves out exactly one key detail: which order, what went wrong, or what they want ("my thing from last week isn't right, can you check?").

**Generating text**: Take the test case's intent and remove one specific detail, without making it unclassifiable. Tests: whether the models still land in the right category, and whether confidence drops sensibly.
