from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import aiohttp
import asyncio
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import json
import time
from collections import deque

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Queue system
class RequestQueue:
    def __init__(self, max_concurrent=10):
        self.queue = deque()
        self.processing = set()
        self.max_concurrent = max_concurrent
        self.api_keys = os.getenv('DEEPSEEK_API_KEYS', '').split(',')
        self.current_key_index = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds

    def get_next_api_key(self):
        if not self.api_keys:
            raise ValueError("No API keys available")
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    async def add_request(self, request_id, request_data):
        self.queue.append((request_id, request_data))
        await self.process_queue()

    async def process_queue(self):
        while self.queue and len(self.processing) < self.max_concurrent:
            request_id, request_data = self.queue.popleft()
            if request_id not in self.processing:
                self.processing.add(request_id)
                asyncio.create_task(self.process_request(request_id, request_data))

    async def process_request(self, request_id, request_data):
        try:
            async with self.semaphore:
                # Rate limiting
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    await asyncio.sleep(self.min_request_interval - time_since_last_request)
                
                self.last_request_time = time.time()
                
                api_key = self.get_next_api_key()
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": request_data['message']}
                            ],
                            "temperature": 0.7
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result['choices'][0]['message']['content']
                            
                            # Save to file
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_entry = {
                                "timestamp": timestamp,
                                "request_id": request_id,
                                "message": request_data['message'],
                                "response": response_text
                            }
                            
                            with open("chat_logs.jsonl", "a", encoding="utf-8") as f:
                                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                            
                            logger.info(f"Request {request_id} processed successfully")
                        else:
                            error_text = await response.text()
                            logger.error(f"API Error for request {request_id}: {error_text}")
                            raise HTTPException(status_code=response.status, detail=error_text)
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}")
        finally:
            self.processing.remove(request_id)
            await self.process_queue()

# Initialize queue
request_queue = RequestQueue()

class ChatRequest(BaseModel):
    message: str
    request_id: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    request_id = request.request_id or str(int(time.time() * 1000))
    await request_queue.add_request(request_id, request.dict())
    return {"status": "processing", "request_id": request_id}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    if request_id in request_queue.processing:
        return {"status": "processing"}
    return {"status": "completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 