"""
LangGraph Skeleton Code - All 10 Building Blocks
A complete template covering all essential components
"""

from typing import TypedDict, List, Optional, Literal, Dict, Any, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import operator

# ============================================================================
# 1. STATE SCHEMA - Define what data flows through the agent
# ============================================================================

class AgentState(TypedDict):
    """Main state that flows through all nodes"""
    # Core conversation
    messages: Annotated[List[Dict], add_messages]
    user_input: str
    agent_response: str
    
    # Processing state
    current_step: str
    intent: Optional[str]
    confidence: float
    
    # Data collection
    collected_data: Dict[str, Any]
    missing_fields: List[str]
    
    # System state
    errors: List[str]
    retry_count: int
    requires_human: bool

# ============================================================================
# LLM INTEGRATION - Setup language models
# ============================================================================

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000
)

# System prompts for different tasks
INTENT_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an intent classifier. Analyze the user input and classify it into one of these categories:
    - search: User wants to find something
    - help: User needs assistance
    - general: General conversation
    
    Respond with JSON: {"intent": "category", "confidence": 0.0-1.0}"""),
    ("human", "{user_input}")
])

RESPONSE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant. Generate a clear, concise response based on:
    - User intent: {intent}
    - Collected data: {collected_data}
    - Context: {context}
    
    Be helpful and professional."""),
    ("human", "{user_input}")
])

# ============================================================================
# 4. TOOLS - External functions the agent can call
# ============================================================================

def search_database(query: str) -> Dict:
    """Tool to search external database"""
    # Simulate database search
    return {"results": f"Found results for: {query}", "count": 3}

def send_notification(message: str, recipient: str) -> Dict:
    """Tool to send notifications"""
    # Simulate sending notification
    return {"status": "sent", "message": message, "to": recipient}

def validate_data(data: Dict) -> Dict:
    """Tool to validate collected data"""
    # Simulate data validation
    return {"valid": True, "errors": []}

# Define tools list
tools = [search_database, send_notification, validate_data]
tool_node = ToolNode(tools)

# ============================================================================
# 2. NODES - Individual processing functions
# ============================================================================

def classify_intent(state: AgentState) -> AgentState:
    """Node: Classify user intent using LLM"""
    user_input = state["user_input"]
    
    try:
        # Use LLM for intent classification
        chain = INTENT_CLASSIFICATION_PROMPT | llm
        response = chain.invoke({"user_input": user_input})
        
        # Parse LLM response (simplified - should use proper JSON parsing)
        content = response.content
        if "search" in content.lower():
            intent = "search"
            confidence = 0.9
        elif "help" in content.lower():
            intent = "help"
            confidence = 0.8
        else:
            intent = "general"
            confidence = 0.6
            
    except Exception as e:
        # Fallback to simple rule-based classification
        if "search" in user_input.lower():
            intent = "search"
            confidence = 0.7
        elif "help" in user_input.lower():
            intent = "help"
            confidence = 0.7
        else:
            intent = "general"
            confidence = 0.5
        
        state["errors"].append(f"LLM classification failed: {e}")
    
    state["intent"] = intent
    state["confidence"] = confidence
    state["current_step"] = "intent_classified"
    
    return state

def collect_information(state: AgentState) -> AgentState:
    """Node: Collect required information"""
    intent = state["intent"]
    
    # Determine what info we need based on intent
    if intent == "search":
        required_fields = ["search_query", "category"]
    elif intent == "help":
        required_fields = ["problem_type"]
    else:
        required_fields = []
    
    # Check what's missing
    collected = state["collected_data"]
    missing = [field for field in required_fields if field not in collected]
    
    state["missing_fields"] = missing
    state["current_step"] = "info_collected"
    
    return state

def process_request(state: AgentState) -> AgentState:
    """Node: Process the user request"""
    intent = state["intent"]
    
    if intent == "search":
        # Call search tool
        query = state["collected_data"].get("search_query", "")
        results = search_database(query)
        response = f"Search results: {results['results']}"
    elif intent == "help":
        response = "I'm here to help! What specific issue are you facing?"
    else:
        response = "I understand you need assistance. How can I help you today?"
    
    state["agent_response"] = response
    state["current_step"] = "request_processed"
    
    return state

def generate_response(state: AgentState) -> AgentState:
    """Node: Generate final response using LLM"""
    user_input = state["user_input"]
    intent = state["intent"]
    collected_data = state["collected_data"]
    
    try:
        # Use LLM for response generation
        chain = RESPONSE_GENERATION_PROMPT | llm
        response = chain.invoke({
            "user_input": user_input,
            "intent": intent,
            "collected_data": str(collected_data),
            "context": f"Current step: {state['current_step']}"
        })
        
        formatted_response = response.content
        
    except Exception as e:
        # Fallback response
        formatted_response = f"I understand you need help with {intent}. Let me assist you."
        state["errors"].append(f"LLM response generation failed: {e}")
    
    state["agent_response"] = formatted_response
    state["current_step"] = "response_generated"
    
    return state

def handle_error(state: AgentState) -> AgentState:
    """Node: Handle errors and retries"""
    errors = state["errors"]
    retry_count = state["retry_count"]
    
    if retry_count < 3:
        state["retry_count"] += 1
        state["agent_response"] = "I encountered an issue. Let me try again..."
        state["current_step"] = "retrying"
    else:
        state["requires_human"] = True
        state["agent_response"] = "I need to escalate this to a human agent."
        state["current_step"] = "escalated"
    
    return state

# ============================================================================
# 3. EDGES - Routing logic between nodes
# ============================================================================

def route_after_intent(state: AgentState) -> str:
    """Conditional edge: Route based on intent classification"""
    confidence = state["confidence"]
    
    if confidence < 0.5:
        return "handle_error"
    elif state["missing_fields"]:
        return "collect_information"
    else:
        return "process_request"

def route_after_collection(state: AgentState) -> str:
    """Conditional edge: Route after information collection"""
    if state["missing_fields"]:
        return "collect_information"  # Still missing info
    else:
        return "process_request"

def route_after_processing(state: AgentState) -> str:
    """Conditional edge: Route after request processing"""
    if state["errors"]:
        return "handle_error"
    else:
        return "generate_response"

def route_after_error(state: AgentState) -> str:
    """Conditional edge: Route after error handling"""
    if state["requires_human"]:
        return END
    else:
        return "classify_intent"  # Retry from beginning

# ============================================================================
# 7. INTERRUPTS - Human-in-the-loop breakpoints
# ============================================================================

def should_interrupt_before_processing(state: AgentState) -> bool:
    """Interrupt: Check if human approval needed before processing"""
    intent = state["intent"]
    # Interrupt for sensitive operations
    return intent in ["delete", "modify", "purchase"]

def should_interrupt_after_error(state: AgentState) -> bool:
    """Interrupt: Check if human needed after error"""
    return state["requires_human"]

# ============================================================================
# 6. GRAPH COMPILER - Build the executable workflow
# ============================================================================

def create_agent():
    """Create and compile the agent graph"""
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("collect_information", collect_information)
    workflow.add_node("process_request", process_request)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("handle_error", handle_error)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.add_edge(START, "classify_intent")
    workflow.add_conditional_edges("classify_intent", route_after_intent)
    workflow.add_conditional_edges("collect_information", route_after_collection)
    workflow.add_conditional_edges("process_request", route_after_processing)
    workflow.add_edge("generate_response", END)
    workflow.add_conditional_edges("handle_error", route_after_error)
    
    # Add interrupts
    workflow.add_conditional_edges(
        "process_request",
        should_interrupt_before_processing,
        {True: "__interrupt__", False: "generate_response"}
    )
    
    return workflow

# ============================================================================
# 5. MEMORY/CHECKPOINTER - Persistence layer
# ============================================================================

def setup_memory():
    """Setup persistent memory for the agent"""
    # SQLite checkpointer for development
    memory = SqliteSaver.from_conn_string(":memory:")
    return memory

# ============================================================================
# 10. CONFIGURATION - Runtime settings
# ============================================================================

class AgentConfig:
    """Configuration for the agent"""
    
    # LLM settings
    MODEL_NAME = "gpt-3.5-turbo"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    OPENAI_API_KEY = "your-api-key-here"  # Set via environment variable
    
    # Alternative LLM options
    USE_AZURE_OPENAI = False
    AZURE_ENDPOINT = "https://your-resource.openai.azure.com/"
    AZURE_API_VERSION = "2023-12-01-preview"
    
    # Local LLM options
    USE_LOCAL_LLM = False
    LOCAL_MODEL_PATH = "path/to/local/model"
    
    # Workflow settings
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    # Feature flags
    ENABLE_VOICE = False
    ENABLE_STREAMING = True
    REQUIRE_CONFIRMATION = True
    
    # Environment
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

# ============================================================================
# 8. ERROR HANDLING - Comprehensive error management
# ============================================================================

class AgentError(Exception):
    """Custom exception for agent errors"""
    pass

def with_error_handling(func):
    """Decorator to add error handling to nodes"""
    def wrapper(state: AgentState):
        try:
            return func(state)
        except Exception as e:
            state["errors"].append(str(e))
            state["current_step"] = "error_occurred"
            return state
    return wrapper

# ============================================================================
# 9. STREAMING - Real-time response delivery
# ============================================================================

async def stream_response(app, config, input_data):
    """Stream responses in real-time"""
    async for event in app.astream(input_data, config=config):
        # Yield intermediate results
        if "agent_response" in event:
            yield event["agent_response"]

async def async_invoke_agent(app, input_data, config):
    """Async invocation of the agent"""
    result = await app.ainvoke(input_data, config=config)
    return result

# ============================================================================
# MAIN APPLICATION - Putting it all together
# ============================================================================

def main():
    """Main function to run the agent"""
    
    # Setup components
    memory = setup_memory()
    workflow = create_agent()
    
    # Compile the agent
    app = workflow.compile(checkpointer=memory)
    
    # Configuration
    config = {
        "configurable": {
            "thread_id": "user_123",
            "model": AgentConfig.MODEL_NAME,
            "temperature": AgentConfig.TEMPERATURE
        }
    }
    
    # Initial state
    initial_state = {
        "messages": [],
        "user_input": "I need help searching for something",
        "agent_response": "",
        "current_step": "starting",
        "intent": None,
        "confidence": 0.0,
        "collected_data": {},
        "missing_fields": [],
        "errors": [],
        "retry_count": 0,
        "requires_human": False
    }
    
    # Run the agent (synchronous)
    try:
        result = app.invoke(initial_state, config=config)
        print(f"Final response: {result['agent_response']}")
        print(f"Final step: {result['current_step']}")
        
    except Exception as e:
        print(f"Agent error: {e}")

async def main_async():
    """Async version of main function"""
    
    # Setup components
    memory = setup_memory()
    workflow = create_agent()
    app = workflow.compile(checkpointer=memory)
    
    config = {
        "configurable": {
            "thread_id": "user_123",
            "model": AgentConfig.MODEL_NAME,
            "temperature": AgentConfig.TEMPERATURE
        }
    }
    
    initial_state = {
        "messages": [],
        "user_input": "I need help searching for something",
        "agent_response": "",
        "current_step": "starting",
        "intent": None,
        "confidence": 0.0,
        "collected_data": {},
        "missing_fields": [],
        "errors": [],
        "retry_count": 0,
        "requires_human": False
    }
    
    # Run the agent (asynchronous)
    try:
        result = await app.ainvoke(initial_state, config=config)
        print(f"Async Final response: {result['agent_response']}")
        print(f"Async Final step: {result['current_step']}")
        
    except Exception as e:
        print(f"Async Agent error: {e}")

if __name__ == "__main__":
    main()

# ============================================================================
# LLM SETUP HELPERS
# ============================================================================

def setup_llm(config: AgentConfig = AgentConfig()):
    """Setup LLM based on configuration"""
    if config.USE_AZURE_OPENAI:
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=config.AZURE_ENDPOINT,
            api_version=config.AZURE_API_VERSION,
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )
    elif config.USE_LOCAL_LLM:
        from langchain_community.llms import Ollama
        return Ollama(model=config.LOCAL_MODEL_PATH)
    else:
        return ChatOpenAI(
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Synchronous Invocation
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key-here"

app = create_agent().compile(checkpointer=setup_memory())
result = app.invoke({"user_input": "Search for laptops"})
print(result["agent_response"])
```

Example 1b: Async Invocation
```python
import asyncio

async def run_agent():
    app = create_agent().compile(checkpointer=setup_memory())
    result = await app.ainvoke({"user_input": "Search for laptops"})
    print(result["agent_response"])

asyncio.run(run_agent())
```

Example 2: With Custom LLM Configuration
```python
config = AgentConfig()
config.MODEL_NAME = "gpt-4"
config.TEMPERATURE = 0.3

llm = setup_llm(config)
# Use custom LLM in your nodes
```

Example 3: Azure OpenAI
```python
config = AgentConfig()
config.USE_AZURE_OPENAI = True
config.AZURE_ENDPOINT = "https://your-resource.openai.azure.com/"

llm = setup_llm(config)
```

Example 4: Local LLM (Ollama)
```python
config = AgentConfig()
config.USE_LOCAL_LLM = True
config.LOCAL_MODEL_PATH = "llama2"

llm = setup_llm(config)
```

Example 5: Streaming with LLM
```python
async for response in stream_response(app, config, input_data):
    print(response)
```
"""
