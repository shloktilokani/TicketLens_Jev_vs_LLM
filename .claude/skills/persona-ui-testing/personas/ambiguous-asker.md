# Persona: Ambiguous Asker (stress persona)

**Who**: Not a real archetype — a constructed persona whose sole purpose is to test how the
system handles genuinely underspecified input.

**Voice**: Normal business language, but every input omits exactly one piece of information a
precise answer needs: no period, no metric ("how are we doing with X?"), a pronoun referring to
nothing established, or a dimension that maps to more than one field.

**Cares about**: Nothing in particular — it exists to probe clarification, default-assumption,
and graceful-degradation behaviour.

**Generating inputs**: Take a well-formed, answerable request about a real topic and remove one
key element. The ambiguity should be about missing scope, never about asking something
nonsensical. Tests: whether the system asks a good clarifying question, states the default it
chose, or silently guesses (the last is the failure to catch).
