# Spiral Homework Generator
Generate Karrie's weekly Spiral Review homework as an editable .xlsx, saved to Nova's Drive.

## Run (local only — no Drive)
    python -m agent.tools.spiral_homework --topic "Equations" --due 2/6 --year 2025-2026 \
      --standards 6.EE.B.7 --review 6.NS.B.3,6.RP.A.2 --track both --no-upload
Output: ./generated/2-6 spiral (regular).xlsx and (accelerated).xlsx

## Drive setup (one-time, to drop into Nova's Drive)
1. In Google Cloud project gen-lang-client-0232400708: enable the Drive API; create an OAuth
   client ID (Desktop); download as ./client_secret.json (gitignored).
2. Set KARRIE_EMAIL=<her email> in .env (to auto-share the root folder).
3. Drop `--no-upload` and run; first run opens a browser consent — approve as
   nova-assistant@example.com. Files land in
   "Nova Teaching Assistant / Homework / <year> / Drafts".

Requires GOOGLE_API_KEY in .env (Gemini). Model via HOMEWORK_MODEL (default gemini-2.0-flash).
