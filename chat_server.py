"""
Chat Server - FastAPI backend for the AI Agent Chat Interface
Connects the web interface to the Enhanced AI Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
import json
import asyncio
from typing import Dict, Any
import os
from datetime import datetime

# Import our enhanced agent
from enhanced_ai_agent import EnhancedAIAgent, AgentConfig

app = FastAPI(title="AI Agent Chat Server", version="1.0.0")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    agent_stats: Dict[str, Any] = None

# Global agent instances (in production, use proper session management)
agent_sessions: Dict[str, EnhancedAIAgent] = {}

def get_or_create_agent(session_id: str) -> EnhancedAIAgent:
    """Get or create agent for session"""
    if session_id not in agent_sessions:
        # Setup configuration
        config = AgentConfig()
        config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        config.weather_api_key = os.getenv("WEATHER_API_KEY", "")
        
        # Disable LLM if no API key (for demo purposes)
        if not config.openai_api_key:
            config.use_llm = False
        
        agent_sessions[session_id] = EnhancedAIAgent(config)
    
    return agent_sessions[session_id]

@app.get("/", response_class=HTMLResponse)
async def serve_chat_interface():
    """Serve the chat interface HTML"""
    try:
        with open("chat_interface.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat interface not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Get agent for this session
        agent = get_or_create_agent(request.session_id)
        
        # Process message with agent
        response = agent.run(request.message)
        
        # Clean up the response (remove emoji prefix if present)
        clean_response = response
        if clean_response.startswith("🤖 Agent: "):
            clean_response = clean_response[11:]  # Remove "🤖 Agent: "
        elif clean_response.startswith(("🌤️", "🕐", "👋", "❓")):
            # Remove emoji and "Agent: " prefix
            parts = clean_response.split("Agent: ", 1)
            if len(parts) > 1:
                clean_response = parts[1]
        
        return ChatResponse(
            response=clean_response,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            agent_stats=agent.get_enhanced_stats()
        )
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint for real-time responses"""
    async def generate_response():
        try:
            agent = get_or_create_agent(request.session_id)
            
            # For demo, we'll simulate streaming by yielding parts of response
            response = agent.run(request.message)
            
            # Clean response
            clean_response = response
            if clean_response.startswith("🤖 Agent: "):
                clean_response = clean_response[11:]
            
            # Simulate streaming by yielding words
            words = clean_response.split()
            for i, word in enumerate(words):
                chunk = {
                    "type": "text",
                    "content": word + " ",
                    "is_complete": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.1)  # Simulate processing time
            
            # Send completion signal
            completion = {
                "type": "complete",
                "session_id": request.session_id,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(completion)}\n\n"
            
        except Exception as e:
            error_chunk = {
                "type": "error",
                "content": f"Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/chat/stats/{session_id}")
async def get_agent_stats(session_id: str):
    """Get agent statistics for a session"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_sessions[session_id]
    return agent.get_enhanced_stats()

@app.post("/chat/reset/{session_id}")
async def reset_agent_session(session_id: str):
    """Reset agent session"""
    if session_id in agent_sessions:
        # Create new agent instance
        config = agent_sessions[session_id].config
        agent_sessions[session_id] = EnhancedAIAgent(config)
        return {"message": "Session reset successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/chat/sessions")
async def list_sessions():
    """List active sessions"""
    sessions = []
    for session_id, agent in agent_sessions.items():
        stats = agent.get_enhanced_stats()
        sessions.append({
            "session_id": session_id,
            "conversation_count": stats["basic_stats"]["conversations"],
            "session_duration": stats["basic_stats"]["session_duration"],
            "last_intent": stats["current_state"].get("current_intent"),
        })
    return {"sessions": sessions}

@app.post("/chat/configure/{session_id}")
async def configure_agent(session_id: str, config_data: dict):
    """Configure agent settings"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_sessions[session_id]
    
    try:
        # Update configuration
        agent.configure(**config_data)
        return {"message": "Configuration updated successfully", "config": config_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")

# Enhanced chat interface with more features
@app.get("/advanced", response_class=HTMLResponse)
async def serve_advanced_interface():
    """Serve advanced chat interface with more features"""
    advanced_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced AI Agent Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 300px; gap: 20px; }
        .chat-panel { background: white; border-radius: 10px; padding: 20px; height: 600px; display: flex; flex-direction: column; }
        .stats-panel { background: white; border-radius: 10px; padding: 20px; }
        .messages { flex: 1; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
        .message { margin-bottom: 10px; padding: 8px; border-radius: 8px; }
        .user { background: #e3f2fd; text-align: right; }
        .agent { background: #f1f8e9; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area button { padding: 10px 20px; background: #2196f3; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .stats { font-size: 12px; }
        .stats h3 { margin-top: 0; }
        .config-section { margin-top: 20px; }
        .config-section input, .config-section select { width: 100%; padding: 5px; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-panel">
            <h2>🤖 Advanced AI Agent Chat</h2>
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
                <button onclick="streamMessage()">Stream</button>
            </div>
        </div>
        
        <div class="stats-panel">
            <h3>📊 Agent Stats</h3>
            <div class="stats" id="stats">Loading...</div>
            
            <div class="config-section">
                <h4>⚙️ Configuration</h4>
                <label>Model Temperature:</label>
                <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.7" onchange="updateConfig()">
                <span id="tempValue">0.7</span>
                
                <label>Use LLM:</label>
                <input type="checkbox" id="useLLM" checked onchange="updateConfig()">
                
                <button onclick="resetSession()">Reset Session</button>
            </div>
        </div>
    </div>

    <script>
        let sessionId = 'advanced_' + Date.now();
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, session_id: sessionId })
                });
                
                const data = await response.json();
                addMessage(data.response, 'agent');
                updateStats(data.agent_stats);
            } catch (error) {
                addMessage('Error: ' + error.message, 'agent');
            }
        }
        
        function addMessage(content, sender) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${sender}`;
            div.textContent = `${sender === 'user' ? 'You' : 'Agent'}: ${content}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function updateStats(stats) {
            if (!stats) return;
            const statsDiv = document.getElementById('stats');
            statsDiv.innerHTML = `
                <strong>Conversations:</strong> ${stats.basic_stats.conversations}<br>
                <strong>Memory Size:</strong> ${stats.basic_stats.memory_size}<br>
                <strong>LLM Enabled:</strong> ${stats.basic_stats.llm_enabled}<br>
                <strong>Session Duration:</strong> ${stats.basic_stats.session_duration}<br>
                <strong>Current Intent:</strong> ${stats.current_state.current_intent || 'None'}<br>
                <strong>User Name:</strong> ${stats.current_state.user_name || 'Unknown'}
            `;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') sendMessage();
        }
        
        async function resetSession() {
            try {
                await fetch(`/chat/reset/${sessionId}`, { method: 'POST' });
                document.getElementById('messages').innerHTML = '';
                addMessage('Session reset!', 'agent');
            } catch (error) {
                addMessage('Reset failed: ' + error.message, 'agent');
            }
        }
        
        async function updateConfig() {
            const temperature = document.getElementById('temperature').value;
            const useLLM = document.getElementById('useLLM').checked;
            document.getElementById('tempValue').textContent = temperature;
            
            try {
                await fetch(`/chat/configure/${sessionId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ temperature: parseFloat(temperature), use_llm: useLLM })
                });
            } catch (error) {
                console.error('Config update failed:', error);
            }
        }
        
        // Load initial stats
        setTimeout(async () => {
            try {
                const response = await fetch(`/chat/stats/${sessionId}`);
                const stats = await response.json();
                updateStats(stats);
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }, 1000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=advanced_html)

if __name__ == "__main__":
    print("🚀 Starting AI Agent Chat Server...")
    print("📱 Chat Interface: http://localhost:8000")
    print("🔧 Advanced Interface: http://localhost:8000/advanced")
    print("📊 API Docs: http://localhost:8000/docs")
    
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OPENAI_API_KEY found - running without LLM capabilities")
    if not os.getenv("WEATHER_API_KEY"):
        print("⚠️  No WEATHER_API_KEY found - weather features disabled")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

