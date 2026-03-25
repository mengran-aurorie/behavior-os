# Launch Post

## Twitter / X (280 chars)

> Most AI personas are fake.
>
> They collapse when you mix them. They can't explain themselves. They hallucinate identity.
>
> We built a system that compiles behavior instead of prompting personas.
>
> Demo + link ↓
>
> github.com/mengran-aurorie/agentic-mindset

---

## Hacker News

**Title:**

We built a system that makes AI personas composable, testable, and explainable

**Body:**

Most "AI personas" are prompt templates with personality adjectives. Blend two and you get generic hedging. Ask the system why it behaved a certain way and you get nothing.

Agentic Mindset is a behavior compilation system — not prompt engineering.

Three independently testable stages:

```
CharacterPack(s) → ConflictResolver → BehaviorIR → ClaudeRenderer → AI Agent
```

**The core difference:** the resolver decides which traits survive blending. The renderer emits behavioral directives, not character descriptions. The `--explain` YAML traces every decision.

Same question, different behavior:

- *Negotiating with a stronger competitor*
- Claude (baseline): "consider both approaches..."
- Sun Tzu: "shape the terrain so agreement favors you"
- Steve Jobs: "are they necessary? what's the minimum you need?"
- Sun Tzu + Jobs blend: "position first — then act precisely, not aggressively"

That blend phrase does not appear in either solo output. The fusion produces behavior neither constituent has alone.

The benchmark suite verifies all critical claims — including that dropped traits stay dropped and no biographical facts are fabricated.

Demo: `mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- "We are negotiating with a much larger competitor."`

GitHub: https://github.com/mengran-aurorie/AGENTIC-MINDSET
