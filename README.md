# Code Collab

A full-stack real-time collaborative coding platform with a React frontend and Flask + Socket.IO backend.

## Folder Structure

```text
Code-Collab/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   ├── BottomPanel.jsx
│       │   ├── EditorArea.jsx
│       │   ├── FileExplorer.jsx
│       │   └── TeamChatSidebar.jsx
│       ├── hooks/
│       │   └── useCollabSession.js
│       ├── services/
│       │   ├── api.js
│       │   └── socketClient.js
│       └── data/
│           └── mockData.js
├── api.py
├── main.py
├── requirements.txt
└── ...
```

## Backend Setup (Flask)

1. Create and activate virtual environment:
   - `python -m venv .venv`
   - `source .venv/bin/activate` (Linux/macOS) or `.venv\\Scripts\\activate` (Windows)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run backend server:
   - `python main.py`
4. Backend runs at:
   - `http://localhost:5000`

## Frontend Setup (React + Vite + Tailwind + Monaco)

1. Open a new terminal and go to frontend:
   - `cd frontend`
2. Install dependencies:
   - `npm install`
3. Start frontend:
   - `npm run dev`
4. Frontend runs at:
   - `http://localhost:5173`

## Features Implemented

- VS Code-style UI layout:
  - Left Explorer sidebar
  - Center Monaco editor with tabs and language selector (Python/C++/Java)
  - Right Team + Chat sidebar with call controls (UI only)
  - Bottom panel tabs (Problems, Output, Debug Console, Terminal)
- Backend responsibilities:
  - Room join/leave management
  - Shared code synchronization
  - Chat message broadcast
  - Code execution API: `POST /run`
- Supported Socket.IO events:
  - `join_room`
  - `code_change`
  - `send_message`
  - `user_join`
  - `user_leave`
- Execution security:
  - 3-second timeout
  - Temporary files deleted after execution

## API Contract

### POST `/run`

Request body:

```json
{
  "language": "python | cpp | java",
  "code": "string"
}
```

Response:

```json
{
  "output": "string"
}
```

## Suggested Improvements

- Add authenticated users and persistent room storage (Redis/PostgreSQL)
- Add per-room execution sandboxing with containers
- Add rate limits for run/chat events
- Add automated tests for API + socket events
- Add reconnect and conflict-resolution strategy for editor sync
