# Example 01 — Standard Library

This example walks through the full workflow using characters from the
**built-in standard library** — no setup required beyond installing the package.

---

## Prerequisites

```bash
pip install agentic-mindset
```

All commands below can be run from any directory.

---

## Step 1 — List available characters

```bash
mindset list
```

Expected output (partial):

```
  atticus-finch
  confucius
  gojo-satoru
  leonardo-da-vinci
  levi-ackermann
  marcus-aurelius
  napoleon-bonaparte
  naruto-uzumaki
  nikola-tesla
  odysseus
  seneca
  sherlock-holmes
  sun-tzu
```

---

## Step 2 — Generate a single character

```bash
mindset generate sun-tzu
```

The compiled prompt block is printed to stdout. The first section looks like:

```
=== THINKING FRAMEWORK ===
Core principles:
- Strategic deception: All warfare is based on deception...
```

You can pipe this directly into a file:

```bash
mindset generate sun-tzu > sun_tzu_prompt.txt
```

---

## Step 3 — Fuse two characters with weights

```bash
mindset generate sun-tzu marcus-aurelius --weights 6,4 --explain
```

The `--explain` flag prints a compilation summary to stderr:

```
Characters: sun-tzu (60%), marcus-aurelius (40%)
Strategy:   blend
Format:     text
Schema:     1.0
```

The fused prompt block blends both characters' thinking frameworks, personality
traits, and voice according to the specified weights.

---

## Step 4 — Inject into Claude (one-shot)

```bash
mindset run claude --persona sun-tzu "Analyze competitor strategy"
```

Claude responds with Sun Tzu's behavioral overlay applied — strategic,
indirect, focused on positioning and information advantage.

Multi-persona injection:

```bash
mindset run claude \
  --persona sun-tzu \
  --persona marcus-aurelius \
  --weights 6,4 \
  "How should I approach this negotiation?"
```

---

## Step 5 — Interactive mode

Omit the query argument to launch a **live Claude session** with the mindset applied.
Claude will remain in the interactive session until you exit (Ctrl+D or `exit`).

```bash
mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4
```

Every message you send in that session will be processed by Claude with the
fused Sun Tzu + Marcus Aurelius behavioral overlay active.

---

## Next step

See [02-custom-character](../02-custom-character/README.md) to learn how to
create and inject your own character.
