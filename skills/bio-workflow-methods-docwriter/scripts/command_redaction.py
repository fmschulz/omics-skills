"""Redact credentials from a shell command before it enters a manifest.

The three extractors import `redact_command`. Python puts the script's own
directory on `sys.path`, so `uv run --script` finds this module beside them.
"""

import re

REDACTED = "$REDACTED"

# One complete shell word: single-quoted, double-quoted (backslash escapes
# honored) and backslash-escaped pieces, and plain characters, in any mix. A
# quote with no closing partner is not part of the word, so the closing quote
# of an enclosing string stays. An unquoted shell separator ends the word.
_WORD = r"""(?:'[^']*'|"(?:[^"\\]|\\.)*"|\\.|[^\s'"\\;&|<>()])+"""

# A flag name is secret when a whole `-` or `_` separated part is a secret
# word, so `--auth-token` matches and `--tokenizer` does not.
_FLAG_NAME_PATTERN = (
    r"--?(?:[a-z0-9]+[-_])*"
    r"(?:password|passwd|secret|token|apikey|credentials?|api[-_]key|access[-_]key)"
    r"(?:[-_][a-z0-9]+)*(?![\w-])"
)

# `--password hunter2`, `--api-key=abc`. A flag followed by another flag has
# no value, so the space form refuses a value that starts with a dash. A
# backslash-newline may sit between the flag and its value.
_SECRET_FLAG_RE = re.compile(
    rf"(?i)(?<![\w-])({_FLAG_NAME_PATTERN})(=|\s*\\\n\s*(?!-)|\s+(?!-))({_WORD})"
)
# `API_KEY=abc`, `export DB_PASSWORD="abc"`. A name that follows a dash is a
# flag, so `--key=2` stays untouched.
_ENV_ASSIGNMENT_RE = re.compile(
    rf"(?i)(?<![\w-])([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|_PAT)[A-Z0-9_]*)=({_WORD})"
)
# `https://user:pw@host/f`: keep the user name and the host.
_URL_PASSWORD_RE = re.compile(
    r"(?<![a-z0-9+.-])([a-z][a-z0-9+.-]*://[^\s/:@'\"]+:)[^\s/@'\"]+(@)", re.IGNORECASE
)
# `Authorization: Bearer abc`: the value stops at a quote so a quoted header
# keeps its closing quote.
_AUTH_HEADER_RE = re.compile(r"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s'\"]+")


def redact_command(command: str) -> str:
    """Replace the secret values in ``command`` with ``$REDACTED``.

    Covers, each as one complete shell word (quoted and escaped parts
    included):

    - the value of a flag when a whole ``-`` or ``_`` separated part of its
      name is password, passwd, secret, token, apikey, credential or
      credentials, or the two parts api and key, or access and key (so
      ``--auth-token`` and ``--api_key`` match, ``--tokenizer`` and
      ``--keyfile`` do not);
    - the value of an environment-style assignment whose name holds KEY, TOKEN,
      SECRET, PASSWORD, CREDENTIAL or _PAT anywhere;
    - the password part of URL userinfo;
    - the value of a Bearer or Basic authorization header.

    It does not look at anything else.
    """
    command = _URL_PASSWORD_RE.sub(rf"\1{REDACTED}\2", command)
    command = _AUTH_HEADER_RE.sub(rf"\1{REDACTED}", command)
    command = _SECRET_FLAG_RE.sub(rf"\1\2{REDACTED}", command)
    return _ENV_ASSIGNMENT_RE.sub(rf"\1={REDACTED}", command)
