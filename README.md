# Claude Multi-Provider Proxy

A simple proxy that routes Claude Code requests to different LLM providers based on model name.

## Features

- **MiniMax** support (your own API token)
- **DeepSeek** support (your own API token)
- Switch models inside Claude Code using `/model <model-name>`
- No external dependencies (stdlib only)
- Works with Claude Code on Mac/Linux

## Models Available

| Model Name | Provider | Description |
|------------|----------|-------------|
| `minimax-m2.7` | MiniMax | MiniMax M2.7 |
| `minimax-m2.5` | MiniMax | MiniMax M2.5 |
| `deepseek-v4-pro` | DeepSeek | DeepSeek V4 Pro |
| `deepseek-v4-flash` | DeepSeek | DeepSeek V4 Flash |
| `deepseek-chat` | DeepSeek | DeepSeek Chat |
| `deepseek-reasoner` | DeepSeek | DeepSeek Reasoner |

## Setup

### 1. Configure your tokens

Edit `proxy.py` and add your API tokens:

```python
MINIMAX_TOKEN = "your-minimax-token-here"
DEEPSEEK_TOKEN = "your-deepseek-token-here"
```

### 2. Start the proxy

```bash
python3 proxy.py
```

The proxy will start on port 8090 (listening on all interfaces).

### 3. Configure Claude Code

Create or edit `~/.claude/settings.json`:

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

### 4. Use in Claude Code

```bash
claude
```

Inside Claude Code, switch models:

```
/model minimax-m2.7    # Use MiniMax
/model deepseek-v4-pro # Use DeepSeek
/model deepseek-v4-flash
```

## Remote Access

If you want to access the proxy from another machine (e.g., a remote Mac), change the proxy URL:

On the remote machine, set `ANTHROPIC_BASE_URL` to the IP of the machine running the proxy, e.g.:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "proxy-local",
    "ANTHROPIC_BASE_URL": "http://192.168.1.100:8090",
    ...
  }
}
```

## Alternative: Shell Scripts

Instead of changing settings.json, you can use the provided shell scripts:

```bash
./claude-minimax.sh   # Start Claude Code with MiniMax
./claude-deepseek.sh  # Start Claude Code with DeepSeek
```

## Requirements

- Python 3 (stdlib only, no external dependencies)
- Claude Code CLI
- API tokens for MiniMax and/or DeepSeek

## License

MIT