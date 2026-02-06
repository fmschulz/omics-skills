#!/usr/bin/env python3
import os
import re
import sys

REQUIRED_SECTIONS = [
    '## Instructions',
    '## Quick Reference',
    '## Input Requirements',
    '## Output',
    '## Quality Gates',
    '## Examples',
    '## Troubleshooting',
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SKILLS_DIR = os.path.join(REPO_ROOT, 'skills')

errors = []

for name in sorted(os.listdir(SKILLS_DIR)):
    skill_dir = os.path.join(SKILLS_DIR, name)
    if not os.path.isdir(skill_dir):
        continue
    skill_md = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_md):
        errors.append(f'{name}: missing SKILL.md')
        continue
    text = open(skill_md, encoding='utf-8').read()
    if not text.startswith('---'):
        errors.append(f'{name}: missing frontmatter')
        continue
    fm_match = re.search(r'^---\n(.*?)\n---\n', text, re.S)
    fm = fm_match.group(1) if fm_match else ''
    m = re.search(r'^name:\s*(.+)$', fm, re.M)
    fm_name = m.group(1).strip() if m else ''
    if fm_name != name:
        errors.append(f'{name}: frontmatter name mismatch ({fm_name})')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', fm_name):
        errors.append(f'{name}: frontmatter name invalid ({fm_name})')
    if len(fm_name) > 64:
        errors.append(f'{name}: frontmatter name too long ({len(fm_name)})')
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing:
        errors.append(f'{name}: missing sections {missing}')
    if len(text.splitlines()) > 500:
        errors.append(f'{name}: SKILL.md over 500 lines ({len(text.splitlines())})')

if errors:
    print('Skill validation failed:')
    for err in errors:
        print(f'- {err}')
    sys.exit(1)

print('Skill validation passed.')
