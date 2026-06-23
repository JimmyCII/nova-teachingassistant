# Nova Voice Console - Deployment Runbook

This runbook contains instructions for testing the Nova Voice Console locally and deploying it to Google Cloud Run.

## 1. Local Testing

Before deploying, always verify the application locally to ensure the Voice API and UI components function properly.

1. **Start the Local Server**
   Ensure your `.env` file is set up with your `GOOGLE_API_KEY`. Start the application using `uvicorn` from the project's root folder:
   ```powershell
   python -m uvicorn web.server:app --reload
   ```

2. **Verify Web UI**
   - Open your browser and navigate to `http://localhost:8000`.
   - You should see the **Nova — your co-teacher** console.
   - Click the **Talk** button and speak into your microphone to verify Nova responds verbally.
   - Click the **Create Homework** button above the composer. It will insert *"Hey Nova, create homework"* into the chat and trigger the generator tool automatically.
   - Click the **Group Activities** button to prompt Nova with *"Hey Nova, create small group activities using the DOK style"* so you can test her DOK curriculum awareness.
   - Click the **Create Quiz** button to prompt Nova with *"Hey Nova, create a weekly quiz"* to test the 10-question generator.

---

## 2. Google Cloud Run Deployment

Cloud Run builds our Docker container and hosts it securely on a public HTTPS URL accessible from mobile browsers.

1. **Authenticate Google Cloud CLI**
   Open PowerShell and log in if you haven't already:
   ```powershell
   gcloud auth login
   ```

2. **Set Active Project**
   Replace `[YOUR_PROJECT_ID]` with your actual Google Cloud Project ID:
   ```powershell
   gcloud config set project [YOUR_PROJECT_ID]
   ```

3. **Enable Required APIs**
   Enable the APIs required to build the Dockerfile, host the service, and manage the API Key:
   ```powershell
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
   ```

4. **Store API Key Securely**
   Because we do not commit our `.env` file, the API key must be stored in Google Secret Manager so Cloud Run can access it securely. Create the secret by running:
   ```powershell
   echo "YOUR_ACTUAL_API_KEY_HERE" | gcloud secrets create GOOGLE_API_KEY --data-file=-
   ```
   *(Be sure to replace `"YOUR_ACTUAL_API_KEY_HERE"` with your actual Gemini API key)*

5. **Run the Deployment**
   Since you are on Windows, the easiest way is to run this single continuous command in your Command Prompt or PowerShell. It will package your code and upload it:
   
   ```cmd
   gcloud run deploy nova-voice-console --source . --region us-central1 --allow-unauthenticated --timeout 3600 --memory 512Mi --min-instances=0 --max-instances=2 --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,CONSOLE_TOKEN=CONSOLE_TOKEN:latest,KARRIE_EMAIL=KARRIE_EMAIL:latest,ADMIN_EMAIL=ADMIN_EMAIL:latest,SENDER_EMAIL=SENDER_EMAIL:latest" --set-env-vars="NOVA_LIVE_MODEL=gemini-3.1-flash-live-preview"
   ```

Once the command completes, Google Cloud will output a **Service URL** (e.g., `https://nova-voice-console-xxxx-uc.a.run.app`). You can open this URL on any web-enabled device to access the live Nova Voice Console!

---

## 3. Redeploying After Updates

Whenever you make changes to your local code, prompts, or tools, you do **not** need to go through the authentication or API setup again. 

To push your latest changes live to the cloud, simply run the exact same deployment command from your terminal:

```cmd
gcloud run deploy nova-voice-console --source . --region us-central1 --allow-unauthenticated --timeout 3600 --memory 512Mi --min-instances=0 --max-instances=2 --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,CONSOLE_TOKEN=CONSOLE_TOKEN:latest,KARRIE_EMAIL=KARRIE_EMAIL:latest,ADMIN_EMAIL=ADMIN_EMAIL:latest,SENDER_EMAIL=SENDER_EMAIL:latest" --set-env-vars="NOVA_LIVE_MODEL=gemini-3.1-flash-live-preview"
```

Cloud Run will automatically build a new version of your container and seamlessly shift all traffic to t