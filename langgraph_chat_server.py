"""
LangGraph Chat Server - FastAPI backend for LangGraph Agent
Connects the web UI to the Full LangGraph Agent
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

# Import our LangGraph agent
from full_langgraph_agent import LangGraphAgent, LangGraphConfig

app = FastAPI(title="LangGraph AI Agent Chat Server", version="2.0.0")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    agent_state: Dict[str, Any] = None
    node_path: list = []

# Global agent instance
langgraph_agent: LangGraphAgent = None

def initialize_agent():
    """Initialize the LangGraph agent"""
    global langgraph_agent
    
    config = LangGraphConfig()
    config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    config.enable_streaming = True
    config.enable_interrupts = True
    
    langgraph_agent = LangGraphAgent(config)
    print("🕸️ LangGraph Agent initialized for web server!")

@app.on_event("startup")
async def startup_event():
    """Initialize agent on server startup"""
    initialize_agent()

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
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "agent_type": "LangGraph",
        "features": ["graph_workflow", "checkpointing", "HITL", "streaming"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint using LangGraph agent"""
    try:
        if not langgraph_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Run LangGraph agent
        response = langgraph_agent.run(request.message, request.session_id)
        
        # Get agent state for debugging
        agent_state = langgraph_agent.get_state(request.session_id)
        
        # Extract node path from state if available
        node_path = []
        if agent_state and "current_node" in agent_state:
            node_path = [agent_state["current_node"]]
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            agent_state=agent_state,
            node_path=node_path
        )
    
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@app.post("/chat/async")
async def chat_async_endpoint(request: ChatRequest):
    """Async chat endpoint"""
    try:
        if not langgraph_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Run LangGraph agent asynchronously
        response = await langgraph_agent.run_async(request.message, request.session_id)
        
        agent_state = langgraph_agent.get_state(request.session_id)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            agent_state=agent_state
        )
    
    except Exception as e:
        print(f"Async chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Async chat error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint with LangGraph"""
    async def generate_stream():
        try:
            if not langgraph_agent:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Agent not initialized'})}\n\n"
                return
            
            # Stream from LangGraph agent
            async for event in langgraph_agent.stream(request.message, request.session_id):
                # Process different types of events from LangGraph
                for node_name, node_output in event.items():
                    if node_output and isinstance(node_output, dict):
                        
                        # Stream node progress
                        progress_chunk = {
                            "type": "node_progress",
                            "node": node_name,
                            "content": f"Processing: {node_name}...",
                            "timestamp": datetime.now().isoformat()
                        }
                        yield f"data: {json.dumps(progress_chunk)}\n\n"
                        
                        # Stream partial response if available
                        if "final_response" in node_output and node_output["final_response"]:
                            response_chunk = {
                                "type": "text",
                                "content": node_output["final_response"],
                                "node": node_name,
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(response_chunk)}\n\n"
                            
                        # Stream tool results
                        if "tool_results" in node_output and node_output["tool_results"]:
                            tool_chunk = {
                                "type": "tool_result",
                                "content": f"Tool executed: {len(node_output['tool_results'])} results",
                                "tools": node_output["tool_results"],
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(tool_chunk)}\n\n"
            
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
                "content": f"Streaming error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.get("/agent/state/{session_id}")
async def get_agent_state(session_id: str):
    """Get current LangGraph agent state"""
    if not langgraph_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        state = langgraph_agent.get_state(session_id)
        return {
            "session_id": session_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State retrieval error: {str(e)}")

@app.post("/agent/reset/{session_id}")
async def reset_agent_session(session_id: str):
    """Reset LangGraph agent session"""
    if not langgraph_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        langgraph_agent.reset_session(session_id)
        return {
            "message": f"Session {session_id} reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")

@app.get("/agent/graph")
async def get_agent_graph():
    """Get LangGraph agent workflow structure"""
    if not langgraph_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    # Return graph structure info
    return {
        "nodes": [
            "input_processing",
            "intent_classification", 
            "decision_making",
            "tool_execution",
            "response_generation",
            "human_approval",
            "error_handling"
        ],
        "edges": {
            "START": "input_processing",
            "input_processing": "intent_classification",
            "intent_classification": "decision_making",
            "decision_making": ["tool_execution", "human_approval", "error_handling"],
            "tool_execution": ["response_generation", "error_handling"],
            "response_generation": "END"
        },
        "features": [
            "conditional_routing",
            "human_in_the_loop",
            "error_recovery",
            "state_persistence",
            "streaming"
        ]
    }

# Enhanced chat interface that shows LangGraph features
@app.get("/langgraph", response_class=HTMLResponse)
async def serve_langgraph_interface():
    """Serve enhanced interface showing LangGraph features"""
    langgraph_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangGraph AI Agent</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 300px 250px; gap: 20px; }
        .panel { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-panel { height: 600px; display: flex; flex-direction: column; }
        .messages { flex: 1; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user { background: #e3f2fd; text-align: right; }
        .agent { background: #f1f8e9; }
        .node-progress { background: #fff3e0; font-size: 12px; font-style: italic; }
        .tool-result { background: #f3e5f5; font-size: 12px; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; color: white; }
        .btn-primary { background: #2196f3; }
        .btn-success { background: #4caf50; }
        .btn-warning { background: #ff9800; }
        .state-panel { max-height: 600px; overflow-y: auto; }
        .graph-panel { max-height: 600px; overflow-y: auto; }
        .node { padding: 8px; margin: 5px 0; border-radius: 5px; font-size: 12px; }
        .node.active { background: #4caf50; color: white; }
        .node.pending { background: #ffc107; }
        .node.completed { background: #28a745; color: white; }
        h3 { margin-top: 0; color: #333; }
        .feature-badge { display: inline-block; background: #e3f2fd; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 11px; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 11px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="panel chat-panel">
            <h2>🕸️ LangGraph AI Agent</h2>
            <div class="messages" id="messages"></div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                <button class="btn btn-success" onclick="streamMessage()">Stream</button>
                <button class="btn btn-warning" onclick="resetSession()">Reset</button>
            </div>
        </div>
        
        <div class="panel state-panel">
            <h3>📊 Agent State</h3>
            <div class="feature-badge">Graph Workflow</div>
            <div class="feature-badge">HITL</div>
            <div class="feature-badge">Checkpointing</div>
            <div class="feature-badge">Streaming</div>
            <div id="agentState">Loading...</div>
        </div>
        
        <div class="panel graph-panel">
            <h3>🕸️ Workflow Graph</h3>
            <div id="graphNodes">
                <div class="node pending">input_processing</div>
                <div class="node pending">intent_classification</div>
                <div class="node pending">decision_making</div>
                <div class="node pending">tool_execution</div>
                <div class="node pending">response_generation</div>
                <div class="node pending">human_approval</div>
                <div class="node pending">error_handling</div>
            </div>
            <h4>Features:</h4>
            <ul style="font-size: 12px;">
                <li>Conditional routing</li>
                <li>Error recovery</li>
                <li>State persistence</li>
                <li>Human interrupts</li>
                <li>Tool integration</li>
            </ul>
        </div>
    </div>

    <script>
        let sessionId = 'langgraph_' + Date.now();
        
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
                
                if (data.agent_state) {
                    updateState(data.agent_state);
                }
                
                if (data.node_path) {
                    updateGraphNodes(data.node_path);
                }
                
            } catch (error) {
                addMessage('Error: ' + error.message, 'agent');
            }
        }
        
        async function streamMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, session_id: sessionId })
                });
                
                const reader = response.body.getReader();
                let currentMessage = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = new TextDecoder().decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.type === 'node_progress') {
                                    addMessage(data.content, 'node-progress');
                                    highlightNode(data.node);
                                } else if (data.type === 'text') {
                                    currentMessage = data.content;
                                    addMessage(currentMessage, 'agent');
                                } else if (data.type === 'tool_result') {
                                    addMessage(data.content, 'tool-result');
                                } else if (data.type === 'complete') {
                                    console.log('Stream complete');
                                }
                            } catch (e) {
                                console.error('Parse error:', e);
                            }
                        }
                    }
                }
            } catch (error) {
                addMessage('Streaming error: ' + error.message, 'agent');
            }
        }
        
        function addMessage(content, sender) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${sender}`;
            div.innerHTML = `<strong>${sender}:</strong> ${content}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function updateState(state) {
            const stateDiv = document.getElementById('agentState');
            stateDiv.innerHTML = `<pre>${JSON.stringify(state, null, 2)}</pre>`;
        }
        
        function highlightNode(nodeName) {
            const nodes = document.querySelectorAll('.node');
            nodes.forEach(node => {
                if (node.textContent === nodeName) {
                    node.className = 'node active';
                    setTimeout(() => {
                        node.className = 'node completed';
                    }, 1000);
                }
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') sendMessage();
        }
        
        async function resetSession() {
            try {
                await fetch(`/agent/reset/${sessionId}`, { method: 'POST' });
                document.getElementById('messages').innerHTML = '';
                addMessage('Session reset! LangGraph agent reinitialized.', 'agent');
                
                // Reset graph visualization
                const nodes = document.querySelectorAll('.node');
                nodes.forEach(node => node.className = 'node pending');
                
            } catch (error) {
                addMessage('Reset failed: ' + error.message, 'agent');
            }
        }
        
        // Load initial state
        setTimeout(async () => {
            try {
                const response = await fetch(`/agent/state/${sessionId}`);
                const data = await response.json();
                updateState(data.state);
            } catch (error) {
                console.error('Failed to load initial state:', error);
            }
        }, 1000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=langgraph_html)

if __name__ == "__main__":
    print("🕸️ Starting LangGraph AI Agent Chat Server...")
    print("📱 Basic Interface: http://localhost:8000")
    print("🕸️ LangGraph Interface: http://localhost:8000/langgraph")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔧 Agent Graph: http://localhost:8000/agent/graph")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
