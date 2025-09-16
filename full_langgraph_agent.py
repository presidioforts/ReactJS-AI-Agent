"""
Full LangGraph AI Agent - Complete Architecture
Converts our enhanced agent to proper LangGraph implementation
"""

import json
import time
import os
from typing import TypedDict, List, Optional, Dict, Any
try:
    from typing import Literal, Annotated
except ImportError:
    from typing_extensions import Literal, Annotated
from datetime import datetime
from dataclasses import dataclass

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# LangChain imports for LLM
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    print("LangChain not installed. Run: pip install langchain-openai")

# ============================================================================
# STATE DEFINITION - The data that flows through the graph
# ============================================================================

class AgentState(TypedDict):
    """Complete state for LangGraph agent"""
    # Input/Output
    messages: Annotated[List[Dict], add_messages]
    user_input: str
    processed_input: str
    final_response: str
    
    # Intent & Decision
    intent: Optional[str]
    confidence: float
    action: Optional[str]
    
    # Tool Execution
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    # Context & Memory
    conversation_history: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    session_data: Dict[str, Any]
    
    # Flow Control
    current_node: str
    requires_approval: bool
    approval_granted: bool
    retry_count: int
    
    # Error Handling
    errors: List[str]
    last_error: Optional[str]
    
    # Streaming
    streaming_content: str
    is_streaming: bool

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class LangGraphConfig:
    """Configuration for LangGraph agent"""
    openai_api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500
    
    # LangGraph settings
    max_retries: int = 3
    enable_streaming: bool = True
    enable_interrupts: bool = True
    
    # Checkpointing
    checkpoint_db: str = "agent_checkpoints.db"

# ============================================================================
# MOCK APIS (Tools)
# ============================================================================

def search_products_tool(query: str) -> Dict[str, Any]:
    """Mock Product Search API Tool"""
    products = {
        "laptop": [
            {"name": "MacBook Pro M3", "price": 1999, "rating": 4.8, "stock": 15},
            {"name": "Dell XPS 13", "price": 1299, "rating": 4.5, "stock": 8},
            {"name": "ThinkPad X1 Carbon", "price": 1599, "rating": 4.6, "stock": 12}
        ],
        "phone": [
            {"name": "iPhone 15 Pro", "price": 999, "rating": 4.7, "stock": 25},
            {"name": "Samsung Galaxy S24", "price": 899, "rating": 4.6, "stock": 18},
            {"name": "Google Pixel 8", "price": 699, "rating": 4.4, "stock": 20}
        ]
    }
    
    query_lower = query.lower()
    for category, items in products.items():
        if category in query_lower:
            return {
                "success": True,
                "category": category,
                "products": items,
                "count": len(items)
            }
    
    return {"success": False, "message": "No products found", "products": []}

def get_weather_tool(city: str = "London") -> Dict[str, Any]:
    """Mock Weather API Tool"""
    weather_data = {
        "london": {"temp": 15, "condition": "partly cloudy", "humidity": 65},
        "new york": {"temp": 22, "condition": "sunny", "humidity": 45},
        "paris": {"temp": 18, "condition": "light rain", "humidity": 78},
        "tokyo": {"temp": 25, "condition": "clear", "humidity": 55}
    }
    
    city_data = weather_data.get(city.lower(), weather_data["london"])
    return {
        "success": True,
        "city": city,
        "temperature": city_data["temp"],
        "condition": city_data["condition"],
        "humidity": city_data["humidity"]
    }

def get_user_profile_tool(user_id: str = "default") -> Dict[str, Any]:
    """Mock User Profile API Tool"""
    return {
        "success": True,
        "user_id": user_id,
        "name": "John Doe",
        "preferences": ["electronics", "books"],
        "loyalty_points": 1250,
        "purchase_history": ["MacBook Pro", "iPhone 14"],
        "member_since": "2023"
    }

# Tool registry
AVAILABLE_TOOLS = {
    "search_products": search_products_tool,
    "get_weather": get_weather_tool,
    "get_user_profile": get_user_profile_tool
}

# ============================================================================
# LANGGRAPH NODES - Individual processing functions
# ============================================================================

def input_processing_node(state: AgentState) -> AgentState:
    """Node 1: Process and clean user input"""
    user_input = state["user_input"]
    
    # Clean and process input
    processed = user_input.strip()
    
    # Detect sentiment (simple)
    sentiment = "neutral"
    if any(word in processed.lower() for word in ["great", "awesome", "love"]):
        sentiment = "positive"
    elif any(word in processed.lower() for word in ["bad", "terrible", "hate"]):
        sentiment = "negative"
    
    state["processed_input"] = processed
    state["current_node"] = "input_processing"
    
    # Update session data
    if "sentiment" not in state["session_data"]:
        state["session_data"]["sentiment"] = []
    state["session_data"]["sentiment"].append(sentiment)
    
    return state

def intent_classification_node(state: AgentState) -> AgentState:
    """Node 2: Classify user intent using LLM or rules"""
    processed_input = state["processed_input"]
    
    # Rule-based intent classification (fallback)
    intent = "general"
    confidence = 0.5
    
    input_lower = processed_input.lower()
    
    if any(word in input_lower for word in ["hello", "hi", "hey"]):
        intent, confidence = "greeting", 0.9
    elif any(word in input_lower for word in ["search", "find", "laptop", "phone", "product"]):
        intent, confidence = "search_products", 0.8
    elif any(word in input_lower for word in ["weather", "temperature", "forecast"]):
        intent, confidence = "weather", 0.8
    elif any(word in input_lower for word in ["profile", "account", "my info"]):
        intent, confidence = "user_profile", 0.7
    elif any(word in input_lower for word in ["help", "assist", "support"]):
        intent, confidence = "help", 0.8
    elif any(word in input_lower for word in ["bye", "goodbye"]):
        intent, confidence = "goodbye", 0.9
    elif "?" in processed_input:
        intent, confidence = "question", 0.6
    
    state["intent"] = intent
    state["confidence"] = confidence
    state["current_node"] = "intent_classification"
    
    return state

def decision_making_node(state: AgentState) -> AgentState:
    """Node 3: Decide what action to take"""
    intent = state["intent"]
    confidence = state["confidence"]
    
    # Map intents to actions
    action_map = {
        "greeting": "greet_user",
        "search_products": "search_products",
        "weather": "get_weather", 
        "user_profile": "get_user_profile",
        "help": "provide_help",
        "goodbye": "say_goodbye",
        "question": "answer_question",
        "general": "general_chat"
    }
    
    action = action_map.get(intent, "general_chat")
    
    # Set approval requirement for sensitive actions
    sensitive_actions = ["get_user_profile", "search_products"]
    state["requires_approval"] = action in sensitive_actions and confidence < 0.8
    
    state["action"] = action
    state["current_node"] = "decision_making"
    
    return state

def tool_execution_node(state: AgentState) -> AgentState:
    """Node 4: Execute tools/APIs"""
    action = state["action"]
    processed_input = state["processed_input"]
    
    tool_results = []
    
    try:
        if action == "search_products":
            result = search_products_tool(processed_input)
            tool_results.append({
                "tool": "search_products",
                "input": processed_input,
                "output": result,
                "timestamp": datetime.now().isoformat()
            })
            
        elif action == "get_weather":
            # Extract city from input (simple)
            city = "London"  # default
            words = processed_input.split()
            for i, word in enumerate(words):
                if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                    city = words[i + 1].title()
                    break
            
            result = get_weather_tool(city)
            tool_results.append({
                "tool": "get_weather",
                "input": city,
                "output": result,
                "timestamp": datetime.now().isoformat()
            })
            
        elif action == "get_user_profile":
            result = get_user_profile_tool()
            tool_results.append({
                "tool": "get_user_profile", 
                "input": "default",
                "output": result,
                "timestamp": datetime.now().isoformat()
            })
            
        else:
            # No tool needed for greetings, help, etc.
            tool_results.append({
                "tool": "none",
                "input": action,
                "output": {"success": True, "message": f"Handled {action}"},
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        state["errors"].append(f"Tool execution error: {str(e)}")
        state["last_error"] = str(e)
        tool_results.append({
            "tool": "error",
            "input": action,
            "output": {"success": False, "error": str(e)},
            "timestamp": datetime.now().isoformat()
        })
    
    state["tool_results"] = tool_results
    state["current_node"] = "tool_execution"
    
    return state

def response_generation_node(state: AgentState) -> AgentState:
    """Node 5: Generate natural language response"""
    action = state["action"]
    intent = state["intent"]
    tool_results = state["tool_results"]
    user_input = state["user_input"]
    
    response = "I'm here to help!"
    
    try:
        if tool_results:
            latest_result = tool_results[-1]
            tool_output = latest_result["output"]
            
            if action == "search_products" and tool_output.get("success"):
                products = tool_output["products"]
                if products:
                    response = f"Found {len(products)} products:\n"
                    for product in products[:3]:  # Show top 3
                        response += f"• {product['name']} - ${product['price']} (⭐{product['rating']}) - {product['stock']} in stock\n"
                else:
                    response = "Sorry, I couldn't find any products matching your search."
                    
            elif action == "get_weather" and tool_output.get("success"):
                city = tool_output["city"]
                temp = tool_output["temperature"]
                condition = tool_output["condition"]
                response = f"The weather in {city} is {condition} with a temperature of {temp}°C"
                
            elif action == "get_user_profile" and tool_output.get("success"):
                name = tool_output["name"]
                points = tool_output["loyalty_points"]
                history = ", ".join(tool_output["purchase_history"])
                response = f"Profile for {name}:\n• Loyalty Points: {points}\n• Recent Purchases: {history}"
                
            elif action == "greet_user":
                greetings = ["Hello!", "Hi there!", "Good to see you!", "Welcome!"]
                response = greetings[len(state["conversation_history"]) % len(greetings)]
                
            elif action == "provide_help":
                response = "I can help you with:\n• Product search (try: 'find laptops')\n• Weather info (try: 'weather in London')\n• Your profile (try: 'show my profile')\n• General questions"
                
            elif action == "say_goodbye":
                response = "Goodbye! Have a great day! 👋"
                
            else:
                response = "I understand you're trying to communicate with me. How can I help you today?"
    
    except Exception as e:
        state["errors"].append(f"Response generation error: {str(e)}")
        response = "I encountered an issue generating a response. Please try again."
    
    state["final_response"] = response
    state["current_node"] = "response_generation"
    
    # Update conversation history
    state["conversation_history"].append({
        "user_input": user_input,
        "agent_response": response,
        "intent": intent,
        "timestamp": datetime.now().isoformat()
    })
    
    return state

def human_approval_node(state: AgentState) -> AgentState:
    """Node 6: Handle human approval (HITL)"""
    action = state["action"]
    confidence = state["confidence"]
    
    # In a real implementation, this would pause execution
    # and wait for human input. For demo, we auto-approve.
    
    print(f"🤔 Human Approval Required:")
    print(f"   Action: {action}")
    print(f"   Confidence: {confidence}")
    print(f"   Auto-approving for demo...")
    
    state["approval_granted"] = True  # Auto-approve for demo
    state["current_node"] = "human_approval"
    
    return state

def error_handling_node(state: AgentState) -> AgentState:
    """Node 7: Handle errors and retries"""
    errors = state["errors"]
    retry_count = state["retry_count"]
    
    if errors and retry_count < 3:
        state["retry_count"] += 1
        state["final_response"] = f"I encountered an issue (attempt {retry_count + 1}/3). Let me try again..."
        state["current_node"] = "error_handling"
        # Clear the last error to retry
        state["last_error"] = None
    else:
        state["final_response"] = "I'm having persistent issues. Please try a different request or contact support."
        state["current_node"] = "error_handling"
    
    return state

# ============================================================================
# CONDITIONAL ROUTING FUNCTIONS - Control flow between nodes
# ============================================================================

def route_after_intent_classification(state: AgentState) -> str:
    """Route based on intent confidence"""
    confidence = state["confidence"]
    
    if confidence < 0.5:
        return "error_handling"  # Low confidence
    elif state["requires_approval"]:
        return "human_approval"  # Need approval
    else:
        return "tool_execution"  # Proceed normally

def route_after_approval(state: AgentState) -> str:
    """Route after human approval"""
    if state["approval_granted"]:
        return "tool_execution"
    else:
        return "response_generation"  # Skip tools, generate rejection response

def route_after_tool_execution(state: AgentState) -> str:
    """Route after tool execution"""
    if state["last_error"] and state["retry_count"] < 3:
        return "error_handling"  # Retry
    else:
        return "response_generation"  # Generate response

def route_after_error_handling(state: AgentState) -> str:
    """Route after error handling"""
    if state["retry_count"] < 3 and not state["last_error"]:
        return "intent_classification"  # Retry from classification
    else:
        return "response_generation"  # Give up, generate error response

# ============================================================================
# LANGGRAPH AGENT BUILDER
# ============================================================================

def create_langgraph_agent(config: LangGraphConfig = None) -> StateGraph:
    """Create the complete LangGraph agent"""
    
    if config is None:
        config = LangGraphConfig()
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("input_processing", input_processing_node)
    workflow.add_node("intent_classification", intent_classification_node)
    workflow.add_node("decision_making", decision_making_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("error_handling", error_handling_node)
    
    # Define the flow with edges
    workflow.add_edge(START, "input_processing")
    workflow.add_edge("input_processing", "intent_classification")
    workflow.add_edge("intent_classification", "decision_making")
    
    # Conditional routing from decision making
    workflow.add_conditional_edges(
        "decision_making",
        route_after_intent_classification,
        {
            "tool_execution": "tool_execution",
            "human_approval": "human_approval", 
            "error_handling": "error_handling"
        }
    )
    
    # Conditional routing from human approval
    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation"
        }
    )
    
    # Conditional routing from tool execution
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool_execution,
        {
            "response_generation": "response_generation",
            "error_handling": "error_handling"
        }
    )
    
    # Conditional routing from error handling
    workflow.add_conditional_edges(
        "error_handling", 
        route_after_error_handling,
        {
            "intent_classification": "intent_classification",
            "response_generation": "response_generation"
        }
    )
    
    # End after response generation
    workflow.add_edge("response_generation", END)
    
    return workflow

# ============================================================================
# AGENT RUNNER WITH CHECKPOINTING
# ============================================================================

class LangGraphAgent:
    """Complete LangGraph Agent with all features"""
    
    def __init__(self, config: LangGraphConfig = None):
        self.config = config or LangGraphConfig()
        
        # Create workflow
        self.workflow = create_langgraph_agent(self.config)
        
        # Setup checkpointing for persistence
        self.memory = SqliteSaver.from_conn_string(self.config.checkpoint_db)
        
        # Compile with checkpointing
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        print("🕸️ LangGraph Agent initialized with full architecture!")
        print(f"📊 Checkpointing: {self.config.checkpoint_db}")
        print(f"🔄 Max retries: {self.config.max_retries}")
        print(f"⚡ Streaming: {self.config.enable_streaming}")
    
    def run(self, user_input: str, session_id: str = "default") -> str:
        """Run the agent synchronously"""
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "processed_input": "",
            "final_response": "",
            "intent": None,
            "confidence": 0.0,
            "action": None,
            "tool_calls": [],
            "tool_results": [],
            "conversation_history": [],
            "user_profile": {},
            "session_data": {},
            "current_node": "",
            "requires_approval": False,
            "approval_granted": False,
            "retry_count": 0,
            "errors": [],
            "last_error": None,
            "streaming_content": "",
            "is_streaming": False
        }
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            result = self.app.invoke(initial_state, config=config)
            return result["final_response"]
        except Exception as e:
            return f"Agent error: {str(e)}"
    
    async def run_async(self, user_input: str, session_id: str = "default") -> str:
        """Run the agent asynchronously"""
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "processed_input": "",
            "final_response": "",
            "intent": None,
            "confidence": 0.0,
            "action": None,
            "tool_calls": [],
            "tool_results": [],
            "conversation_history": [],
            "user_profile": {},
            "session_data": {},
            "current_node": "",
            "requires_approval": False,
            "approval_granted": False,
            "retry_count": 0,
            "errors": [],
            "last_error": None,
            "streaming_content": "",
            "is_streaming": False
        }
        
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            result = await self.app.ainvoke(initial_state, config=config)
            return result["final_response"]
        except Exception as e:
            return f"Agent error: {str(e)}"
    
    async def stream(self, user_input: str, session_id: str = "default"):
        """Stream responses in real-time"""
        initial_state = {
            "messages": [],
            "user_input": user_input,
            "processed_input": "",
            "final_response": "",
            "intent": None,
            "confidence": 0.0,
            "action": None,
            "tool_calls": [],
            "tool_results": [],
            "conversation_history": [],
            "user_profile": {},
            "session_data": {},
            "current_node": "",
            "requires_approval": False,
            "approval_granted": False,
            "retry_count": 0,
            "errors": [],
            "last_error": None,
            "streaming_content": "",
            "is_streaming": False
        }
        
        config = {"configurable": {"thread_id": session_id}}
        
        async for event in self.app.astream(initial_state, config=config):
            yield event
    
    def get_state(self, session_id: str = "default") -> dict:
        """Get current state for a session"""
        config = {"configurable": {"thread_id": session_id}}
        try:
            return self.app.get_state(config).values
        except:
            return {}
    
    def reset_session(self, session_id: str = "default"):
        """Reset a session"""
        # This would clear the checkpointed state for the session
        print(f"🔄 Session {session_id} reset (implementation depends on checkpointer)")

# ============================================================================
# DEMO APPLICATION
# ============================================================================

def demo_langgraph_agent():
    """Interactive demo of the full LangGraph agent"""
    print("🕸️ Full LangGraph AI Agent Demo")
    print("=" * 50)
    print("Features: Graph workflow, HITL, checkpointing, error handling")
    print("Try: 'find laptops', 'weather in Tokyo', 'show my profile', 'help'")
    print("Commands: 'state', 'reset', 'quit'")
    print()
    
    # Create agent
    config = LangGraphConfig()
    agent = LangGraphAgent(config)
    session_id = f"demo_{int(time.time())}"
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                response = agent.run("goodbye", session_id)
                print(f"🕸️ Agent: {response}")
                break
            elif user_input.lower() == 'state':
                state = agent.get_state(session_id)
                print(f"📊 Current State: {json.dumps(state, indent=2)}")
                continue
            elif user_input.lower() == 'reset':
                agent.reset_session(session_id)
                continue
            elif not user_input:
                continue
            
            # Run the agent
            response = agent.run(user_input, session_id)
            print(f"🕸️ Agent: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_langgraph_agent()
