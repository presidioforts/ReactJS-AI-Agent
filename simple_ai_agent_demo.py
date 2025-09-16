"""
Simple AI Agent Demo - 10 Core Components
A working demonstration of basic AI agent functionality
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class SimpleAIAgent:
    """A basic AI agent implementing 10 core components"""
    
    def __init__(self):
        # 3. Context Memory - Store conversation history
        self.memory = []
        
        # 7. State Management - Track current state
        self.state = {
            "current_intent": None,
            "user_name": None,
            "conversation_count": 0,
            "last_action": None
        }
        
        # Simple knowledge base for responses
        self.knowledge = {
            "greeting": ["Hello!", "Hi there!", "Good to see you!"],
            "weather": "I don't have real weather data, but it's probably nice outside!",
            "time": "Let me check the time for you.",
            "help": "I can help with greetings, time, weather, or just chat!",
            "goodbye": ["Goodbye!", "See you later!", "Take care!"]
        }
    
    def run(self, user_input: str) -> str:
        """Main agent loop implementing all 10 components"""
        
        # 1. Input Processing - Clean and prepare input
        processed_input = self._process_input(user_input)
        
        # 2. Intent Recognition - Understand what user wants
        intent = self._recognize_intent(processed_input)
        
        # 3. Context Memory - Add to conversation history
        self._update_memory(user_input, intent)
        
        # 4. Decision Making - Choose action based on intent
        action = self._make_decision(intent, processed_input)
        
        # 5. Tool Execution - Execute chosen action
        result = self._execute_tool(action, processed_input)
        
        # 6. Response Generation - Create user-friendly response
        response = self._generate_response(result, intent)
        
        # 7. State Management - Update agent state
        self._update_state(intent, action)
        
        # 8. Error Handling - Handle any issues (built into each method)
        
        # 9. Output Delivery - Format and return response
        final_output = self._deliver_output(response)
        
        # 10. Learning/Feedback - Simple learning from interaction
        self._learn_from_interaction(user_input, intent, response)
        
        return final_output
    
    # ========================================================================
    # 1. INPUT PROCESSING
    # ========================================================================
    def _process_input(self, user_input: str) -> str:
        """Clean and normalize user input"""
        try:
            # Basic cleaning
            processed = user_input.strip().lower()
            return processed
        except Exception as e:
            print(f"Input processing error: {e}")
            return user_input.lower()
    
    # ========================================================================
    # 2. INTENT RECOGNITION
    # ========================================================================
    def _recognize_intent(self, processed_input: str) -> str:
        """Simple rule-based intent recognition"""
        try:
            # Basic intent patterns
            if any(word in processed_input for word in ["hello", "hi", "hey"]):
                return "greeting"
            elif any(word in processed_input for word in ["weather", "rain", "sunny"]):
                return "weather"
            elif any(word in processed_input for word in ["time", "clock", "hour"]):
                return "time"
            elif any(word in processed_input for word in ["help", "assist", "support"]):
                return "help"
            elif any(word in processed_input for word in ["bye", "goodbye", "exit"]):
                return "goodbye"
            else:
                return "general"
        except Exception as e:
            print(f"Intent recognition error: {e}")
            return "general"
    
    # ========================================================================
    # 3. CONTEXT MEMORY
    # ========================================================================
    def _update_memory(self, user_input: str, intent: str):
        """Store conversation in memory"""
        try:
            memory_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "intent": intent,
                "conversation_id": len(self.memory) + 1
            }
            self.memory.append(memory_entry)
            
            # Keep only last 10 interactions
            if len(self.memory) > 10:
                self.memory.pop(0)
        except Exception as e:
            print(f"Memory update error: {e}")
    
    # ========================================================================
    # 4. DECISION MAKING
    # ========================================================================
    def _make_decision(self, intent: str, processed_input: str) -> str:
        """Decide what action to take based on intent"""
        try:
            action_map = {
                "greeting": "greet_user",
                "weather": "get_weather",
                "time": "get_time",
                "help": "provide_help",
                "goodbye": "say_goodbye",
                "general": "general_chat"
            }
            return action_map.get(intent, "general_chat")
        except Exception as e:
            print(f"Decision making error: {e}")
            return "general_chat"
    
    # ========================================================================
    # 5. TOOL EXECUTION
    # ========================================================================
    def _execute_tool(self, action: str, processed_input: str) -> Dict[str, Any]:
        """Execute the chosen action/tool"""
        try:
            if action == "greet_user":
                return {"type": "greeting", "data": self.knowledge["greeting"][0]}
            
            elif action == "get_weather":
                return {"type": "weather", "data": self.knowledge["weather"]}
            
            elif action == "get_time":
                current_time = datetime.now().strftime("%H:%M:%S")
                return {"type": "time", "data": f"Current time is {current_time}"}
            
            elif action == "provide_help":
                return {"type": "help", "data": self.knowledge["help"]}
            
            elif action == "say_goodbye":
                return {"type": "goodbye", "data": self.knowledge["goodbye"][0]}
            
            else:
                return {"type": "general", "data": "I understand you're saying something, but I'm not sure how to help with that specific request."}
        
        except Exception as e:
            print(f"Tool execution error: {e}")
            return {"type": "error", "data": "I encountered an issue processing your request."}
    
    # ========================================================================
    # 6. RESPONSE GENERATION
    # ========================================================================
    def _generate_response(self, result: Dict[str, Any], intent: str) -> str:
        """Generate user-friendly response"""
        try:
            response_data = result.get("data", "I'm not sure how to respond to that.")
            
            # Add context based on conversation history
            if len(self.memory) > 1:
                if intent == "greeting" and self.state.get("user_name"):
                    response_data = f"Hello again, {self.state['user_name']}!"
                elif intent == "general":
                    response_data += " Is there anything specific I can help you with?"
            
            return response_data
        
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm having trouble generating a response right now."
    
    # ========================================================================
    # 7. STATE MANAGEMENT
    # ========================================================================
    def _update_state(self, intent: str, action: str):
        """Update agent's internal state"""
        try:
            self.state["current_intent"] = intent
            self.state["last_action"] = action
            self.state["conversation_count"] += 1
            
            # Simple name extraction
            if intent == "greeting" and len(self.memory) > 0:
                last_input = self.memory[-1]["user_input"]
                words = last_input.split()
                if "my name is" in last_input:
                    name_index = words.index("is") + 1
                    if name_index < len(words):
                        self.state["user_name"] = words[name_index].capitalize()
        
        except Exception as e:
            print(f"State management error: {e}")
    
    # ========================================================================
    # 8. ERROR HANDLING (built into each method above)
    # ========================================================================
    
    # ========================================================================
    # 9. OUTPUT DELIVERY
    # ========================================================================
    def _deliver_output(self, response: str) -> str:
        """Format and prepare final output"""
        try:
            # Add some personality and formatting
            formatted_response = f"🤖 Agent: {response}"
            return formatted_response
        except Exception as e:
            print(f"Output delivery error: {e}")
            return f"🤖 Agent: {response}"
    
    # ========================================================================
    # 10. LEARNING/FEEDBACK
    # ========================================================================
    def _learn_from_interaction(self, user_input: str, intent: str, response: str):
        """Simple learning mechanism"""
        try:
            # Track interaction patterns
            if not hasattr(self, 'learning_data'):
                self.learning_data = {}
            
            if intent not in self.learning_data:
                self.learning_data[intent] = {"count": 0, "examples": []}
            
            self.learning_data[intent]["count"] += 1
            self.learning_data[intent]["examples"].append(user_input)
            
            # Keep only recent examples
            if len(self.learning_data[intent]["examples"]) > 5:
                self.learning_data[intent]["examples"].pop(0)
        
        except Exception as e:
            print(f"Learning error: {e}")
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "conversations": self.state["conversation_count"],
            "memory_size": len(self.memory),
            "current_state": self.state,
            "learning_data": getattr(self, 'learning_data', {})
        }
    
    def reset(self):
        """Reset agent state"""
        self.memory.clear()
        self.state = {
            "current_intent": None,
            "user_name": None,
            "conversation_count": 0,
            "last_action": None
        }

# ============================================================================
# DEMO APPLICATION
# ============================================================================

def run_demo():
    """Interactive demo of the AI agent"""
    print("🤖 Simple AI Agent Demo")
    print("=" * 50)
    print("Try saying: hello, what's the weather, what time is it, help, or goodbye")
    print("Type 'stats' to see agent statistics, 'reset' to reset, 'quit' to exit")
    print()
    
    agent = SimpleAIAgent()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'stats':
                stats = agent.get_stats()
                print(f"📊 Agent Stats: {json.dumps(stats, indent=2)}")
                continue
            elif user_input.lower() == 'reset':
                agent.reset()
                print("🔄 Agent reset!")
                continue
            elif not user_input:
                continue
            
            # Run the agent
            response = agent.run(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# ============================================================================
# AUTOMATED TEST
# ============================================================================

def run_tests():
    """Run automated tests of all 10 components"""
    print("🧪 Testing AI Agent Components...")
    
    agent = SimpleAIAgent()
    
    test_cases = [
        ("hello", "greeting"),
        ("what's the weather like?", "weather"),
        ("what time is it?", "time"),
        ("help me", "help"),
        ("goodbye", "goodbye"),
        ("random text", "general")
    ]
    
    for user_input, expected_intent in test_cases:
        print(f"\nTest: '{user_input}'")
        response = agent.run(user_input)
        print(f"Response: {response}")
        
        # Verify intent was recognized
        actual_intent = agent.state["current_intent"]
        status = "✅" if actual_intent == expected_intent else "❌"
        print(f"Intent: {actual_intent} {status}")
    
    print(f"\n📊 Final Stats:")
    stats = agent.get_stats()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    print("Choose mode:")
    print("1. Interactive Demo")
    print("2. Automated Tests")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        run_tests()
    else:
        run_demo()
