#!/bin/bash
# Claude Code with MiniMax
export ANTHROPIC_AUTH_TOKEN="minimax-local"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8090"
export ANTHROPIC_MODEL="minimax-m2.7"
export ANTHROPIC_DEFAULT_OPUS_MODEL="minimax-m2.7"
export ANTHROPIC_DEFAULT_SONNET_MODEL="minimax-m2.7"
export ANTHROPIC_SMALL_FAST_MODEL="minimax-m2.7"
echo "🚀 Starting Claude Code with MiniMax M2.7..."
claude "$@"