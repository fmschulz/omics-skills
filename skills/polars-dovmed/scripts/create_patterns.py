#!/usr/bin/env python3
"""Create structured literature-query JSON using an OpenAI-compatible API.

This is a lightweight vendored helper mirroring the upstream
`dovmed create-patterns` workflow closely enough for agent use inside this skill.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_env_file(path):
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def default_api_base():
    if os.environ.get("LLM_API_BASE"):
        return os.environ["LLM_API_BASE"]
    if os.environ.get("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1"
    return "https://api.openai.com/v1"


def default_api_key():
    return (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


def default_model(api_base):
    explicit = os.environ.get("LLM_MODEL")
    if explicit:
        return explicit
    if "openrouter.ai" in api_base:
        return "openai/gpt-4.1-mini"
    return "gpt-4.1-mini"


def create_user_prompt(input_text):
    return f"\nUser query: {input_text}\n\n"


def load_prompt(path):
    return Path(path).read_text(encoding="utf-8")


def strip_code_fences(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def call_llm(api_base, api_key, payload):
    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_args():
    skill_dir = Path(__file__).resolve().parents[1]
    load_env_file("~/.config/polars-dovmed/.env")
    parser = argparse.ArgumentParser(
        description="Generate structured JSON query patterns for polars-dovmed searches"
    )
    parser.add_argument("--input-text", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument(
        "--prompt-file",
        default=str(skill_dir / "prompts" / "pattern_groups_query.txt"),
    )
    parser.add_argument("--api-base", default=default_api_base())
    parser.add_argument("--api-key", default=default_api_key())
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=4000)
    parser.add_argument(
        "--save-raw-response",
        help="Optional path to save the raw LLM response text before JSON parsing",
    )
    parser.add_argument(
        "--save-payload",
        help="Optional path to save the exact LLM request payload",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.api_key:
        raise SystemExit(
            "missing LLM API key: set --api-key or one of LLM_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY"
        )

    model = args.model or default_model(args.api_base)
    system_prompt = load_prompt(args.prompt_file)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": create_user_prompt(args.input_text)},
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.save_payload:
        output = Path(args.save_payload)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    try:
        response = call_llm(args.api_base, args.api_key, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"http error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"request failed: {exc.reason}") from exc

    try:
        content = response["choices"][0]["message"]["content"]
    except Exception as exc:
        raise SystemExit(f"unexpected response format: {json.dumps(response)[:1000]}") from exc

    if args.save_raw_response:
        Path(args.save_raw_response).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save_raw_response).write_text(content, encoding="utf-8")

    cleaned = strip_code_fences(content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON response from LLM: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit("invalid response from LLM: expected a JSON object")

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
