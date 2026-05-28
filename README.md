# Claude Multi-Provider Proxy

A simple proxy that routes Claude Code traffic between MiniMax and DeepSeek based on model name.

## Features

- Routes `minimax-m2.7`, `minimax-m2.5` → MiniMax API
- Routes `deepseek-v4-pro`, `deepseek-v4-flash`, `deepseek-chat`, `deepseek-reasoner` → DeepSeek API
- Fixes DeepSeek thinking mode (injects empty thinking blocks in assistant messages)
- Converts system messages to user messages (both providers don't support system role)
- Removes thinking blocks from user messages

## Quick Start

### 1. Start the proxy

```bash
python3 proxy.py
```

The proxy listens on `0.0.0.0:8090` by default.

### 2. Configure Claude Code

Create `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "proxy-local",
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8090",
    "ANTHROPIC_MODEL": "minimax-m2.7",
    "ANTHROPIC_SMALL_FAST_MODEL": "minimax-m2.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "minimax-m2.7"
  },
  "model": "sonnet"
}
```

### 3. Set API tokens

```bash
export MINIMAX_TOKEN="your-minimax-token"
export DEEPSEEK_TOKEN="your-deepseek-token"
```

Or edit the tokens directly in `proxy.py` (not recommended for sharing).

## Available Models

| Model | Provider |
|-------|----------|
| minimax-m2.7 | MiniMax |
| minimax-m2.5 | MiniMax |
| deepseek-v4-pro | DeepSeek |
| deepseek-v4-flash | DeepSeek |
| deepseek-chat | DeepSeek |
| deepseek-reasoner | DeepSeek |

## Claude Code Commands

```
/model minimax-m2.7   # Use MiniMax
/model deepseek-v4-pro  # Use DeepSeek V4 Pro
```

## Troubleshooting

### "invalid message role: system"
- The proxy converts system messages to user messages automatically.

### "thinking blocks must be passed back"
- The proxy injects empty thinking blocks in assistant messages for DeepSeek.

### Proxy not responding
- Check the proxy is running: `curl http://127.0.0.1:8090/health`
- Check port 8090 is not blocked by firewall

## Remote Setup

For using on a remote Mac, point to the proxy on your local machine:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "proxy-local",
    "ANTHROPIC_BASE_URL": "http://YOUR_LOCAL_IP:8090",
    "ANTHROPIC_MODEL": "minimax-m2.7",
    "ANTHROPIC_SMALL_FAST_MODEL": "minimax-m2.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "minimax-m2.7"
  },
  "model": "sonnet"
}
```
