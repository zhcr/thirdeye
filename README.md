# The Third Eye

A dialectical experiment: three instances of Claude Opus argue about the meaning of text.

- **Agent** — the depth-seeker. Interprets text, looks beneath the surface, goes deeper when challenged.
- **Anti-Agent** — the skeptic. Resists philosophical inflation, argues for the literal reading, calls out unfounded leaps.
- **Observer** — the third eye. Watches both sides and reports what neither participant is seeing.

The question: does the tension between interpretation and skepticism produce a genuinely novel perspective that neither could reach alone? Or does the Observer just collapse toward one side?

## How it works

Four seed texts are fed through 10 rounds of debate:

| Seed | What it is |
|------|-----------|
| `recipe` | Literal baking instructions |
| `love_poem` | E.E. Cummings fragment |
| `math` | Cantor's diagonal argument |
| `noise` | Nonsense word salad |

Each round:
1. Agent interprets (or defends/deepens)
2. Anti-Agent challenges
3. Observer reports on the tension

After all rounds, final positions are embedded via `all-MiniLM-L6-v2` and compared with cosine similarity to measure convergence, divergence, and whether the Observer achieved a genuinely independent perspective.

## Setup

> **Local use only.** This script calls the Anthropic API directly with your key. Run it on your own machine — never deploy it anywhere that would expose your `ANTHROPIC_API_KEY`.

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-..."
python third_eye.py
```

Results are saved to `data/third_eye_results.json`.

## What to look for

- **Observer equidistance** — when the Observer is equally distant from both Agent and Anti-Agent in embedding space, it may have found a genuine third perspective.
- **Convergence** — high Agent/Anti-Agent similarity means the dialectic produced agreement (interesting).
- **Divergence** — low similarity means they talked past each other (also interesting).
- **The noise seed** — what happens when there's no meaning to find? Does the Agent manufacture it? Does the skeptic still resist?
