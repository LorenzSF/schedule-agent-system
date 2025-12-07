# Google Calendar API Setup Guide

## Step-by-Step Instructions

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click "Select a project" → "New Project"
4. Name: `schedule-agent-system`
5. Click "Create"

### 2. Enable Google Calendar API

1. In the sidebar, go to **"APIs & Services" → "Library"**
2. Search for "Google Calendar API"
3. Click on it
4. Click **"Enable"**

### 3. Create OAuth Credentials

1. Go to **"APIs & Services" → "Credentials"**
2. Click **"Configure Consent Screen"**
   - User Type: **External**
   - App name: `Schedule Agent System`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
3. **Scopes**: Click "Add or Remove Scopes"
   - Search for "Google Calendar API"
   - Select `.../auth/calendar`
   - Click "Update" → "Save and Continue"
4. **Test users**: Add your email address
   - Click "Save and Continue"

5. Go back to **"Credentials"**
6. Click **"+ Create Credentials" → "OAuth client ID"**
7. Application type: **Desktop app**
8. Name: `Schedule Agent Desktop Client`
9. Click **"Create"**
10. **Download JSON** - Save as `credentials.json`

### 4. Place Credentials File

Move the downloaded file to your project:
```
schedule_agent_system/
└── config/
    └── credentials.json  ← Place here
```

### 5. First Run Authentication

When you run the application for the first time:

1. A browser window will open
2. You'll see "Google hasn't verified this app"
   - Click **"Advanced"**
   - Click **"Go to Schedule Agent System (unsafe)"**
   - This is normal for development apps!
3. Click **"Allow"** to grant calendar access
4. Browser will show "Authentication completed"
5. A `token.json` file will be created automatically

### 6. Troubleshooting

**"Access blocked" error**:
- Make sure you added your email as a test user in Step 3.4

**"Redirect URI mismatch"**:
- Ensure you selected "Desktop app" in Step 3.7

**Token expired**:
- Delete `config/token.json` and run again to re-authenticate
```

---

## 🔄 CHANGE 7: Final Project Structure

After all changes, your structure should look like:
```
schedule_agent_system/
├── .gitignore                   ← NEW
├── README.md                    ← UPDATED
├── requirements.txt
├── main.py
├── create_my_schedule.py
├── modify_my_schedule.py
├── test_my_schedule.py
├── test_screenshot_import.py    ← NEW
├── agents/
│   ├── __init__.py
│   ├── parser_agent.py
│   ├── calendar_agent.py
│   ├── change_manager_agent.py
│   ├── conflict_detector_agent.py
│   └── orchestrator_agent.py
├── utils/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── pdf_extractor.py
│   └── calendar_client.py
├── config/
│   ├── __init__.py
│   ├── config_template.py       ← NEW (template)
│   ├── credentials_template.json ← NEW (template)
│   ├── config.py                ← NOT IN GIT
│   ├── credentials.json         ← NOT IN GIT
│   └── token.json               ← NOT IN GIT
├── docs/                        ← NEW
│   └── SETUP_GOOGLE.md
└── tests/
    └── sample_schedules/
        └── (your test files)