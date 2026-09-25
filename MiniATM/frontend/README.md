# MiniATM frontend

This directory contains the React/Vite client for MiniATM v2.

## Development

From this directory:

```powershell
npm install
npm run dev
```

Vite listens on port `5173`, binds to `0.0.0.0`, accepts `*.trycloudflare.com`
Quick Tunnel hostnames, and proxies browser requests beginning with `/api` to
FastAPI at `http://127.0.0.1:8000`.

The frontend intentionally uses relative `/api/...` URLs. It does not expose the
local backend address in browser-facing application code.

## Checks

```powershell
npm run lint
npm run build
```
