#!/usr/bin/env bash
# Tests guard.yml's regexes against strings that must fail and strings that must pass.
set -u

ATTRIB='co-authored-by:[[:space:]]*claude|generated with \[?claude|🤖 generated|claude\.ai/code|\.claude/(plugins|projects|jobs)/'
EMAIL='[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
EMAIL_OK='noreply|example\.(com|org)|@v[0-9]'
CRED='\b(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|xox[baprs]-[a-zA-Z0-9-]{10,})\b'

fails=0

must_match() {  # pattern, string, label
  if ! printf '%s' "$2" | grep -Eqi "$1"; then
    echo "FAIL: expected to catch: $3"; fails=$((fails+1))
  fi
}
must_not_match() {
  if printf '%s' "$2" | grep -Eqi "$1"; then
    echo "FAIL: false positive on: $3"; fails=$((fails+1))
  fi
}

must_match "$ATTRIB" 'Co-Authored-By: Claude <noreply@anthropic.com>' 'trailer'
must_match "$ATTRIB" '🤖 Generated with [Claude Code](https://claude.ai/code)' 'footer'
must_match "$ATTRIB" 'C:/Users/x/.claude/plugins/cache/foo' 'tool path'
must_not_match "$ATTRIB" 'the model claude judges candidates' 'ordinary prose'

must_match "$CRED" 'ghp_abcdefghijklmnopqrstuvwxyz0123456789' 'github pat'
must_match "$CRED" 'sk-abcdefghijklmnopqrstuvwxyz' 'api key'
must_not_match "$CRED" 'sk-short' 'too-short lookalike'

printf '%s' 'me@personal.dev' | grep -Eio "$EMAIL" | grep -vEi "$EMAIL_OK" >/dev/null \
  || { echo 'FAIL: expected to catch: real email'; fails=$((fails+1)); }
printf '%s' 'uses: actions/checkout@v4' | grep -Eio "$EMAIL" | grep -vEi "$EMAIL_OK" >/dev/null \
  && { echo 'FAIL: false positive on: action pin'; fails=$((fails+1)); }
printf '%s' 'hq-collect@users.noreply.github.com' | grep -Eio "$EMAIL" | grep -vEi "$EMAIL_OK" >/dev/null \
  && { echo 'FAIL: false positive on: github noreply committer'; fails=$((fails+1)); }

if [ "$fails" -eq 0 ]; then echo "all guard pattern tests passed"; else exit 1; fi
