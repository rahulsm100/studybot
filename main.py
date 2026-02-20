# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client_db = MongoClient(MONGO_URI)
db = client_db.studybot_db
chat_collection = db.chats

# FastAPI app
app = FastAPI(title="Study Bot")

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Request body
class ChatRequest(BaseModel):
    user_message: str

# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.user_message

    try:
        # Retrieve previous chats for context
        previous_chats = list(chat_collection.find({}, {"_id": 0}))
        context_messages = [{"role": "system", "content": "You are a helpful study assistant."}]

        for chat in previous_chats:
            context_messages.append({"role": "user", "content": chat["user_message"]})
            context_messages.append({"role": "assistant", "content": chat["bot_response"]})

        # Add current user message
        context_messages.append({"role": "user", "content": user_message})

        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=context_messages
        )
        bot_response = response.choices[0].message.content

        # Save chat to MongoDB
        chat_collection.insert_one({
            "user_message": user_message,
            "bot_response": bot_response
        })

        # Return response
        return {"response": bot_response}

    except Exception as e:
        return {"error": str(e)}
