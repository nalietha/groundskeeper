"""Renders the newsletter email to an HTML file so it can be checked in a
browser without sending anything.

    python creator/preview_newsletter.py               # full morning edition
    python creator/preview_newsletter.py --ready       # short 'ready' alert
    python creator/preview_newsletter.py --theme Tea

The network-backed extras (fun fact, word of the day) are stubbed so a preview
works offline and renders the same every time.
"""
import argparse
import os
import sys
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import jinja2  # noqa: E402

from core.newsletter_service import NewsletterService  # noqa: E402
from core.theme_service import ThemeService  # noqa: E402


class _StubJokes:
    def get_joke(self, theme=None):
        return "What do you call a sad cup of coffee? A depresso."


class _StubAffirmations:
    def get_daily_affirmation(self):
        return "You have already done the hardest part of today, which was starting it."


class _StubGames:
    def get_scores(self, game_name=""):
        return [
            {"game": "snake", "name": "NAT", "score": 4120},
            {"game": "snake", "name": "AMY", "score": 3380},
            {"game": "snake", "name": "BOB", "score": 900},
            {"game": "espresso_express", "name": "ZZZ", "score": 275},
            {"game": "espresso_express", "name": "KAT", "score": 190},
        ]


def build_context(theme, ready_mode):
    service = NewsletterService(_StubJokes(), _StubAffirmations(), _StubGames())

    if ready_mode:
        context = {
            "theme_name": theme.name,
            "main_message": f"{theme.name} is now ready! Enjoy your morning cuppa!",
        }
        context.update(service.get_basic_content(theme))
    else:
        context = {
            "theme_name": theme.name,
            "main_message": f"{theme.name} has just been started!",
        }
        # Stub the two network calls so previewing works offline.
        service.get_fun_fact = lambda: "A group of pugs is called a grumble."
        service.get_word_of_the_day = lambda: "Bombastic"
        context.update(service.generate_morning_newsletter(theme))

    context["alias"] = "Nathan"
    context["unsubscribe_url"] = "http://127.0.0.1:5000/unsubscribe?contact=you&theme=" + theme.name
    return context


def main():
    parser = argparse.ArgumentParser(description="Preview the newsletter email.")
    parser.add_argument("--theme", default="Coffee", help="Theme name (default: Coffee)")
    parser.add_argument("--ready", action="store_true", help="Render the short 'ready' alert instead")
    parser.add_argument("--out", default="newsletter_preview.html", help="Output file")
    parser.add_argument("--no-open", action="store_true", help="Don't open a browser")
    args = parser.parse_args()

    themes = ThemeService()
    theme = themes.get_theme(args.theme)
    if theme is None:
        available = ", ".join(t.name for t in themes.get_all_themes()) or "none"
        parser.error(f"Unknown theme '{args.theme}'. Active themes: {available}")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(PROJECT_ROOT / "templates" / "notifications"))
    )
    html = env.get_template("email_alert.html").render(**build_context(theme, args.ready))

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.write_text(html, encoding="utf-8")

    edition = "ready alert" if args.ready else "morning edition"
    print(f"Wrote {theme.name} {edition} to {out_path}")
    if not args.no_open:
        webbrowser.open(out_path.as_uri())


if __name__ == "__main__":
    main()
