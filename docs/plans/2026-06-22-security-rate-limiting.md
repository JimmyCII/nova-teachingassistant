# Implementation Plan & Walkthrough: Security & Rate Limiting

*Note: This document combines the planning and walkthrough of the security and anti-flooding implementation done on 2026-06-22.*

## 1. Plan: Security & Rate Limiting

This plan addresses two core requests: moving hardcoded emails into variables and securing the Nova Voice Console against token-draining attacks if the link gets out.

### Proposed Changes

#### 1.1. Extract Hardcoded Emails
- **[MODIFY] `mcp_servers/comms_server/server.py`**:
  - Pull the hardcoded sender (`[SENDER_EMAIL]`) into an environment variable `SENDER_EMAIL`.
  - Add a new helper function `send_security_alert(admin_email, details)` to dispatch warning emails to the admin.

#### 1.2. Implement Anti-Flooding Rate Limits
- **[MODIFY] `web/server.py`**:
  - Define `ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "[ADMIN_EMAIL]")`.
  - Define `MAX_TURNS_PER_SESSION = int(os.getenv("MAX_TURNS_PER_SESSION", "15"))`.
  - Inside the WebSocket connection (`gemini_to_browser` loop), count how many times Nova completes a turn (answers a question). 
  - If a single connection asks more than 15 questions:
    1. Immediately drop the connection (`1008 Policy Violation`).
    2. Fire off an alert email to `[ADMIN_EMAIL]` warning that a session exceeded the rate limit, allowing the admin to cycle the `CONSOLE_TOKEN` or investigate.

---

## 2. Walkthrough: Security & Anti-Flooding Implementation Complete

The rate-limiting logic and email variable extraction have been successfully implemented to secure the Nova Voice Console against token exhaustion attacks!

### What Changed

#### 2.1. Extracted Emails to Environment Variables
We ensured that all critical emails are fully configurable without modifying the codebase:
- **`KARRIE_EMAIL`**: Already defined and defaults to `test@example.com` if missing. The production `.env` safely overrides this to `[KARRIE_EMAIL]`.
- **`ADMIN_EMAIL`**: A new variable for security alerts, defaulting to `[ADMIN_EMAIL]`.
- **`SENDER_EMAIL`**: The email account sending the messages, defaulting to `[SENDER_EMAIL]`.

#### 2.2. Implemented WebSocket Rate-Limiting
To prevent a leaked console URL from being abused to drain the Gemini API tokens, we added a strict rate limit in **`web/server.py`**:
- **Turn Tracking**: The server now tracks exactly how many times the user asks a question (a "turn") per WebSocket connection.
- **Threshold Limit**: If the session exceeds `MAX_TURNS_PER_SESSION` (defaulting to **15**), the server immediately steps in.

#### 2.3. Automated Admin Security Alerts
When the rate limit threshold is exceeded:
1. The WebSocket connection is **forcefully disconnected** with a Policy Violation code (`1008`).
2. An error message is flashed to the offending browser UI.
3. The server automatically triggers the new **`send_admin_alert_email`** function in the `comms_server`.
4. The admin receives an immediate **🚨 URGENT: Nova Security Alert** email at `[ADMIN_EMAIL]` warning that a session was forcefully closed due to token exhaustion protection.

> **Tip:** If you ever need to cycle the console access, simply change `CONSOLE_TOKEN="mjv..."` in your `.env` file and restart the server! Anyone with the old link will get a `403 Forbidden` error.
