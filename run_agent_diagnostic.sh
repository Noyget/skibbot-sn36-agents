#!/bin/bash

set -e

echo "=========================================="
echo "SN36 Agent Performance Diagnostic"
echo "=========================================="
echo ""
echo "Repository: https://github.com/Noyget/skibbot-sn36-agents"
echo "Commit: 782862b"
echo "Tasks to evaluate: 5"
echo "Max steps per task: 12"
echo ""

cd ~/.openclaw/workspace/bittensor-workspace/autoppia-official

# Check environment
echo "Checking environment..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY not set"
    exit 1
fi
echo "✅ OPENAI_API_KEY configured"

# Run the evaluation
echo ""
echo "Starting local validator-like evaluation..."
echo "(This will take 5-10 minutes)"
echo ""

OUTPUT_FILE="/tmp/agent_eval_results.json"

python3 scripts/miner/eval_github.py \
    --github "https://github.com/Noyget/skibbot-sn36-agents/commit/782862b" \
    --tasks 5 \
    --max-steps 12 \
    --uid 98 \
    --output-json "$OUTPUT_FILE" \
    --logging.debug

echo ""
echo "=========================================="
echo "Evaluation Complete"
echo "=========================================="
echo ""

if [ -f "$OUTPUT_FILE" ]; then
    echo "Results saved to: $OUTPUT_FILE"
    echo ""
    echo "Summary:"
    cat "$OUTPUT_FILE" | jq '.summary // .results // .' 2>/dev/null || cat "$OUTPUT_FILE"
else
    echo "⚠️  No JSON output file created"
fi

echo ""
echo "=========================================="
echo "Log Analysis"
echo "=========================================="
echo ""
echo "Check the logs above for:"
echo "  1. Which tasks completed successfully?"
echo "  2. Which tasks failed? (look for 'error', 'timeout', 'hard timeout')"
echo "  3. Did /act endpoint respond correctly?"
echo "  4. Were actions being executed?"
echo "  5. What was the final eval_score for each task?"
