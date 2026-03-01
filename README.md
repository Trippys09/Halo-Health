# HALO Health

An AI-powered healthcare platform featuring multi-agent architecture for comprehensive health assistance, powered by Google Gemini.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)

## Features

### AI Health Agents

| Agent | Description |
|-------|-------------|
| **Virtual Doctor** | General health consultations and medical guidance |
| **Diagnostic Agent** | Symptom analysis and preliminary assessments |
| **Dietary Agent** | Personalized nutrition and meal planning advice |
| **Wellbeing Agent** | Mental health support and wellness tips |
| **Insurance Agent** | Healthcare coverage guidance and claims assistance |
| **Oculomics (IRIS)** | Retinal fundus image analysis for health biomarkers |
| **Orchestrator** | Intelligent routing to the right specialist agent |

### Key Capabilities

- **Multi-Agent Architecture** - Specialized AI agents for different health domains
- **Retinal Analysis (IRIS)** - Upload fundus images for AI-powered biomarker detection
- **Conversation Memory** - ChromaDB-powered context retention across sessions
- **Real-time Chat** - Streaming responses with markdown support
- **PDF Export** - Download consultation reports
- **Voice Assistant** - Speech-to-text input support
- **Secure Auth** - JWT-based authentication

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Google Gemini** - LLM for AI agents
- **ChromaDB** - Vector database for conversation memory
- **PostgreSQL** - Primary database (Neon for production)
- **SQLAlchemy** - ORM for database operations

### Frontend
- **React 18** - Modern UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **React Router** - Client-side routing

## Project Structure

```
Halo-Health/
├── backend/
│   ├── agents/           # AI agent implementations
│   │   ├── base_agent.py
│   │   ├── virtual_doctor_agent.py
│   │   ├── diagnostic_agent.py
│   │   ├── dietary_agent.py
│   │   ├── wellbeing_agent.py
│   │   ├── insurance_agent.py
│   │   ├── oculomics_agent.py
│   │   └── orchestrator_agent.py
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── models.py         # Database models
│   ├── config.py         # Configuration
│   ├── main.py           # FastAPI app
│   └── requirements.txt
│
├── frontend-react/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # Reusable components
│   │   ├── context/      # React context
│   │   └── utils/        # Utilities
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml
├── render.yaml           # Render deployment config
└── DEPLOYMENT.md         # Deployment guide
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/halo-health.git
   cd halo-health
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Setup Frontend**
   ```bash
   cd ../frontend-react
   npm install
   ```

### Running Locally

**Option 1: Using the start script**
```bash
chmod +x start.sh
./start.sh
```

**Option 2: Manual start**
```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend-react
npm run dev
```

Access the app at:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_jwt_secret_key

# Database
DATABASE_URL=postgresql+psycopg://user:pass@host/db?sslmode=require

# Optional
TAVILY_API_KEY=your_tavily_key  # For web search
PRO_MODEL=gemini-2.5-flash
FLASH_MODEL=gemini-2.5-flash
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Quick Deploy (Free)

| Service | Purpose | Cost |
|---------|---------|------|
| **Vercel** | Frontend hosting | Free |
| **Render** | Backend hosting | Free |
| **Neon** | PostgreSQL database | Free |

Total: **$0/month**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | User login |
| `/auth/me` | GET | Get current user |
| `/sessions` | GET/POST | Manage chat sessions |
| `/sessions/{id}/messages` | GET | Get session messages |
| `/agents/{type}/chat` | POST | Chat with specific agent |
| `/agents/oculomics/chat` | POST | Analyze retinal images |

## Screenshots

*Coming soon*

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini for AI capabilities
- FastAPI for the excellent web framework
- The open-source community

---

Built with care for better healthcare accessibility.
