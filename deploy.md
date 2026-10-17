# NexusAI Deployment Guide

This guide details instructions for deploying the **NexusAI Central Hub** to cloud hosting platforms (such as Render, Fly.io, or AWS) using Docker and Infrastructure-as-Code (Blueprint).

---

## 1. Cloud Service Overview

* **Unique Service Name:** `nexusai-central-workspace-hub`
* **Default Deployed Domain:** `https://nexusai-central-workspace-hub.onrender.com`
* **Runtime:** Docker (`Dockerfile`)
* **Health Check Path:** `/health`
* **Listening Port:** Dynamically assigned via `$PORT` (defaults to `8000`)
* **Resource Plan:** Free Tier compatible (< 80MB RAM baseline)

---

## 2. Configuration & Environment Variables

Configure the following environment variables in the Render Dashboard under **Environment**:

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `PORT` | Listening port for Uvicorn | `8000` |
| `OPENAI_API_KEY` | OpenAI API key for LLM orchestrator & subagents | `sk-...` |
| `GROQ_API_KEY` | Groq API key (optional alternative LLM provider) | `gsk_...` |
| `DATABASE_URL` | PostgreSQL connection URL (falls back to local SQLite if empty) | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_POSTGRES_URL` | Supabase transaction pooler URL (optional) | `postgresql://user:pass@aws-0-...:6543/postgres` |
| `SUPABASE_JWT_SECRET` | Secret key for verifying external OAuth2 JWT tokens | `your-jwt-secret` |
| `MONGO_URI` | MongoDB Atlas cluster connection URI for Credential Vault | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority` |
| `MONGO_DB_NAME` | MongoDB database name | `nexusai` |
| `ENCRYPTION_KEY` | 32-byte Base64-encoded master key for Fernet AES credential vault | `your-32byte-base64-fernet-key` |
| `DAYTONA_API_KEY` | Daytona API key for Sandboxed Python code execution | `dtn_...` |
| `DAYTONA_SERVER_URL` | Daytona API server endpoint URL (optional) | `https://app.daytona.io/api` |

---

## 3. Deployment Instructions (Render Blueprint)

1. **Fork or Push:** Push this repository to your GitHub account.
2. **Open Render Dashboard:** Navigate to [Render Dashboard](https://dashboard.render.com/).
3. **Create Blueprint:**
   - Click **New +** -> **Blueprint**.
   - Connect your GitHub repository.
   - Render detects `render.yaml` and provisions the `nexusai-central-workspace-hub` web service.
4. **Enter Secrets:**
   - In the Blueprint configuration screen, populate your secret keys (`OPENAI_API_KEY`, `MONGO_URI`, `ENCRYPTION_KEY`, etc.).
5. **Deploy:** Click **Apply**. Render will build the Docker container and start the service.

---

## 4. Manual Docker Deployment

You can also deploy the Docker container to any container platform:

```bash
# Build the production container image
docker build -t nexusai-central-workspace-hub:latest .

# Run container locally or in cloud runtime
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  -e OPENAI_API_KEY="sk-..." \
  -e MONGO_URI="mongodb+srv://..." \
  -e ENCRYPTION_KEY="your-base64-key" \
  --name nexusai-hub \
  nexusai-central-workspace-hub:latest
```

---

## 5. Post-Deployment Verification

Verify that the service is operational by querying the health endpoint:

```bash
curl -i https://nexusai-central-workspace-hub.onrender.com/health
```

Expected JSON response (HTTP 200 OK):
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "connected",
      "type": "SQLite"
    },
    "mongodb": {
      "status": "connected"
    },
    "redis": {
      "status": "not_used",
      "used": false
    }
  },
  "timestamp": "2026-10-18T00:00:00.000000+00:00",
  "version": "2.0.0"
}
```

The response includes the `X-Request-ID` tracing header for end-to-end request tracking in log streams.
