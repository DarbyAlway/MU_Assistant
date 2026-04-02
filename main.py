from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from SAR import MusashinoAssistant_SAR
from RAG import MusashinoAssistant_RAG
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import time

app = FastAPI()

# In-memory storage for history
# In a production app with many users, you'd want to use a Session ID to separate users.
chat_history = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

assistant_SAR = MusashinoAssistant_SAR()
assistant_RAG = MusashinoAssistant_RAG()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

def detect_language(text: str):
    for c in text:
        if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9faf':
            return "japanese"
    return "english"

class SearchRequest(BaseModel):
    query: str

@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

# 1. This route serves the actual HTML page
@app.get("/history")
async def get_history_page():
    return FileResponse('frontend/history.html')

# 2. This route provides the DATA to the Javascript
@app.get("/api/history")
async def get_history_data():
    return {"status": "success", "history": chat_history}

@app.post("/search")
async def search(request: SearchRequest):
    try:
        start_time = time.perf_counter()
        user_query = request.query
        language = detect_language(user_query)

        loop = asyncio.get_event_loop()

        sar_future = loop.run_in_executor(None, assistant_SAR.get_answer, user_query, language)
        rag_future = loop.run_in_executor(None, assistant_RAG.get_answer, user_query, language)

        result_SAR, result_RAG = await asyncio.gather(sar_future, rag_future)
        
        answer_SAR, sar_url = result_SAR
        answer_RAG, rag_url = result_RAG

        duration = round(time.perf_counter() - start_time, 2)

        # Prepare the response object
        response_data = {
            "query": user_query,
            "answer_SAR": answer_SAR,
            "answer_RAG": answer_RAG,
            "sources_SAR": sar_url if sar_url else [],
            "sources_RAG": rag_url if rag_url else [],
            "duration": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        print(response_data["sources_RAG"])
        # Save to in-memory history
        chat_history.append(response_data)
        
        # Limit history size to last 50 entries to prevent memory bloat
        if len(chat_history) > 50:
            chat_history.pop(0)

        return {**{"status": "success"}, **response_data}

    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)