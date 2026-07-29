# TruthLens — Deepfake Detection System

## Quick start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# opens at http://localhost:5173
```

## Demo flow (for judges)
1. Open http://localhost:5173
2. Either upload a video OR click **Run demo analysis**
3. Watch the live forensic pipeline animate step by step
4. Read the verdict card, confidence score, and frame indicators

## Git workflow
- `backend-dev` → all Python changes
- `frontend-dev` → all React changes
- `main` → working merges only, push daily