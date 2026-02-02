# Deepseeker
## 📂 Project Structure

```text
Deepseeker/
├── backend/                        # FastAPI Application
│   ├── app/
│   │   ├── api/                    # API Routes (Endpoints)
│   │   │   └── v1/
│   │   │       ├── chat.py         # Chat & streaming logic
│   │   │       └── ingest.py       # API for file/data ingestion
│   │   ├── core/                   # System-wide logic
│   │   │   ├── config.py           # Environment variables & settings
│   │   │   └── database.py         # Connection setup for all 4 data sources
│   │   ├── models/                 # Pydantic schemas & SQLAlchemy models
│   │   ├── services/               # Core Business Logic
│   │   │   ├── orchestrator.py     # Router logic for query dispatching
│   │   │   └── llm_service.py      # LLM integration (OpenAI/Gemini)
│   │   ├── tools/                  # Database-specific retrieval modules
│   │   │   ├── sql_tool.py         # Relational DB querying
│   │   │   ├── graph_tool.py       # Knowledge graph traversal
│   │   │   ├── vector_tool.py      # Semantic vector search
│   │   │   └── web_search.py       # Real-time web retrieval
│   │   └── main.py                 # Application entry point
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Backend containerization
│
├── frontend/                       # React Vite Application
│   ├── src/
│   │   ├── components/             # UI: ChatBox, Graphs, Data Tables
│   │   ├── hooks/                  # Custom hooks: useChat, useAuth
│   │   ├── api/                    # Axios instances for Backend communication
│   │   └── ...
│   ├── .env.development            # VITE_API_URL=http://localhost:8000
│   └── .env.production             # VITE_API_URL=https://your-api.com
│
├── research/                       # [LAB] Experimental & Prototyping environment
│   ├── data/                       # Raw data (CSV, PDF) for testing purposes
│   ├── notebooks/                  # Jupyter Notebooks (.ipynb)
│   │   ├── 01_test_sql_query.ipynb # SQL generation prompt engineering
│   │   ├── 02_test_vector_search.ipynb # Search accuracy & retrieval testing
│   │   └── 03_graph_building.ipynb # Neo4j node & edge creation logic
│   ├── scripts/                    # One-time execution scripts
│   │   └── seed_db.py              # Script to populate databases with sample data
│   └── .env                        # Environment configurations for testing
│
├── data/                           # Initialization & Seed Data
│   ├── init.sql                    # SQL database schema/seed
│   └── knowledge_graph.csv         # Graph database initial data
│
├── README.md                       # Project documentation & setup guide
└── .gitignore                      # Version control exclusion rules