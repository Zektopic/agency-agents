#!/usr/bin/env bash
#
# test-lib.sh — unit tests for scripts/lib.sh

set -euo pipefail
cd "$(dirname "$0")/.."

source scripts/lib.sh

errors=0
fail() { echo "ERROR: $*"; errors=$((errors + 1)); }

# Test runner for slugify
assert_slugify() {
  local input="$1"
  local expected="$2"
  local actual
  actual="$(slugify "$input")"

  if [[ "$actual" != "$expected" ]]; then
    fail "slugify \"$input\" -> expected \"$expected\", got \"$actual\""
  fi
}


# Test runner for generic equality
assert_equals() {
  local expected="$1"
  local actual="$2"
  local msg="$3"
  if [[ "$actual" != "$expected" ]]; then
    fail "$msg: expected \"$expected\", got \"$actual\""
  fi
}

echo "Testing frontmatter helpers..."
TMP_AGENT=$(mktemp)
cat << 'YML' > "$TMP_AGENT"
---
name: Agent Smith
role: matrix
---
Body text
line 2
YML

assert_equals "Agent Smith" "$(get_field name "$TMP_AGENT")" "get_field name"
assert_equals "matrix" "$(get_field role "$TMP_AGENT")" "get_field role"
assert_equals "" "$(get_field missing "$TMP_AGENT")" "get_field missing"

expected_body=$'Body text\nline 2'
assert_equals "$expected_body" "$(get_body "$TMP_AGENT")" "get_body"

assert_equals "agent-smith" "$(agent_slug "$TMP_AGENT")" "agent_slug"

is_agent_file "$TMP_AGENT" || fail "is_agent_file returned false for valid file"

TMP_INVALID=$(mktemp)
echo "not frontmatter" > "$TMP_INVALID"
if is_agent_file "$TMP_INVALID"; then fail "is_agent_file returned true for invalid file"; fi
if is_agent_file "/does/not/exist"; then fail "is_agent_file returned true for missing file"; fi

rm "$TMP_AGENT" "$TMP_INVALID"

echo "Testing set -e-safe primitives..."
x=0
incr x
assert_equals "1" "$x" "incr 0->1"
incr x
assert_equals "2" "$x" "incr 1->2"
unset y
incr y
assert_equals "1" "$y" "incr unset->1"

echo "Testing Terminal capability + ANSI..."
assert_equals "aaa" "$(repeat a 3)" "repeat"
assert_equals "hello" "$(strip_ansi $'\033[31mhello\033[0m')" "strip_ansi"
assert_equals "5" "$(vis_len $'\033[31mhello\033[0m')" "vis_len"

echo "Testing slugify..."
assert_slugify "Frontend Developer" "frontend-developer"
assert_slugify "C++ Developer" "c-developer"
assert_slugify "---Hello---World---" "hello-world"
assert_slugify "" ""
assert_slugify "  spaces  " "spaces"
assert_slugify "A!B@C#D\$E%F^G&H*I(J)K-L_M+N=O" "a-b-c-d-e-f-g-h-i-j-k-l-m-n-o"
assert_slugify "123 Numbers 456" "123-numbers-456"

if [[ $errors -gt 0 ]]; then
  echo "FAILED: $errors test(s) failed."
  exit 1
fi

echo "PASSED: All tests passed."
