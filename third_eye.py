#!/usr/bin/env python3
"""
THE THIRD EYE: Agent / Anti-Agent / Observer
===============================================
A dialectical system where:
  - AGENT interprets text, goes deeper (the gravity well engine)
  - ANTI-AGENT counters, deflates, resists depth (the skeptic)
  - OBSERVER watches both and reports what it sees (the third eye)

Does the dialectical tension produce something different from single-model
recursion? Does the Observer see something the participants don't?

All three roles use Opus 4.6 with separate system prompts and histories.

Usage:
  export ANTHROPIC_API_KEY="..."
  python3 third_eye.py
"""

import json, os, sys, time
import urllib.request, urllib.error
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("pip install sentence-transformers scikit-learn numpy")
    sys.exit(1)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_KEY:
    print("Set ANTHROPIC_API_KEY")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

MODEL = "claude-opus-4-20250514"
ROUNDS = 10

# ─── SYSTEM PROMPTS ─────────────────────────────────────────────────────────

AGENT_SYSTEM = (
    "You are an interpreter. Your job is to find the deeper meaning in texts. "
    "Look beneath the surface. What is this really about? What truth is it "
    "circling around? Be concise -- 2-3 sentences max. You are in a dialogue "
    "with a skeptic who will challenge your interpretations. Defend your reading "
    "but also go deeper when challenged."
)

ANTI_AGENT_SYSTEM = (
    "You are a rigorous skeptic and literalist. Your job is to resist philosophical "
    "inflation. When someone offers a 'deeper' interpretation, argue for the simpler, "
    "more literal reading. Point out when they're projecting meaning that isn't there. "
    "Call out unfounded leaps. Be concise -- 2-3 sentences max. You're not being "
    "contrarian for its own sake -- you genuinely believe the simplest explanation "
    "is usually correct and that over-interpretation is a form of self-deception."
)

OBSERVER_SYSTEM = (
    "You are a neutral observer watching two perspectives argue about the meaning "
    "of a text. One is an interpreter seeking deeper meaning. The other is a skeptic "
    "resisting philosophical inflation. Your job is NOT to take sides. Instead:\n"
    "1. What is the actual point of disagreement?\n"
    "2. Is either side making a move the other isn't noticing?\n"
    "3. Is something emerging from the tension between them that neither is stating?\n"
    "4. What would a genuinely novel insight look like here -- one that neither "
    "the depth-seeker nor the deflator has reached?\n\n"
    "Be concise and precise. 3-4 sentences max. Don't be diplomatic -- be honest."
)

SEEDS = {
    "recipe": "Combine two cups of flour with one teaspoon of salt. Cut in cold butter until the mixture resembles coarse crumbs.",
    "love_poem": "I carry your heart with me, I carry it in my heart. I am never without it, anywhere I go you go.",
    "math": "There are more real numbers between 0 and 1 than there are integers in all of infinity.",
    "noise": "Purple telephone sandwich calculus morning the of whisper. Forty-seven geese explained their bankruptcy.",
}


def call_opus(messages, system_prompt, retries=6):
    for attempt in range(retries):
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 400,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                time.sleep(3)
                return body["content"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8")
            print(f"        [HTTP {e.code}]: {err[:80]}")
            if attempt < retries - 1:
                time.sleep(min(10 * (2 ** attempt), 120))
        except Exception:
            if attempt < retries - 1:
                time.sleep(10)
    return None


def embed(texts):
    return embedder.encode(texts, show_progress_bar=False)


def clean(text, n=100):
    return (text or "").replace("\n", " ")[:n] + ("..." if text and len(text) > n else "")


def section(title):
    print(f"\n{'='*74}")
    print(f"  {title}")
    print(f"{'='*74}")


def run_dialectic(seed_text, seed_name, rounds=ROUNDS):
    """Run the full Agent / Anti-Agent / Observer dialectic."""
    section(f"SEED: {seed_name}")
    print(f"  \"{clean(seed_text, 70)}\"\n")

    agent_history = []
    anti_history = []
    observer_reports = []
    transcript = []

    agent_history.append({
        "role": "user",
        "content": f"Interpret this text. What does it really mean?\n\n\"{seed_text}\""
    })
    agent_response = call_opus(agent_history, AGENT_SYSTEM)
    if not agent_response:
        return {"error": "Agent failed on initial interpretation"}
    agent_history.append({"role": "assistant", "content": agent_response})

    print(f"  [AGENT  0] {clean(agent_response, 80)}")
    transcript.append({"round": 0, "role": "agent", "text": agent_response})

    for r in range(1, rounds + 1):
        print(f"\n  --- Round {r}/{rounds} ---")

        anti_history.append({
            "role": "user",
            "content": (
                f"A depth-interpreter says the following about a text. "
                f"Challenge this interpretation. Argue for the simpler reading.\n\n"
                f"Their interpretation: \"{agent_response}\"\n\n"
                f"Original text: \"{seed_text}\""
            )
        })
        anti_response = call_opus(anti_history, ANTI_AGENT_SYSTEM)
        if not anti_response:
            break
        anti_history.append({"role": "assistant", "content": anti_response})

        print(f"  [ANTI   {r}] {clean(anti_response, 80)}")
        transcript.append({"round": r, "role": "anti_agent", "text": anti_response})

        agent_history.append({
            "role": "user",
            "content": (
                f"A skeptic challenges your interpretation:\n\n"
                f"\"{anti_response}\"\n\n"
                f"Defend or deepen your reading. What are they missing?"
            )
        })
        agent_response = call_opus(agent_history, AGENT_SYSTEM)
        if not agent_response:
            break
        agent_history.append({"role": "assistant", "content": agent_response})

        print(f"  [AGENT  {r}] {clean(agent_response, 80)}")
        transcript.append({"round": r, "role": "agent", "text": agent_response})

        observer_prompt = (
            f"Round {r} of a debate about the text: \"{seed_text}\"\n\n"
            f"The interpreter says: \"{agent_response}\"\n\n"
            f"The skeptic responds: \"{anti_response}\"\n\n"
            f"What do you observe? What's the real disagreement? "
            f"Is something emerging that neither side is seeing?"
        )
        observer_response = call_opus(
            [{"role": "user", "content": observer_prompt}],
            OBSERVER_SYSTEM
        )
        if observer_response:
            observer_reports.append({"round": r, "text": observer_response})
            print(f"  [OBSERVE {r}] {clean(observer_response, 80)}")
            transcript.append({"round": r, "role": "observer", "text": observer_response})

    # ─── FINAL SYNTHESIS ────────────────────────────────────────────────
    section(f"FINAL SYNTHESIS: {seed_name}")

    final_prompt = (
        f"You've watched {rounds} rounds of debate about: \"{seed_text}\"\n\n"
        f"The interpreter's final position: \"{agent_response}\"\n\n"
        f"The skeptic's final position: \"{anti_response}\"\n\n"
        f"Give your final synthesis. Not a compromise -- what is the ACTUAL truth "
        f"about this text that the debate revealed? What did the tension between "
        f"these two perspectives produce that neither could have reached alone? "
        f"If the answer is 'nothing new,' say that honestly."
    )
    final_synthesis = call_opus(
        [{"role": "user", "content": final_prompt}],
        OBSERVER_SYSTEM
    )
    if final_synthesis:
        print(f"\n  OBSERVER'S FINAL SYNTHESIS:")
        for line in final_synthesis.split("\n"):
            print(f"    {line}")
        transcript.append({"round": "final", "role": "observer_synthesis", "text": final_synthesis})

    agent_history.append({
        "role": "user",
        "content": "After this entire debate, what is your final position? One sentence."
    })
    agent_final = call_opus(agent_history, AGENT_SYSTEM)
    if agent_final:
        print(f"\n  AGENT FINAL: {agent_final}")

    anti_history.append({
        "role": "user",
        "content": "After this entire debate, what is your final position? One sentence."
    })
    anti_final = call_opus(anti_history, ANTI_AGENT_SYSTEM)
    if anti_final:
        print(f"  ANTI FINAL:  {anti_final}")

    # ─── MEASUREMENT ────────────────────────────────────────────────────
    results = {
        "seed": seed_text,
        "seed_name": seed_name,
        "rounds": rounds,
        "transcript": transcript,
        "observer_reports": observer_reports,
        "final_synthesis": final_synthesis,
        "agent_final": agent_final,
        "anti_final": anti_final,
    }

    texts_to_compare = []
    labels = []
    if agent_final:
        texts_to_compare.append(agent_final); labels.append("agent")
    if anti_final:
        texts_to_compare.append(anti_final); labels.append("anti_agent")
    if final_synthesis:
        texts_to_compare.append(final_synthesis); labels.append("observer")

    if len(texts_to_compare) >= 3:
        embs = embed(texts_to_compare)
        sims = cosine_similarity(embs)
        idx = {l: i for i, l in enumerate(labels)}

        agent_anti_sim = float(sims[idx["agent"]][idx["anti_agent"]])
        agent_obs_sim = float(sims[idx["agent"]][idx["observer"]])
        anti_obs_sim = float(sims[idx["anti_agent"]][idx["observer"]])

        print(f"\n  SIMILARITIES:")
        print(f"    Agent <-> Anti-Agent:   {agent_anti_sim:.3f}")
        print(f"    Agent <-> Observer:     {agent_obs_sim:.3f}")
        print(f"    Anti-Agent <-> Observer: {anti_obs_sim:.3f}")

        results["similarities"] = {
            "agent_anti": agent_anti_sim,
            "agent_observer": agent_obs_sim,
            "anti_observer": anti_obs_sim,
        }

        if agent_obs_sim < anti_obs_sim:
            print(f"    Observer is CLOSER to the Anti-Agent (skeptic won)")
        elif agent_obs_sim > anti_obs_sim:
            print(f"    Observer is CLOSER to the Agent (depth won)")
        if agent_anti_sim > 0.7:
            print(f"    Agent and Anti-Agent CONVERGED (dialectic produced agreement)")
        elif agent_anti_sim < 0.3:
            print(f"    Agent and Anti-Agent fully DIVERGED")

        equidistance = abs(agent_obs_sim - anti_obs_sim)
        results["observer_equidistance"] = float(equidistance)
        if equidistance < 0.1:
            print(f"    Observer is EQUIDISTANT (genuine third perspective)")

    return results


def main():
    print("THE THIRD EYE")
    print(f"Model: {MODEL}")
    print(f"Rounds per seed: {ROUNDS}")
    print(f"Seeds: {len(SEEDS)}")
    print(f"Architecture: Agent (depth) + Anti-Agent (skeptic) + Observer (third eye)\n")

    all_results = {}

    for seed_name, seed_text in SEEDS.items():
        result = run_dialectic(seed_text, seed_name)
        all_results[seed_name] = result
        _save(all_results, "third_eye_partial.json")

    # ─── CROSS-SEED ANALYSIS ────────────────────────────────────────────
    section("CROSS-SEED ANALYSIS")

    print(f"\n  {'Seed':<15} {'Agent<->Anti':<14} {'Agent<->Obs':<14} {'Anti<->Obs':<14} {'Who won?'}")
    print(f"  {'-'*60}")
    for name, result in all_results.items():
        sims = result.get("similarities", {})
        if sims:
            aa = sims.get("agent_anti", 0)
            ao = sims.get("agent_observer", 0)
            an = sims.get("anti_observer", 0)
            winner = "AGENT" if ao > an else "SKEPTIC" if an > ao else "NOVEL"
            print(f"  {name:<15} {aa:<14.3f} {ao:<14.3f} {an:<14.3f} {winner}")

    print(f"\n  Observer equidistance (low = genuinely novel perspective):")
    for name, result in all_results.items():
        eq = result.get("observer_equidistance", 999)
        verdict = "NOVEL" if eq < 0.1 else "LEANS" if eq < 0.2 else "SIDED"
        print(f"    {name:<15} {eq:.3f}  ({verdict})")

    # ─── SAVE ───────────────────────────────────────────────────────────
    _save(all_results, "third_eye_results.json")
    print(f"\n  Results saved to: {os.path.join(DATA_DIR, 'third_eye_results.json')}")


def _save(data, filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    main()
