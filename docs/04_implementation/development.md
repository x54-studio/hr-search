## �� Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Quick Start (5 minutes)

1. **Clone and start database**
   ```bash
   git clone https://github.com/x54-studio/hr-search.git
   cd hr-search
   docker-compose up -d db
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5431/hr_search" > .env
   ```

5. **Seed sample data**
   ```bash
   python backend/scripts/generate_sample.py
   ```

6. **Start the API**
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Test the API**
   ```bash
   curl http://localhost:8000/api/health
   curl "http://localhost:8000/api/search?q=rekrutacja"
   ```