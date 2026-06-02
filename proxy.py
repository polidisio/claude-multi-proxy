#!/usr/bin/env python3
"""
Multi-Provider Proxy for Claude Code
Routes model requests to MiniMax or DeepSeek based on model name.
Fixes DeepSeek thinking mode by ensuring assistant messages have thinking blocks.
"""

import http.client
import http.server
import json
import logging
from urllib.parse import urlparse
import os

# Configuration
MAX_REQUEST_BYTES = 10 * 1024 * 1024  # 10MB
PROXY_TIMEOUT_SECONDS = 60
SERVER_PORT = int(os.environ.get("PROXY_PORT", 8090))

MINIMAX_TOKEN = os.environ.get("MINIMAX_TOKEN", "")
MINIMAX_BASE_URL = "https://api.minimax.io/anthropic/v1"

DEEPSEEK_TOKEN = os.environ.get("DEEPSEEK_TOKEN", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic/v1"

SERVER_PORT = 8090

MODEL_ROUTES = {
    "minimax-m3": {"provider": "minimax", "model": "MiniMax-M3"},
    "minimax-m2.7": {"provider": "minimax", "model": "MiniMax-M2.7"},
    "minimax-m2.5": {"provider": "minimax", "model": "MiniMax-M2.5"},
    "minimax-m2": {"provider": "minimax", "model": "MiniMax-M2"},
    "deepseek-v4-pro": {"provider": "deepseek", "model": "deepseek-chat"},
    "deepseek-v4-flash": {"provider": "deepseek", "model": "deepseek-chat"},
    "deepseek-chat": {"provider": "deepseek", "model": "deepseek-chat"},
    "deepseek-reasoner": {"provider": "deepseek", "model": "deepseek-chat"},
}

DEFAULT_PROVIDER = "deepseek"


def ensure_thinking_in_assistant_messages(messages):
    """
    Claude Code strips thinking blocks from assistant messages.
    DeepSeek requires them in thinking mode.
    Add empty thinking block to assistant messages that don't have one.
    """
    fixed = []
    for msg in messages:
        if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
            msg = dict(msg)
            has_thinking = any(
                isinstance(b, dict) and b.get("type") == "thinking"
                for b in msg["content"]
            )
            if not has_thinking:
                # Prepend empty thinking block
                msg["content"] = [{"type": "thinking", "thinking": ""}] + msg["content"]
        fixed.append(msg)
    return fixed


def strip_thinking_from_user_messages(messages):
    """DeepSeek rejects thinking blocks in user messages."""
    cleaned = []
    for msg in messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            msg = dict(msg)
            msg["content"] = [
                block for block in msg["content"]
                if not (isinstance(block, dict) and block.get("type") == "thinking")
            ]
            if not msg["content"]:
                msg["content"] = [{"type": "text", "text": "."}]
        cleaned.append(msg)
    return cleaned


def convert_system_messages(messages):
    """DeepSeek doesn't support system role - convert to user message."""
    system_content = []
    cleaned = []
    
    for msg in messages:
        if msg.get("role") == "system":
            # Collect system messages
            if isinstance(msg.get("content"), str):
                system_content.append(msg["content"])
            elif isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        system_content.append(block.get("text", ""))
        else:
            cleaned.append(msg)
    
    # Prepend system content as user message if any
    if system_content:
        system_text = "\n\n".join(system_content)
        if cleaned and cleaned[0].get("role") == "user":
            # Merge into first user message
            first = dict(cleaned[0])
            if isinstance(first["content"], str):
                first["content"] = f"[System context]\n{system_text}\n\n[User request]\n{first['content']}"
            cleaned[0] = first
        else:
            cleaned.insert(0, {"role": "user", "content": f"[System context]\n{system_text}"})
    
    return cleaned


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logging.info("%s - %s", self.address_string(), format % args)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            self.send_error_response(400, "Missing Content-Length")
            return
        if content_length > MAX_REQUEST_BYTES:
            self.send_error_response(413, f"Request too large (max {MAX_REQUEST_BYTES} bytes)")
            return
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            request_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
            return

        if not isinstance(request_data, dict):
            self.send_error_response(400, "Request body must be a JSON object")
            return
        if not isinstance(request_data.get("messages"), list):
            self.send_error_response(400, "Field 'messages' must be a list")
            return

        model = request_data.get('model', DEFAULT_PROVIDER)
        
        if model in MODEL_ROUTES:
            route = MODEL_ROUTES[model]
            provider = route["provider"]
            target_model = route["model"]
        elif "deepseek" in model.lower():
            provider = "deepseek"
            target_model = "deepseek-chat"
        elif "minimax" in model.lower():
            if "m3" in model.lower():
                target_model = "MiniMax-M3"
            elif "m2.5" in model.lower():
                target_model = "MiniMax-M2.5"
            elif "m2" in model.lower():
                target_model = "MiniMax-M2"
            else:
                target_model = "MiniMax-M3"
            provider = "minimax"
        else:
            provider = "deepseek"
            target_model = "deepseek-chat"

        if provider == "minimax":
            token = MINIMAX_TOKEN
            base_url = MINIMAX_BASE_URL
        else:
            token = DEEPSEEK_TOKEN
            base_url = DEEPSEEK_BASE_URL

        request_data['model'] = target_model

        # Fix system role issues (DeepSeek and MiniMax don't support system role)
        if provider in ("deepseek", "minimax") and "messages" in request_data:
            request_data["messages"] = convert_system_messages(
                request_data["messages"]
            )

        # Fix thinking mode issues for DeepSeek
        if provider == "deepseek" and "messages" in request_data:
            # 1. Add thinking block to assistant messages if missing
            request_data["messages"] = ensure_thinking_in_assistant_messages(
                request_data["messages"]
            )
            # 2. Remove thinking blocks from user messages
            request_data["messages"] = strip_thinking_from_user_messages(
                request_data["messages"]
            )

        self.proxy_request(base_url, token, request_data, provider)

    def proxy_request(self, base_url, token, request_data, provider):
        parsed = urlparse(base_url)
        conn = None
        try:
            conn = http.client.HTTPSConnection(parsed.netloc, timeout=PROXY_TIMEOUT_SECONDS)
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'anthropic-version': '2023-06-01'
            }
            
            body = json.dumps(request_data)
            
            conn.request('POST', f"{parsed.path}/messages", body, headers)
            response = conn.getresponse()
            
            self.send_response(response.status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response_body = response.read().decode('utf-8')
            self.wfile.write(response_body.encode('utf-8'))
            
        except (ConnectionError, TimeoutError, http.client.HTTPException) as e:
            logging.exception("Upstream error from %s", provider)
            self.send_error_response(502, "Upstream provider error")
        except Exception as e:
            logging.exception("Unexpected error in proxy_request")
            self.send_error_response(500, "Internal proxy error")
        finally:
            if conn:
                conn.close()

    def do_GET(self):
        if self.path == '/v1/models':
            models = {
                "data": [
                {"id": "minimax-m3", "display_name": "MiniMax M3", "type": "model"},
                    {"id": "minimax-m2.7", "display_name": "MiniMax M2.7", "type": "model"},
                    {"id": "minimax-m2.5", "display_name": "MiniMax M2.5", "type": "model"},
                    {"id": "deepseek-v4-pro", "display_name": "DeepSeek V4 Pro", "type": "model"},
                    {"id": "deepseek-v4-flash", "display_name": "DeepSeek V4 Flash", "type": "model"},
                    {"id": "deepseek-chat", "display_name": "DeepSeek Chat", "type": "model"},
                    {"id": "deepseek-reasoner", "display_name": "DeepSeek Reasoner", "type": "model"},
                ]
            }
            self.send_json_response(models)
        elif self.path == '/health':
            self.send_json_response({"status": "healthy", "provider": "multi-provider"})
        else:
            self.send_error_response(404, "Not Found")

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error = {"error": {"type": "invalid_request", "message": message}}
        self.wfile.write(json.dumps(error).encode('utf-8'))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)


def run_server(port):
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, ProxyHandler)
    logging.info("Multi-Provider Proxy running on http://127.0.0.1:%s", port)
    logging.info("Available models: %s", ", ".join(sorted(MODEL_ROUTES.keys())))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down")
        httpd.shutdown()


if __name__ == '__main__':
    run_server(SERVER_PORT)