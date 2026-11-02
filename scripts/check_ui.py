#!/usr/bin/env python3
"""Browser smoke tests for all Syllanix chapters and user-selectable themes.

Requires: pip install playwright && python -m playwright install chromium
Serve repository root at http://127.0.0.1:8765/ before running.
"""
from __future__ import annotations
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765/"
CHAPTERS = sorted(ROOT.glob("ch-[0-9][0-9]-*.html"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    check(len(CHAPTERS) == 56, "Expected 56 published chapter pages")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            for width, height in [(320, 720), (390, 844), (768, 1024), (1440, 900)]:
                context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
                page = context.new_page()
                page.goto(BASE + "ch-06-loops.html", wait_until="domcontentloaded")
                page.locator("#theme-select").wait_for()
                value = page.locator("#theme-select").input_value()
                check(value == "warm", f"{width}: default must be warm, got {value}")
                page.locator("#theme-select").select_option("light")
                background = page.evaluate("getComputedStyle(document.body).backgroundColor")
                check(background == "rgb(255, 255, 255)", f"{width}: white theme background is {background}")
                page.reload(wait_until="domcontentloaded")
                check(page.locator("#theme-select").input_value() == "light", f"{width}: theme was not saved")
                page.locator("#theme-select").select_option("dark")
                check(page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark", "dark theme not applied")
                page.locator("#theme-select").select_option("warm")
                page.evaluate("localStorage.removeItem('syllanix-theme')")
                docwidth = page.evaluate("document.documentElement.scrollWidth")
                check(docwidth <= width + 3, f"{width}: horizontal overflow {docwidth}")
                for img in page.locator(".figure img").all():
                    check(bool(img.get_attribute("alt")), f"{width}: image missing alt")
                    # Image loading is lazy; scroll to it before checking its bytes.
                    img.scroll_into_view_if_needed()
                    loaded = img.evaluate("""(el) => new Promise((resolve) => {
                        el.loading = 'eager';
                        if (el.complete) { resolve(el.naturalWidth > 0); return; }
                        el.addEventListener('load', () => resolve(true), {once:true});
                        el.addEventListener('error', () => resolve(false), {once:true});
                    })""")
                    check(loaded, f"{width}: image did not load: {img.get_attribute('src')}")
                page.close()
                context.close()

            # Mobile viewport across the whole textbook.
            context = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=1)
            page = context.new_page()
            for chapter in CHAPTERS:
                page.goto(BASE + chapter.name, wait_until="domcontentloaded")
                check(page.locator("h1").count() >= 1, f"{chapter.name}: heading missing")
                check(page.locator("#theme-select").count() == 1, f"{chapter.name}: theme control missing")
                docwidth = page.evaluate("document.documentElement.scrollWidth")
                check(docwidth <= 378, f"{chapter.name}: mobile overflow {docwidth}")
            print(f"PASS: 4 viewport/theme tests and {len(CHAPTERS)} mobile chapters; no browser overflow")
            context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
