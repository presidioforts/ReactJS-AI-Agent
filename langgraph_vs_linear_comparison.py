"""
Comparison: Linear Agent vs LangGraph Agent
Shows the architectural differences
"""

# ============================================================================
# CURRENT APPROACH: Linear Agent
# ============================================================================

class LinearAgent:
    """Our current enhanced agent - linear flow"""
    
    def run(self, user_input: str) -> str:
        # Linear sequence - one after another
        processed_input = self._process_input(user_input)        # Step 1
        intent = self._recognize_intent(processed_input)         # Step 2
        self._update_memory(user_input, intent, processed_input) # Step 3
        action = self._make_decision(intent, processed_input)    # Step 4
        result = self._execute_tool(action, processed_input)     # Step 5
        response = self._generate_response(result, intent)       # Step 6
        self._update_state(intent, action, processed_input)     # Step 7
        final_output = self._deliver_output(response)           # Step 8
        self._learn_from_interaction(user_input, intent, response) # Step 9
        return final_output

# ============================================================================
# LANGGRAPH APPROACH: Graph-based Agent
# ============================================================================

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END, START

class AgentState(TypedDict):
    """State that flows through the graph"""
    user_input: str
    processed_input: str
    intent: str
    confidence: float
    tool_result: dict
    response: str
    requires_approval: bool
    error: str

def process_input_node(state: AgentState) -> AgentState:
    """Node: Process user input"""
    state["processed_input"] = state["user_input"].strip().lower()
    return state

def classify_intent_node(state: AgentState) -> AgentState:
    """Node: Classify intent using LLM"""
    # LLM call here
    if "laptop" in state["processed_input"]:
        state["intent"] = "search_products"
        state["confidence"] = 0.9
    elif "weather" in state["processed_input"]:
        state["intent"] = "weather"
        state["confidence"] = 0.8
    else:
        state["intent"] = "general"
        state["confidence"] = 0.5
    return state

def execute_tool_node(state: AgentState) -> AgentState:
    """Node: Execute appropriate tool"""
    intent = state["intent"]
    
    if intent == "search_products":
        # Mock product API
        state["tool_result"] = {
            "products": [
                {"name": "MacBook Pro", "price": 1999},
                {"name": "Dell XPS", "price": 1299}
            ]
        }
    elif intent == "weather":
        # Mock weather API  
        state["tool_result"] = {
            "temperature": 22,
            "condition": "sunny"
        }
    else:
        state["tool_result"] = {"message": "General response"}
    
    return state

def generate_response_node(state: AgentState) -> AgentState:
    """Node: Generate response using LLM"""
    tool_result = state["tool_result"]
    intent = state["intent"]
    
    if intent == "search_products":
        products = tool_result["products"]
        state["response"] = f"Found {len(products)} laptops: "
        for p in products:
            state["response"] += f"{p['name']} (${p['price']}), "
    elif intent == "weather":
        state["response"] = f"It's {tool_result['condition']} and {tool_result['temperature']}°C"
    else:
        state["response"] = "I can help you with that!"
    
    return state

def approval_node(state: AgentState) -> AgentState:
    """Node: Handle human approval (HITL)"""
    # In real implementation, this would pause and wait for human input
    state["requires_approval"] = False  # Auto-approve for demo
    return state

# Conditional routing functions
def route_after_classification(state: AgentState) -> str:
    """Route based on confidence"""
    if state["confidence"] < 0.6:
        return "approval_needed"
    else:
        return "execute_tool"

def route_after_approval(state: AgentState) -> str:
    """Route after approval"""
    if state["requires_approval"]:
        return "approval_node"  # Loop back for more approval
    else:
        return "generate_response"

def create_langgraph_agent():
    """Create LangGraph-based agent"""
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("process_input", process_input_node)
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("approval_node", approval_node)
    
    # Add edges (flow control)
    workflow.add_edge(START, "process_input")
    workflow.add_edge("process_input", "classify_intent")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {
            "execute_tool": "execute_tool",
            "approval_needed": "approval_node"
        }
    )
    
    workflow.add_edge("execute_tool", "generate_response")
    workflow.add_edge("generate_response", END)
    
    workflow.add_conditional_edges(
        "approval_node",
        route_after_approval,
        {
            "generate_response": "generate_response",
            "approval_node": "approval_node"  # Can loop
        }
    )
    
    return workflow.compile()

# ============================================================================
# COMPARISON DEMO
# ============================================================================

def compare_approaches():
    """Compare both approaches"""
    
    print("🔄 LINEAR AGENT (Current):")
    print("Input → Process → Intent → Decision → Tool → Response")
    print("✅ Simple, fast, predictable")
    print("❌ No branching, no interrupts, no complex flows")
    print()
    
    print("🕸️ LANGGRAPH AGENT:")
    print("Input → Process → Intent → [Branch based on confidence]")
    print("                     ↓")
    print("              Tool → Response")
    print("                     ↓")
    print("              [Human approval if needed]")
    print("✅ Complex flows, branching, interrupts, streaming")
    print("❌ More complex to build and debug")
    print()
    
    # Test input
    test_input = "Find me a laptop"
    
    print(f"🧪 Test Input: '{test_input}'")
    print()
    
    # LangGraph approach
    print("🕸️ LangGraph Flow:")
    langgraph_agent = create_langgraph_agent()
    
    initial_state = {
        "user_input": test_input,
        "processed_input": "",
        "intent": "",
        "confidence": 0.0,
        "tool_result": {},
        "response": "",
        "requires_approval": False,
        "error": ""
    }
    
    result = langgraph_agent.invoke(initial_state)
    print(f"Result: {result['response']}")

if __name__ == "__main__":
    compare_approaches()
