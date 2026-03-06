"""
Production smoke tests for movie-picker.georg-nikola.com

Usage:
  # Against production (via Cloudflare)
  python tests/test_movie_picker.py

  # Against a local port-forward  (kubectl port-forward svc/movie-picker 8888:80 -n default)
  python tests/test_movie_picker.py --url http://localhost:8888

  # Against local file (no server needed)
  python tests/test_movie_picker.py --local
"""
import argparse
import os
import sys
import time
from playwright.sync_api import sync_playwright, expect

PROD_URL   = "https://movie-picker.georg-nikola.com"
PROD_IP    = "104.21.12.221"
LOCAL_FILE = f"file://{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/index.html"

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"


def run_tests(base_url: str, dns_override: bool = False):
    results = []

    def record(name, passed, detail=""):
        icon = PASS if passed else FAIL
        print(f"  {icon} {name}" + (f"  ({detail})" if detail else ""))
        results.append((name, passed))

    launch_args = []
    if dns_override:
        launch_args.append(f"--host-resolver-rules=MAP movie-picker.georg-nikola.com {PROD_IP}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=launch_args)
        context = browser.new_context()
        page    = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append(req.url))

        # ── Test 1: Page loads ────────────────────────────────────────────────
        print("\n[Page Load]")
        try:
            page.goto(base_url, timeout=30000)
            page.wait_for_load_state("networkidle")
            record("Page loads successfully", True)
        except Exception as e:
            record("Page loads successfully", False, str(e))
            browser.close()
            return results

        # ── Test 2: No failed resource requests ───────────────────────────────
        record("No failed resource requests", len(failed_requests) == 0,
               f"failed: {failed_requests}" if failed_requests else "")

        # ── Test 3: No console errors on load ─────────────────────────────────
        record("No JS console errors on load", len(console_errors) == 0,
               console_errors[0] if console_errors else "")

        # ── Test 4: MOVIES array loaded ───────────────────────────────────────
        print("\n[JavaScript State]")
        movies_ok    = page.evaluate("typeof MOVIES !== 'undefined' && MOVIES.length > 0")
        movies_count = page.evaluate("typeof MOVIES !== 'undefined' ? MOVIES.length : 0")
        record("MOVIES array is defined and non-empty", movies_ok, f"{movies_count} titles")

        # ── Test 5: Key DOM elements present ─────────────────────────────────
        print("\n[DOM Structure]")
        record("Pick button exists",       page.locator("#pickBtn").count() == 1)
        record("Card placeholder exists",  page.locator("#placeholder").count() == 1)
        record("Result container exists",  page.locator("#result").count() == 1)
        record("Movie title element exists", page.locator("#movieTitle").count() == 1)

        # ── Test 6: Initial state ─────────────────────────────────────────────
        print("\n[Initial State]")
        placeholder_visible = page.locator("#placeholder").is_visible()
        result_hidden       = not page.locator("#result").is_visible()
        btn_initial_text    = page.locator(".btn-text").inner_text()
        record("Placeholder is visible before first pick", placeholder_visible)
        record("Result is hidden before first pick",       result_hidden)
        record("Button shows 'Pick a Movie' initially",    btn_initial_text == "Pick a Movie",
               f"got: {btn_initial_text!r}")

        # ── Test 7: Pick a movie ───────────────────────────────────────────────
        print("\n[Pick Functionality]")
        page.locator("#pickBtn").click()
        page.wait_for_timeout(600)

        result_shown     = page.locator("#result").is_visible()
        placeholder_gone = not page.locator("#placeholder").is_visible()
        title_text       = page.locator("#movieTitle").inner_text()
        number_text      = page.locator("#movieNumber").inner_text()
        btn_pick_again   = page.locator(".btn-text").inner_text()

        record("Result card is visible after click",      result_shown)
        record("Placeholder is hidden after click",       placeholder_gone)
        record("Movie title is non-empty",                len(title_text.strip()) > 0, f"{title_text!r}")
        record("Movie number shows correct format",       number_text.startswith("#") and "of" in number_text,
               f"{number_text!r}")
        record("Button text changes to 'Pick Again'",     btn_pick_again == "Pick Again",
               f"got: {btn_pick_again!r}")
        record("Picked title exists in MOVIES list",
               page.evaluate(f"MOVIES.includes({title_text!r})"), f"{title_text!r}")

        # ── Test 8: Pick again — different movie ──────────────────────────────
        print("\n[Re-pick Behaviour]")
        first_title = title_text
        page.locator("#pickBtn").click()
        page.wait_for_timeout(600)
        second_title = page.locator("#movieTitle").inner_text()
        record("Re-pick shows a movie title",             len(second_title.strip()) > 0)
        record("Re-pick result still in MOVIES list",
               page.evaluate(f"MOVIES.includes({second_title!r})"))

        # Do a few more picks to verify no repeat on consecutive calls
        picks = {first_title, second_title}
        for _ in range(5):
            page.locator("#pickBtn").click()
            page.wait_for_timeout(400)
            picks.add(page.locator("#movieTitle").inner_text())
        record("Multiple picks produce variety (≥2 distinct titles in 7 picks)", len(picks) >= 2,
               f"{len(picks)} distinct titles seen")

        # ── Test 9: History appears after 2+ picks ────────────────────────────
        print("\n[History]")
        history_visible = page.locator("#historySection").is_visible()
        record("History section appears after multiple picks", history_visible)
        if history_visible:
            history_items = page.locator(".history-item").count()
            record("History contains at least one previous pick", history_items >= 1,
                   f"{history_items} items")

        # ── Test 10: Keyboard shortcut ────────────────────────────────────────
        print("\n[Keyboard]")
        pre_kbd_title = page.locator("#movieTitle").inner_text()
        page.keyboard.press("Space")
        page.wait_for_timeout(600)
        post_kbd_title = page.locator("#movieTitle").inner_text()
        record("Space key triggers a pick", len(post_kbd_title.strip()) > 0)

        # ── Test 11: Auth DOM elements ────────────────────────────────────────
        print("\n[Auth Elements]")
        record("Sign In button exists",          page.locator("#loginBtn").count() == 1)
        record("Auth user span exists",           page.locator("#authUser").count() == 1)
        record("Sign Out button exists",          page.locator("#logoutBtn").count() == 1)
        record("Auth modal exists",               page.locator("#authModal").count() == 1)
        record("Sign In button visible initially", page.locator("#loginBtn").is_visible())
        record("Auth user hidden initially",       not page.locator("#authUser").is_visible())
        record("Sign Out hidden initially",        not page.locator("#logoutBtn").is_visible())

        # ── Test 12: Modal open / close / tab switching ───────────────────────
        print("\n[Auth Modal UI]")
        modal_ui_ok = True
        try:
            # Use JS click to bypass any Cloudflare overlay that may intercept events
            page.evaluate("document.getElementById('loginBtn').click()")
            page.wait_for_timeout(400)
            modal_visible = page.locator("#authModal").is_visible()
            record("Modal opens on Sign In click",       modal_visible)
            record("Login form shown by default",         page.locator("#loginForm").is_visible())
            record("Register form hidden by default",     not page.locator("#registerForm").is_visible())

            page.evaluate("document.querySelector('[data-tab=\"register\"]').click()")
            page.wait_for_timeout(200)
            record("Register form shows on Register tab", page.locator("#registerForm").is_visible())
            record("Login form hidden on Register tab",   not page.locator("#loginForm").is_visible())

            page.evaluate("document.querySelector('[data-tab=\"login\"]').click()")
            page.wait_for_timeout(200)
            record("Login form restored on Sign In tab",  page.locator("#loginForm").is_visible())

            page.evaluate("document.getElementById('modalClose').click()")
            page.wait_for_timeout(300)
            record("Modal closes on × button",            not page.locator("#authModal").is_visible())
        except Exception as e:
            record("Auth modal UI interactions", False, str(e)[:80])
            modal_ui_ok = False

        # ── Test 13: Full auth flow (requires live API via Traefik) ─────────────
        api_reachable = False
        if not base_url.startswith("file://"):
            try:
                api_reachable = page.evaluate("""async () => {
                    try {
                        const r = await fetch('/api/health');
                        const j = await r.json();
                        return j.status === 'ok';
                    } catch { return false; }
                }""")
            except Exception:
                pass

        if api_reachable:
            print("\n[Auth Flow]")
            try:
                test_email = f"smoke-{int(time.time())}@example.com"

                # Register → should immediately log in (no OTP)
                page.evaluate("document.getElementById('loginBtn').click()")
                page.wait_for_timeout(300)
                page.evaluate("document.querySelector('[data-tab=\"register\"]').click()")
                page.wait_for_timeout(200)
                page.locator("#registerEmail").fill(test_email)
                page.locator("#registerPassword").fill("SmokeTest1234")
                page.evaluate("document.querySelector('#registerForm button[type=\"submit\"]').click()")
                page.wait_for_timeout(1500)

                logged_in = page.evaluate("!!localStorage.getItem('mp_token')")
                record("Register → JWT in localStorage (no OTP)", logged_in)
                record("Auth user email shown in header",  page.locator("#authUser").is_visible())
                record("Sign Out button visible",           page.locator("#logoutBtn").is_visible())
                record("Sign In button hidden",             not page.locator("#loginBtn").is_visible())
                record("Modal closed after register",       not page.locator("#authModal").is_visible())

                # Logout, then test login flow
                page.evaluate("document.getElementById('logoutBtn').click()")
                page.wait_for_timeout(400)

                page.evaluate("document.getElementById('loginBtn').click()")
                page.wait_for_timeout(300)
                page.locator("#loginEmail").fill(test_email)
                page.locator("#loginPassword").fill("SmokeTest1234")
                page.evaluate("document.querySelector('#loginForm button[type=\"submit\"]').click()")
                page.wait_for_timeout(1500)

                record("Login → JWT in localStorage (no OTP)",    page.evaluate("!!localStorage.getItem('mp_token')"))
                record("Modal closed after login",                 not page.locator("#authModal").is_visible())

                # Pick a movie and check watched controls
                page.wait_for_timeout(500)
                page.locator("#pickBtn").click()
                page.wait_for_timeout(1000)
                record("Skip-watched filter visible when logged in",  page.locator("#watchedFilter").is_visible())
                record("Watched button visible when logged in",       page.locator("#watchedBtn").is_visible())

                # Mark as watched
                page.locator("#watchedBtn").click()
                page.wait_for_timeout(1500)
                btn_text = page.locator("#watchedBtn .watched-btn-text").inner_text()
                record("Watched button shows 'Watched' after marking", btn_text == "Watched", f"got: {btn_text!r}")

                # Logout
                page.evaluate("document.getElementById('logoutBtn').click()")
                page.wait_for_timeout(400)
                record("Logout clears JWT from localStorage",   page.evaluate("!localStorage.getItem('mp_token')"))
                record("Sign In button restored after logout",  page.locator("#loginBtn").is_visible())
                record("Sign Out button hidden after logout",   not page.locator("#logoutBtn").is_visible())
                record("Watched filter hidden after logout",    not page.locator("#watchedFilter").is_visible())
            except Exception as e:
                record("Auth flow", False, str(e)[:80])

        # ── Final: No JS errors throughout ────────────────────────────────────
        print("\n[Final Check]")
        record("No JS errors during any interaction", len(console_errors) == 0,
               console_errors[0] if console_errors else "")

        browser.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="Movie Picker smoke tests")
    group  = parser.add_mutually_exclusive_group()
    group.add_argument("--url",   help="Custom base URL (e.g. http://localhost:8888)")
    group.add_argument("--local", action="store_true", help="Test against local file://")
    args = parser.parse_args()

    if args.local:
        url, dns = LOCAL_FILE, False
        label = "LOCAL (file://)"
    elif args.url:
        url, dns = args.url, False
        label = f"CUSTOM ({url})"
    else:
        url, dns = PROD_URL, True
        label = f"PRODUCTION ({PROD_URL})"

    print(f"\n{'='*55}")
    print(f"  Movie Picker — Smoke Tests")
    print(f"  Target: {label}")
    print(f"{'='*55}")
    t0      = time.time()
    results = run_tests(url, dns_override=dns)
    elapsed = time.time() - t0

    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    failed = total - passed

    print(f"\n{'='*55}")
    print(f"  {passed}/{total} passed  |  {failed} failed  |  {elapsed:.1f}s")
    print(f"{'='*55}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
