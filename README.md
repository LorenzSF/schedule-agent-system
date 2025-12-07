# Schedule Agent System

AI-powered calendar management system with multi-agent architecture. Automatically parse schedules from PDFs/images, detect conflicts, and manage events with natural language.

##  Features

-  **Import Schedules**: Parse PDFs and screenshots automatically
-  **Natural Language Modifications**: "Move meeting to Friday at 2pm"
-  **Intelligent Conflict Detection**: Detect overlaps and tight schedules
-  **AI-Powered Suggestions**: Get smart scheduling advice
-  **User Configurable**: Customize gap times and preferences
-  **Multi-Agent Architecture**: Specialized agents work together

##  Architecture

### Agents

- **Parser Agent**: Extracts schedules from PDFs/images using GPT-4 Vision
- **Calendar Agent**: Manages Google Calendar API operations
- **Change Manager Agent**: Handles natural language event modifications
- **Conflict Detector Agent**: Identifies scheduling conflicts
- **Orchestrator Agent**: Coordinates all agents for complex workflows

### Technology Stack

- Python 3.12 (If you use a new version, you may experience compatibility issues with other settings)
- Azure OpenAI (GPT-4o)
- Google Calendar API
- GPT-4 Vision for OCR (no Tesseract needed!)

##  Quick Start

### Prerequisites

- Python 3.12 (If you use a new version, you may experience compatibility issues with other settings)
- Google account
- Azure OpenAI API access (or OpenAI API key)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/schedule_agent_system.git
cd schedule_agent_system
```

2. **Create virtual environment**
```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Setup Credentials

#### 1. Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google Calendar API**
4. Create **OAuth 2.0 credentials** (Desktop app)
5. Download the JSON file
6. Save it as `config/credentials.json`

**Detailed guide**: See [SETUP_GOOGLE.md](docs/SETUP_GOOGLE.md)

#### 2. Azure OpenAI API

1. Copy the template: `cp config/config_template.py config/config.py`
2. Edit `config/config.py` and add your credentials:
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_DEPLOYMENT`

**Alternative**: Use environment variables:
```bash
# Windows PowerShell
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "your-api-key"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

# Mac/Linux
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
```

### First Run
```bash
python main.py
```

On first run:
1. Browser will open for Google Calendar authentication
2. You'll be asked to configure minimum gap between events
3. Main menu will appear

##  Usage

### Import a Schedule

1. **From PDF**:
   - Place your PDF in `tests/sample_schedules/`
   - Select option 1 from main menu
   - Enter path: `tests/sample_schedules/your_schedule.pdf`

2. **From Screenshot**:
   - Save screenshot as PNG/JPG in `tests/sample_schedules/`
   - Select option 1 from main menu
   - Enter path: `tests/sample_schedules/your_screenshot.png`

### Modify Events
Select option 2 and use natural language:
```
"move Machine Learning to Friday at 2pm"
"cancel Neural Networks on Thursday"
"change location of AI lecture to Room 305"
"reschedule Applied AI to next week"
```

### Check Conflicts
Select option 3 to analyze your calendar for:
-  Overlapping events
-  Tight schedules (insufficient gap time)
-  Back-to-back events at different locations

##  Project Structure
```
schedule_agent_system/
├── agents/                      # All agent modules
│   ├── parser_agent.py         # PDF/image parsing
│   ├── calendar_agent.py       # Calendar operations
│   ├── change_manager_agent.py # Event modifications
│   ├── conflict_detector_agent.py # Conflict detection
│   └── orchestrator_agent.py   # Workflow coordination
├── utils/                       # Utility modules
│   ├── llm_client.py           # Azure OpenAI integration
│   ├── pdf_extractor.py        # PDF/image text extraction
│   └── calendar_client.py      # Google Calendar API wrapper
├── config/                      # Configuration
│   ├── config_template.py      # Template for credentials
│   ├── credentials_template.json # Template for Google creds
│   └── [config.py]             # Your actual config (not in Git)
├── tests/
│   └── sample_schedules/       # Test schedule files
├── main.py                      # Main application
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

##  Configuration

### Minimum Gap Between Events

Configure in the app (Option 6) or in `config/config.py`:
```python
MINIMUM_GAP_MINUTES = 15  # Default: 15 minutes
```

Suggested values:
- **0 min**: Back-to-back is OK
- **15 min**: Standard buffer (default)
- **30 min**: Different buildings
- **60 min**: Lunch/break time

### Timezone

Change in `config/config.py`:
```python
DEFAULT_TIMEZONE = 'Europe/Brussels'  # Change to your timezone
```

##  Testing

Run agent tests individually:
```bash
# Test Parser Agent
python agents/parser_agent.py

# Test Calendar Agent
python agents/calendar_agent.py

# Test Conflict Detector
python agents/conflict_detector_agent.py

# Test Change Manager
python agents/change_manager_agent.py
```

##  Troubleshooting

### "Credentials file not found"
Ensure `config/credentials.json` exists and contains valid Google OAuth credentials.

### "Azure OpenAI authentication failed"
Check that `config/config.py` has correct Azure credentials or environment variables are set.


##  Requirements
See [requirements.txt](requirements.txt) for full list.

Key dependencies:
- `openai>=1.57.0` - Azure OpenAI integration
- `google-api-python-client>=2.108.0` - Google Calendar API
- `PyPDF2>=3.0.1` - PDF text extraction
- `Pillow>=11.0.0` - Image processing

##  Academic Context
This project was developed for the Applied AI course at KU Leuven (2025) as a demonstration of agentic AI systems and practical LLM integration.

### Assignment Requirements Met
- Extract schedule information from PDF/screenshots  
- Translate to API calls for calendar updates  
- Handle user modification requests with natural language  
- Detect scheduling conflicts  
- Multi-agent collaboration and coordination  
- Working prototype with complete documentation  

## 👨‍💻 Author
**Lorenzo Stefano Fresca**  
AI Master's Program  
KU Leuven, November of 2025

## 📄 License
Educational project - KU Leuven

=======
# schedule-agent-system
AI-powered calendar management with multi-agent architecture
>>>>>>> 29b54ea0830ee37d38c01d3b7c869283009b4880
