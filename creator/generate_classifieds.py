"""Drafts new newsletter filler in the existing voice and appends it for review.

This is a dev-time tool, not a runtime dependency -- it never runs on the Pi.
Generated entries land in assets/lists/classifieds.json for you to read before
committing, which is the whole point: the ads go out to coworkers, so a human
stays between the model and the break room.

    pip install anthropic
    export ANTHROPIC_API_KEY=...          # or: ant auth login

    python creator/generate_classifieds.py --kind ads --count 15
    python creator/generate_classifieds.py --kind classifieds --count 40
    python creator/generate_classifieds.py --kind all --count 20 --dry-run

Existing entries are sent as style reference and as a do-not-repeat list, so
the new material matches the voice without restating jokes already in the file.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CLASSIFIEDS_PATH = PROJECT_ROOT / "assets" / "lists" / "classifieds.json"

MODEL = "claude-opus-5"

STYLE = """You write filler for a parody small-town free newspaper that gets \
emailed to an office break room -- the kind of single-sheet paper found next to \
the till in a diner, packed with ads for tiny local businesses.

The voice is deadpan and understated. The joke is always that someone is taking \
an absurd premise completely seriously, or that a mundane thing is being \
described with unearned gravity. Never wink at the reader, never use exclamation \
marks for emphasis, and never explain the joke. Short is better than long.

Hard rules:
- Every business, person, and review is invented. Never use the name of a real \
company, product, brand, or public figure.
- Reviews are obviously fictional in tone. Attribute them to invented first \
names with an initial, or to a role ("Facilities", "Desk 14", "Withheld").
- Keep it workplace-safe: no politics, religion, sex, alcohol, drugs, illness, \
or anything a colleague could read as aimed at them personally.
- British-leaning spelling, to match the existing entries."""

KINDS = {
    "ads": {
        "field": "advertisements",
        "brief": (
            "Fake advertisements for invented small local businesses. Each has a name in "
            "capitals, a deadpan tagline, an all-caps offer line of the 'MENTION THIS AD' "
            "variety, and a short customer review with a 1-5 star rating. The funniest "
            "reviews faintly undercut the business, and a rating that mismatches its "
            "review is good -- five stars for something alarming, two stars for a glowing "
            "quote. Vary the trades: repair, food, professional services, and at least a "
            "few businesses that inexplicably combine two unrelated ones."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Business name, in capitals"},
                "tagline": {"type": "string", "description": "One deadpan sentence, occasionally two"},
                "offer": {"type": "string", "description": "All-caps offer line"},
                "review": {
                    "type": "object",
                    "properties": {
                        "quote": {"type": "string", "description": "One sentence, no quote marks"},
                        "author": {"type": "string", "description": "Invented name or role"},
                        "stars": {"type": "integer", "description": "1 to 5"},
                    },
                    "required": ["quote", "author", "stars"],
                    "additionalProperties": False,
                },
            },
            "required": ["name", "tagline", "offer", "review"],
            "additionalProperties": False,
        },
    },
    "classifieds": {
        "field": "classifieds",
        "brief": (
            "One-line small ads from the office. Each opens with a category in capitals "
            "-- FOR SALE, LOST, FOUND, WANTED, FREE, NOTICE, SEEKING -- then one deadpan "
            "sentence, occasionally two. These are the smallest jokes in the paper: a "
            "quiet observation about shared office life, never a setup and punchline."
        ),
        "schema": {"type": "string"},
    },
    "quotes": {
        "field": "quotes",
        "brief": (
            "Inspirational quotes of the kind printed in a corner box, except each is a "
            "real proverb or famous line derailed halfway through by something mundane "
            "and office-related. Attribution is always unreliable and part of the joke "
            "-- 'Attributed, Probably Wrongly', 'Contested', 'Philosopher, Diminished'. "
            "Never attribute to a real named person."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The quote itself"},
                "author": {"type": "string", "description": "Unreliable attribution, never a real person"},
            },
            "required": ["text", "author"],
            "additionalProperties": False,
        },
    },
    "forecasts": {
        "field": "forecasts",
        "brief": (
            "Weather forecasts for the inside of an office building, written in the flat "
            "register of a real regional forecast but describing morale, meetings, the "
            "temperature disputes, and the state of the break room. One or two sentences."
        ),
        "schema": {"type": "string"},
    },
}


def entry_key(item):
    """Identifies an entry for dedup. Matches core/deck.py's keying."""
    if isinstance(item, dict):
        return (item.get("name") or item.get("text") or "").strip().lower()
    return str(item).strip().lower()


def build_prompt(kind, count, existing):
    spec = KINDS[kind]
    sample = existing[-40:] if len(existing) > 40 else existing
    existing_names = sorted(filter(None, (entry_key(e) for e in existing)))

    return (
        f"Write {count} new entries for the '{kind}' section.\n\n"
        f"{spec['brief']}\n\n"
        "Here are existing entries, as a style reference. Match their register and "
        "length; do not reuse their premises:\n"
        f"{json.dumps(sample, indent=2, ensure_ascii=False)}\n\n"
        "Every one of these premises is already taken -- avoid all of them, and avoid "
        "near-misses of them too:\n"
        f"{json.dumps(existing_names, ensure_ascii=False)}\n\n"
        f"Return exactly {count} entries, each distinct from the others."
    )


def generate(client, kind, count, existing):
    spec = KINDS[kind]
    schema = {
        "type": "object",
        "properties": {
            "entries": {"type": "array", "items": spec["schema"]},
        },
        "required": ["entries"],
        "additionalProperties": False,
    }

    # Streaming because the batch plus thinking can run long, and a non-streaming
    # request at this max_tokens risks an HTTP timeout.
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=STYLE,
        messages=[{"role": "user", "content": build_prompt(kind, count, existing)}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
        # Safety classifiers can decline; this re-runs the request on Anthropic's
        # recommended fallback model server-side instead of returning nothing.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        detail = getattr(response.stop_details, "explanation", None) or "no explanation given"
        raise RuntimeError(f"Request was declined ({detail}). Try rewording the brief.")

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise RuntimeError(f"No text in response (stop_reason={response.stop_reason}).")

    return json.loads(text)["entries"], response.usage


def merge(existing, new_entries):
    """Appends only entries whose key isn't already present."""
    seen = {entry_key(e) for e in existing}
    added, skipped = [], 0
    for entry in new_entries:
        key = entry_key(entry)
        if not key or key in seen:
            skipped += 1
            continue
        seen.add(key)
        added.append(entry)
    return added, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--kind", default="ads", choices=list(KINDS) + ["all"])
    parser.add_argument("--count", type=int, default=15, help="Entries to request per kind")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    try:
        import anthropic
    except ImportError:
        parser.error("The anthropic SDK is not installed. Run: pip install anthropic")

    if not os.getenv("ANTHROPIC_API_KEY"):
        # Not fatal: the SDK also resolves an `ant auth login` profile.
        print("Note: ANTHROPIC_API_KEY is unset; relying on a stored credential profile.")

    client = anthropic.Anthropic()

    with open(CLASSIFIEDS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    kinds = list(KINDS) if args.kind == "all" else [args.kind]
    total_added = 0

    for kind in kinds:
        field = KINDS[kind]["field"]
        existing = data.get(field, [])
        print(f"\nGenerating {args.count} '{kind}' entries (pool is {len(existing)})...")

        try:
            entries, usage = generate(client, kind, args.count, existing)
        except Exception as e:
            print(f"  Failed: {e}")
            continue

        added, skipped = merge(existing, entries)
        print(f"  {len(added)} new, {skipped} duplicate/blank "
              f"({usage.input_tokens} in / {usage.output_tokens} out)")

        for entry in added:
            preview = entry.get("name") or entry.get("text") if isinstance(entry, dict) else entry
            print(f"    - {preview}")

        if not args.dry_run:
            data[field] = existing + added
            total_added += len(added)

    if args.dry_run:
        print("\nDry run -- nothing written.")
        return

    if total_added:
        with open(CLASSIFIEDS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nAdded {total_added} entries to {CLASSIFIEDS_PATH.relative_to(PROJECT_ROOT)}.")
        print("Read the diff before committing -- these go out to real coworkers.")
    else:
        print("\nNothing new to add.")


if __name__ == "__main__":
    main()
