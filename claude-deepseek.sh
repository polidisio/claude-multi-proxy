#!/bin/bash
# Claude Code with DeepSeek
export ANTHROPIC_AUTH_TOKEN="deepseek-local"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8090"
export ANTHROPIC_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
export ANTHROPIC_SMALL_FAST_MODEL="deepseek-v4-pro"
echo "🚀 Starting Claude Code with DeepSeek V4 Pro..."
claude "$@"