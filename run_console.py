"""Launch the Nova voice console.

    python run_console.py      ->  open http://localhost:8000

Secure by default: binds to localhost only. To reach it from another device (phone/LAN/tunnel),
you MUST set a shared token first, then open the console with ?token=<secret>:
    set CONSOLE_HOST=0.0.0.0
    set CONSOLE_TOKEN=<secret>
Other env: GOOGLE_API_KEY (.env), NOVA_LIVE_MODEL, NOVA_VOICE, CONSOLE_PORT.
"""
import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("CONSOLE_HOST", "127.0.0.1")          # loopback by default
    port = int(os.getenv("CONSOLE_PORT", "8000"))
    token = os.getenv("CONSOLE_TOKEN", "").strip()
    loopback = host in ("127.0.0.1", "localhost", "::1")

    if not loopback and not token:
        raise SystemExit(
            "\n  Refusing to expose Nova on a network without a token.\n"
            "  The /ws socket spends your Gemini API key, so anyone who reaches it could use\n"
            "  your key. Set a shared secret first:\n"
            "      set CONSOLE_TOKEN=<secret>\n"
            "  and open the console at  http://<host>:%d/?token=<secret>\n"
            "  Or keep CONSOLE_HOST=127.0.0.1 (default) for local-only use.\n" % port
        )

    print(f"\n  Nova console: http://localhost:{port}")
    if token:
        # Never print the secret. It rides in the URL fragment (#) + WS subprotocol — not the
        # query string — so it stays out of server access logs and shell history.
        print(f"  Exposed mode: open the console, then append  #token=<your CONSOLE_TOKEN>")
    print()
    uvicorn.run("web.server:app", host=host, port=port, reload=False)
