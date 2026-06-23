# Judge Access Safety Spec

**Goal:** Allow Kaggle judges to interact with the live Nova Voice Console while ensuring strict budget caps and isolating the "blast radius" so a leaked URL cannot be abused or result in a high Google Cloud bill.

This spec outlines the exact safety gates implemented and the administrative checklist you must follow prior to the July 6th submission.

---

## 1. Application-Level Safety Gates (Already Implemented)

1. **Token-Gated URL:** The WebSocket connection string hardcodes a 32-byte `CONSOLE_TOKEN`. The UI reads this token from the URL fragment (e.g., `#token=EXAMPLE_TOKEN_xxxx`). If a judge opens the root domain without the token, or if someone finds the domain on a web scanner, they receive a `403 Forbidden` response and cannot access the Gemini Live API.
2. **Turn Limits (Anti-Flooding):** A single active WebSocket session is hard-capped via `MAX_TURNS_PER_SESSION=15`. If the user hits 15 continuous queries, the session is forcibly dropped and a Policy Violation error is thrown.
3. **Admin Alerts:** If the rate limit is hit, the application automatically dispatches an alert email via the `comms_server` MCP to `[ADMIN_EMAIL]`, allowing you to instantly cycle the console token if active abuse is occurring.

---

## 2. Infrastructure-Level Safety Gates (Your Checklist)

To guarantee safety even if the code limits fail, follow this checklist in Google Cloud Platform (GCP) before submitting:

### [ ] Step A: API Key Isolation
Do not use your personal, unbounded Gemini API Key for the submission.
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create a **new** API Key specifically named `Kaggle_Judging_Key`.
3. Re-deploy the Cloud Run service using this new key (see `docs/runbook_deployment.md`).
4. On July 7th (when judging ends), simply click **Delete** on this key. The deployed app will instantly stop working, completely closing the attack vector.

### [ ] Step B: Strict Scaling Limits
We have already updated `docs/runbook_deployment.md` to include scaling caps, but confirm they are active on your deployment:
- `--min-instances=0`: Ensures that if judges are not actively using the app, Cloud Run spins down to zero. You pay nothing for idle time.
- `--max-instances=2`: Caps concurrency. Even if the URL is leaked to Reddit, Cloud Run will absolutely refuse to spin up more than 2 servers at a time, hard-capping the theoretical maximum cost.

### [ ] Step C: Billing Alerts
Set a hard budget cap so you are never surprised.
1. In the GCP Console, search for **Billing**.
2. Go to **Budgets & alerts** and create a new budget.
3. Set the target amount to **$5.00**.
4. Check the box to trigger an email alert to you when it hits 50% ($2.50) and 100% ($5.00).

---

## 3. Submission Wording

When finalizing the Kaggle Writeup and providing the "Project Link", use the following wording to set clear expectations:

> **Live Interactive Demo**
> You can speak with Nova directly via our live voice console. Because this uses the Gemini Live API over WebSocket, we have implemented strict safety limits:
> - The live demo URL is token-gated and strictly limited to 15 conversational turns per session.
> - The deployment is capped and will only be available to the judging panel through the end of the judging period (July 6th), after which the API keys and endpoints will be revoked.
> 
> **Access the Demo Here:** `https://nova-voice-console-[YOUR_PROJECT_ID].a.run.app/#token=[YOUR_CONSOLE_TOKEN]`
