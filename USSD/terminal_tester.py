#!/usr/bin/env python3
"""
Interactive USSD terminal tester for local development.

This script mimics how USSD behaves on a phone:
- Keeps one session_id, service_code, and phone_number
- Sends cumulative `text` segments (e.g. "4*John*mail@example.com")
- Prints backend responses with CON/END states

Usage:
  python USSD/terminal_tester.py
  python USSD/terminal_tester.py --url http://127.0.0.1:8000/ussd/callback/
  python USSD/terminal_tester.py --phone 255758523353 --session s1 --service "*123#"
"""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SessionState:
    url: str
    phone: str
    service_code: str
    session_id: str
    segments: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "*".join(self.segments)


def _random_session_id(prefix: str = "s") -> str:
    tail = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}{tail}"


def _post_callback(state: SessionState) -> str:
    payload = {
        "sessionId": state.session_id,
        "serviceCode": state.service_code,
        "phoneNumber": state.phone,
        "text": state.text,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        state.url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return body.strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return f"HTTP {e.code}: {body}"
    except Exception as e:  # pylint: disable=broad-except
        return f"ERROR: {e}"


def _parse_ussd_response(body: str) -> Tuple[str, str]:
    if body.startswith("CON "):
        return "CON", body[4:]
    if body.startswith("END "):
        return "END", body[4:]
    return "RAW", body


def _print_help() -> None:
    print("\nCommands:")
    print("  :help     Show commands")
    print("  :show     Show current session payload")
    print("  :back     Remove last segment")
    print("  :reset    Clear segments and restart same session")
    print("  :new      New session_id + clear segments")
    print("  :exit     Quit tester")
    print("\nNormal input (e.g. 1, yes, 50000) appends as next USSD segment.\n")


def _print_state(state: SessionState) -> None:
    print("\nCurrent state")
    print(f"  url         : {state.url}")
    print(f"  session_id  : {state.session_id}")
    print(f"  service_code: {state.service_code}")
    print(f"  phone       : {state.phone}")
    print(f"  text        : {state.text!r}")


def run_interactive(state: SessionState) -> int:
    print("\nUSSD terminal tester started.")
    print(f"Callback: {state.url}")
    _print_help()

    # Initial dial-in (empty text)
    print("Dialing...")
    body = _post_callback(state)
    kind, message = _parse_ussd_response(body)
    print(f"\n[{kind}] {message}\n")

    while True:
        try:
            user_input = input("ussd> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0

        if not user_input:
            print("(empty input ignored; type :help for commands)")
            continue

        if user_input == ":help":
            _print_help()
            continue
        if user_input == ":show":
            _print_state(state)
            continue
        if user_input == ":back":
            if state.segments:
                removed = state.segments.pop()
                print(f"Removed segment: {removed!r}")
            else:
                print("No segments to remove.")
            continue
        if user_input == ":reset":
            state.segments = []
            print("Session text reset.")
            body = _post_callback(state)
            kind, message = _parse_ussd_response(body)
            print(f"\n[{kind}] {message}\n")
            continue
        if user_input == ":new":
            state.session_id = _random_session_id()
            state.segments = []
            print(f"Started new session: {state.session_id}")
            body = _post_callback(state)
            kind, message = _parse_ussd_response(body)
            print(f"\n[{kind}] {message}\n")
            continue
        if user_input == ":exit":
            print("Bye.")
            return 0

        # Phone-style behavior: append this choice as next segment.
        state.segments.append(user_input)
        body = _post_callback(state)
        kind, message = _parse_ussd_response(body)
        print(f"\n[{kind}] {message}\n")

        if kind == "END":
            print("Session ended. Type :new for a fresh session, or :reset to dial again.")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive USSD callback tester")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/ussd/callback/",
        help="USSD callback URL",
    )
    parser.add_argument(
        "--phone",
        default="255758523353",
        help="MSISDN / phone number to test with",
    )
    parser.add_argument(
        "--service",
        default="*123#",
        help="USSD service code",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="sessionId (default: random)",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    state = SessionState(
        url=args.url,
        phone=args.phone,
        service_code=args.service,
        session_id=args.session or _random_session_id(),
    )
    return run_interactive(state)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
