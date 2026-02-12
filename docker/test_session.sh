#!/usr/bin/env bash
# Test published agent session API — multi-turn conversation
set -euo pipefail

API_BASE="http://localhost:62610/api/v1"
AGENT_ID="fa848411-e4ab-4d15-8150-b8ccf044b774"
SESSION_ID="test-session-$(date +%s)"

echo "=== Published Agent Session Test ==="
echo "Agent:   $AGENT_ID"
echo "Session: $SESSION_ID"
echo ""

# Helper: send a message, print the final answer
send() {
  local msg="$1"
  echo ">>> User: $msg"
  answer=$(curl -s -X POST "$API_BASE/published/$AGENT_ID/chat" \
    -H "Content-Type: application/json" \
    -d "{\"request\":\"$msg\",\"session_id\":\"$SESSION_ID\"}" \
    | grep '"event_type": "complete"' \
    | sed 's/^data: //' \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer','(no answer)'))")
  echo "<<< Assistant: $answer"
  echo ""
}

# Round 1: give context
send "My name is Alice and my favorite color is blue. Just confirm you got it."

# Round 2: recall name
send "What is my name?"

# Round 3: recall color
send "What is my favorite color?"

# Round 4: verify via GET session endpoint
echo "=== Verify session in DB ==="
session_data=$(curl -s "$API_BASE/published/$AGENT_ID/sessions/$SESSION_ID")
msg_count=$(echo "$session_data" | python3 -c "import sys,json; d=json.loads(sys.stdin.read(),strict=False); print(len(d['messages']))")
echo "Session $SESSION_ID has $msg_count messages stored"
echo ""

# Show stored messages
echo "=== Stored Messages ==="
echo "$session_data" | python3 -c "
import sys, json
data = json.loads(sys.stdin.read(), strict=False)
for i, m in enumerate(data['messages']):
    role = m['role']
    content = m['content'][:120].replace(chr(10), ' ')
    print(f'  [{i}] {role}: {content}')
"
echo ""
echo "=== Done ==="
