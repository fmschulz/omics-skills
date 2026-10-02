"""Tracked files must not contain personal email addresses."""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(
    rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"
)
ALLOWED_DOMAINS = {
    "example.org",
    "example.com",
    "example.net",
    "users.noreply.github.com",
}
ALLOWED_ADDRESSES = {"git@github.com"}
AT = "@"  # Fixtures below join their parts so this file holds no real address.


def tracked_files() -> list[Path]:
    """Return the files git tracks in this repository."""
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    return [ROOT / name.decode() for name in filter(None, listing.split(b"\0"))]


def is_allowed(address: str) -> bool:
    """Accept placeholder domains, GitHub noreply addresses and git@github.com."""
    address = address.lower()
    domain = address.rsplit("@", 1)[1]
    return address in ALLOWED_ADDRESSES or any(
        domain == allowed or domain.endswith("." + allowed)
        for allowed in ALLOWED_DOMAINS
    )


@pytest.mark.parametrize(
    ("address", "allowed"),
    [
        ("you" + AT + "example.org", True),
        ("1+someone" + AT + "users.noreply.github.com", True),
        ("git" + AT + "github.com", True),
        ("someone" + AT + "university.edu", False),
        ("someone" + AT + "notexample.org", False),
    ],
)
def test_is_allowed(address: str, allowed: bool) -> None:
    """Only placeholder and noreply addresses pass."""
    assert is_allowed(address) is allowed


def test_tracked_files_hold_no_personal_email_addresses() -> None:
    """Every email-like string in a tracked file uses a placeholder domain.

    Files are scanned as bytes, so a file that is not valid UTF-8 is still checked.
    Failures name the file and line only, so the address never reaches a CI log.
    """
    offenders = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in tracked_files()
        if path.is_file()
        for number, line in enumerate(path.read_bytes().splitlines(), 1)
        if any(not is_allowed(match.decode("ascii")) for match in EMAIL.findall(line))
    ]
    assert not offenders, (
        "email addresses outside placeholder domains at:\n" + "\n".join(offenders)
    )
