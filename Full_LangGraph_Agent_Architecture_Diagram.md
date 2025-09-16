# **Full LangGraph Agent Architecture Diagram**

## **Visual Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CONFIGURATION                                      │
│   LangGraphConfig: OpenAI API, Model Settings, Retries, Streaming, Checkpoints │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────────┐
│                         LANGGRAPH AGENT                                        │
│                    (Workflow + Memory + Compiler)                              │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   AGENT STATE   │  │     NODES       │  │     EDGES       │
│   (TypedDict)   │◄─┤   (7 Nodes)     │─►│  (Conditional)  │
│                 │  │                 │  │                 │
│ • Input/Output  │  │ 1. Input Proc   │  │ • Route by      │
│ • Intent/Action │  │ 2. Intent Class │  │   Confidence    │
│ • Tool Results  │  │ 3. Decision     │  │ • Route by      │
│ • Context/Mem   │  │ 4. Tool Exec    │  │   Approval      │
│ • Flow Control  │  │ 5. Response Gen │  │ • Route by      │
│ • Error Handle  │  │ 6. Human Appr   │  │   Errors        │
│ • Streaming     │  │ 7. Error Handle │  │ • Route by      │
└─────────────────┘  └─────────────────┘  │   Retry Logic   │
         ▲                    │            └─────────────────┘
         │                    ▼                    ▲
         │           ┌────────────────┐            │
         │           │     TOOLS      │            │
         │           │  (3 Mock APIs) │            │
         │           │                │            │
         │           │ • Product      │            │
         │           │   Search       │            │
         │           │ • Weather API  │            │
         │           │ • User Profile │            │
         │           └────────────────┘            │
         │                    │                    │
┌────────┴────────┐          │           ┌────────┴────────┐
│  SQLITE MEMORY  │          │           │   INTERRUPTS    │
│  (Checkpoints)  │          │           │ (Human-in-Loop) │
│                 │          │           │                 │
│ • Session Data  │          │           │ • Approval Req  │
│ • Conversation  │          │           │ • Auto-approve  │
│ • State Persist │          │           │ • Confidence    │
└─────────────────┘          │           │   Threshold     │
         ▲                   │           └─────────────────┘
         │                   │                    ▲
         │                   ▼                    │
         │           ┌────────────────┐           │
         │           │ ERROR HANDLING │           │
         │           │  (Retry Logic) │           │
         │           │                │           │
         │           │ • Max 3 Retries│           │
         │           │ • Error Collect│           │
         │           │ • Graceful Deg │           │
         │           └────────────────┘           │
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    STREAMING    │
                    │  (Real-time)    │
                    │                 │
                    │ • Async Support │
                    │ • Event Stream  │
                    │ • Live Updates  │
                    └─────────────────┘
```

---

## **Detailed Flow Diagram**

```
START
  │
  ▼
┌─────────────────┐
│ INPUT PROCESSING│ ← User Input: "find laptops"
│                 │
│ • Clean input   │
│ • Detect sentiment
│ • Update session│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│INTENT CLASSIFY  │ ← Rule-based classification
│                 │
│ • Match keywords│
│ • Set confidence│
│ • Intent: search_products (0.8)
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ DECISION MAKING │ ← Map intent to action
│                 │
│ • Action: search_products
│ • Check sensitive: YES
│ • Requires approval: confidence < 0.8
└─────────┬───────┘
          │
          ▼
    ┌─────────────┐
    │ CONDITIONAL │ ← Route based on confidence
    │   ROUTING   │
    └─────┬───────┘
          │
    ┌─────▼─────┬─────────────┬──────────────┐
    │           │             │              │
    ▼           ▼             ▼              ▼
confidence   requires      has_error      normal
  < 0.5      approval        = true        flow
    │           │             │              │
    ▼           ▼             ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ ERROR   │ │ HUMAN   │ │ ERROR       │ │ TOOL        │
│HANDLING │ │APPROVAL │ │ HANDLING    │ │ EXECUTION   │
└─────────┘ └─────────┘ └─────────────┘ └─────┬───────┘
    │           │             │              │
    │           ▼             │              ▼
    │    ┌─────────────┐      │       ┌─────────────┐
    │    │ CONDITIONAL │      │       │   TOOLS     │
    │    │   ROUTING   │      │       │             │
    │    └─────┬───────┘      │       │ • search_   │
    │          │              │       │   products_ │
    │     ┌────▼────┐         │       │   tool()    │
    │     │approved?│         │       │ • Extract   │
    │     └────┬────┘         │       │   query     │
    │          │              │       │ • Return    │
    │      ┌───▼───┬──────┐   │       │   results   │
    │      │ YES   │  NO  │   │       └─────┬───────┘
    │      ▼       ▼      │   │             │
    │  ┌────────┐ ┌──────▼┐  │             ▼
    │  │ TOOL   │ │REJECT││  │      ┌─────────────┐
    │  │ EXEC   │ │RESPO ││  │      │ CONDITIONAL │
    │  └────────┘ │NSE  ││  │      │   ROUTING   │
    │             └──────┘│  │      └─────┬───────┘
    │                     │  │            │
    └─────────────────────┼──┼────────────┘
                          │  │       ┌────▼────┐
                          │  │       │has_error│
                          │  │       │retry<3? │
                          │  │       └────┬────┘
                          │  │            │
                          │  │       ┌────▼────┬─────────┐
                          │  │       │   YES   │   NO    │
                          │  │       ▼         ▼         │
                          │  │  ┌─────────┐ ┌─────────┐  │
                          │  │  │ ERROR   │ │RESPONSE │  │
                          │  │  │HANDLING │ │  GEN    │  │
                          │  │  └─────────┘ └─────────┘  │
                          │  │       │                   │
                          │  └───────┼───────────────────┘
                          │          │
                          ▼          ▼
                    ┌─────────────────────┐
                    │ RESPONSE GENERATION │ ← Generate natural language
                    │                     │
                    │ • Process tool results
                    │ • Format products list
                    │ • Update conversation
                    │ • Create final response
                    └─────────┬───────────┘
                              │
                              ▼
                            END
```

---

## **Component Breakdown**

### **1. Agent State (TypedDict)**

**Complete state management with 21 fields:**

```python
class AgentState(TypedDict):
    # Input/Output Layer
    messages: Annotated[List[Dict], add_messages]  # LangGraph message handling
    user_input: str                                # Raw user input
    processed_input: str                           # Cleaned input
    final_response: str                            # Generated response
    
    # Intelligence Layer
    intent: Optional[str]                          # Classified intent
    confidence: float                              # Classification confidence
    action: Optional[str]                          # Mapped action
    
    # Tool Integration Layer
    tool_calls: List[Dict[str, Any]]              # Tool invocations
    tool_results: List[Dict[str, Any]]            # Tool outputs
    
    # Memory & Context Layer
    conversation_history: List[Dict[str, Any]]     # Chat history
    user_profile: Dict[str, Any]                   # User data
    session_data: Dict[str, Any]                   # Session info
    
    # Flow Control Layer
    current_node: str                              # Current processing node
    requires_approval: bool                        # HITL flag
    approval_granted: bool                         # Approval status
    retry_count: int                               # Error retry counter
    
    # Error Management Layer
    errors: List[str]                              # Error collection
    last_error: Optional[str]                      # Most recent error
    
    # Streaming Layer
    streaming_content: str                         # Real-time content
    is_streaming: bool                             # Streaming flag
```

---

### **2. Processing Nodes (7 Specialized Functions)**

**Node 1: Input Processing**
- Clean and validate input
- Sentiment analysis (positive/negative/neutral)
- Session data updates

**Node 2: Intent Classification** 
- Rule-based pattern matching
- Confidence scoring (0.0-1.0)
- Intent categories: greeting, search_products, weather, user_profile, help, goodbye, question, general

**Node 3: Decision Making**
- Intent-to-action mapping
- Sensitivity analysis for approval requirements
- Action categories: greet_user, search_products, get_weather, get_user_profile, provide_help, say_goodbye, answer_question, general_chat

**Node 4: Tool Execution**
- Dynamic tool selection based on action
- Error handling with try/catch
- Result formatting and timestamping
- City extraction for weather queries

**Node 5: Response Generation**
- Natural language response creation
- Tool result formatting
- Product listings with pricing/ratings
- Weather information formatting
- Conversation history updates

**Node 6: Human Approval (HITL)**
- Confidence threshold checking
- Approval workflow (auto-approve in demo)
- Sensitive action gating

**Node 7: Error Handling**
- Retry logic (max 3 attempts)
- Error collection and reporting
- Graceful degradation
- Recovery path routing

---

### **3. Conditional Edge Routing (4 Route Functions)**

**Route 1: After Intent Classification**
```python
if confidence < 0.5:
    return "error_handling"      # Low confidence
elif requires_approval:
    return "human_approval"      # Need HITL
else:
    return "tool_execution"      # Normal flow
```

**Route 2: After Human Approval**
```python
if approval_granted:
    return "tool_execution"      # Proceed
else:
    return "response_generation" # Reject
```

**Route 3: After Tool Execution**
```python
if last_error and retry_count < 3:
    return "error_handling"      # Retry
else:
    return "response_generation" # Continue
```

**Route 4: After Error Handling**
```python
if retry_count < 3 and not last_error:
    return "intent_classification" # Retry from classification
else:
    return "response_generation"   # Give up gracefully
```

---

### **4. Tool Registry (3 Mock APIs)**

**Product Search Tool:**
- Mock product database (laptops, phones)
- Query matching and filtering
- Stock and pricing information
- Rating system

**Weather API Tool:**
- Mock weather data for major cities
- Temperature, condition, humidity
- Default fallback to London

**User Profile Tool:**
- Mock user data retrieval
- Loyalty points and purchase history
- Preference tracking

---

### **5. Memory & Checkpointing**

**SQLite-based persistence:**
- Session state storage
- Conversation history
- Automatic checkpointing after each node
- Session recovery and reset capabilities

**Features:**
- Thread-based session management
- State persistence across restarts
- Conversation continuity

---

### **6. Streaming & Execution Modes**

**Three execution modes:**
1. **Synchronous:** `agent.run(input, session_id)`
2. **Asynchronous:** `await agent.run_async(input, session_id)`
3. **Streaming:** `async for event in agent.stream(input, session_id)`

**Real-time capabilities:**
- Event streaming
- Live progress updates
- Intermediate result display

---

### **7. Configuration Management**

**LangGraphConfig dataclass:**
```python
@dataclass
class LangGraphConfig:
    # LLM Settings
    openai_api_key: str = ""
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500
    
    # Agent Settings
    max_retries: int = 3
    enable_streaming: bool = True
    enable_interrupts: bool = True
    
    # Persistence
    checkpoint_db: str = "agent_checkpoints.db"
```

---

## **Key Architecture Features**

### **🔄 Complete State Management**
- 21-field TypedDict with comprehensive data flow
- Persistent conversation history and session data
- Real-time state updates across all nodes

### **🧠 Intelligent Routing**
- 4 conditional routing functions
- Confidence-based decision making
- Error recovery and retry logic
- Human-in-the-loop integration

### **🛠️ Tool Integration**
- Dynamic tool selection based on intent
- Error handling for tool failures
- Result formatting and timestamping
- Extensible tool registry

### **💾 Persistent Memory**
- SQLite checkpointing for state persistence
- Session-based conversation tracking
- Automatic state recovery

### **⚡ Multiple Execution Modes**
- Synchronous, asynchronous, and streaming support
- Real-time progress updates
- Event-driven architecture

### **🔧 Production Ready**
- Comprehensive error handling
- Retry logic with limits
- Graceful degradation
- Configuration management

---

## **Execution Flow Example**

**User Input:** `"find laptops"`

1. **Input Processing:** Clean input, detect neutral sentiment
2. **Intent Classification:** Match "find" → search_products (confidence: 0.8)
3. **Decision Making:** Map to search_products action, requires_approval = False
4. **Route:** Confidence ≥ 0.5, no approval needed → Tool Execution
5. **Tool Execution:** Call search_products_tool("find laptops")
6. **Tool Result:** Return 3 laptop products with pricing/ratings
7. **Response Generation:** Format product list with details
8. **Update State:** Add to conversation history
9. **END:** Return formatted response

**Output:**
```
Found 3 products:
• MacBook Pro M3 - $1999 (⭐4.8) - 15 in stock
• Dell XPS 13 - $1299 (⭐4.5) - 8 in stock  
• ThinkPad X1 Carbon - $1599 (⭐4.6) - 12 in stock
```

This architecture provides a complete, production-ready LangGraph agent with sophisticated state management, intelligent routing, tool integration, and robust error handling.
