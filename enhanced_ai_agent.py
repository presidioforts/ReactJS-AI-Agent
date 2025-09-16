"""
Enhanced AI Agent - With Real LLM Integration
Building on the 10 core components with actual AI capabilities
"""

import json
import time
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Try to import OpenAI - graceful fallback if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("OpenAI not installed. Run: pip install openai")

@dataclass
class AgentConfig:
    """Configuration for the enhanced agent"""
    openai_api_key: str = ""
    weather_api_key: str = ""  # Get from openweathermap.org
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 150
    use_llm: bool = True

class EnhancedAIAgent:
    """Enhanced AI agent with real LLM and API integration"""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
        # Initialize OpenAI client
        self.openai_client = None
        if HAS_OPENAI and self.config.openai_api_key:
            self.openai_client = OpenAI(api_key=self.config.openai_api_key)
        
        # 3. Context Memory - Enhanced with more details
        self.memory = []
        
        # 7. State Management - Enhanced state tracking
        self.state = {
            "current_intent": None,
            "user_name": None,
            "conversation_count": 0,
            "last_action": None,
            "user_location": None,
            "preferences": {},
            "session_start": datetime.now().isoformat()
        }
        
        # Enhanced knowledge base
        self.knowledge = {
            "greeting": ["Hello!", "Hi there!", "Good to see you!", "Welcome!"],
            "help": "I can help with weather, time, general questions, or just chat! I use AI to understand you better.",
            "goodbye": ["Goodbye!", "See you later!", "Take care!", "Have a great day!"],
            "capabilities": "I can check weather, tell time, answer questions using AI, and learn from our conversations."
        }
    
    def run(self, user_input: str) -> str:
        """Enhanced agent loop with LLM integration"""
        
        # 1. Input Processing - Enhanced cleaning
        processed_input = self._process_input(user_input)
        
        # 2. Intent Recognition - LLM-powered or rule-based fallback
        intent = self._recognize_intent_llm(processed_input) if self.config.use_llm else self._recognize_intent_rules(processed_input)
        
        # 3. Context Memory - Enhanced memory with sentiment
        self._update_memory(user_input, intent, processed_input)
        
        # 4. Decision Making - Enhanced with context awareness
        action = self._make_decision(intent, processed_input)
        
        # 5. Tool Execution - Enhanced with real APIs
        result = self._execute_tool(action, processed_input)
        
        # 6. Response Generation - LLM-powered responses
        response = self._generate_response_llm(result, intent, processed_input) if self.config.use_llm else self._generate_response_simple(result, intent)
        
        # 7. State Management - Enhanced state updates
        self._update_state(intent, action, processed_input)
        
        # 8. Error Handling - Built into each method
        
        # 9. Output Delivery - Enhanced formatting
        final_output = self._deliver_output(response)
        
        # 10. Learning/Feedback - Enhanced learning with patterns
        self._learn_from_interaction(user_input, intent, response)
        
        return final_output
    
    # ========================================================================
    # 1. ENHANCED INPUT PROCESSING
    # ========================================================================
    def _process_input(self, user_input: str) -> str:
        """Enhanced input processing with better cleaning"""
        try:
            # Remove extra whitespace
            processed = user_input.strip()
            
            # Basic profanity filter (simple example)
            if any(word in processed.lower() for word in ["bad", "terrible"]):
                self.state["user_sentiment"] = "negative"
            elif any(word in processed.lower() for word in ["good", "great", "awesome"]):
                self.state["user_sentiment"] = "positive"
            else:
                self.state["user_sentiment"] = "neutral"
            
            return processed
        except Exception as e:
            print(f"Input processing error: {e}")
            return user_input
    
    # ========================================================================
    # 2. ENHANCED INTENT RECOGNITION
    # ========================================================================
    def _recognize_intent_llm(self, processed_input: str) -> str:
        """LLM-powered intent recognition"""
        if not self.openai_client:
            return self._recognize_intent_rules(processed_input)
        
        try:
            prompt = f"""Classify the user's intent from this message: "{processed_input}"

Choose from these categories:
- greeting: hello, hi, good morning
- weather: asking about weather conditions
- time: asking for current time
- location: asking about places or locations
- help: asking for assistance or capabilities
- goodbye: farewell messages
- question: general questions
- general: everything else

Respond with just the category name."""

            response = self.openai_client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate intent
            valid_intents = ["greeting", "weather", "time", "location", "help", "goodbye", "question", "general"]
            return intent if intent in valid_intents else "general"
            
        except Exception as e:
            print(f"LLM intent recognition error: {e}")
            return self._recognize_intent_rules(processed_input)
    
    def _recognize_intent_rules(self, processed_input: str) -> str:
        """Fallback rule-based intent recognition"""
        try:
            input_lower = processed_input.lower()
            
            if any(word in input_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
                return "greeting"
            elif any(word in input_lower for word in ["weather", "rain", "sunny", "temperature", "forecast"]):
                return "weather"
            elif any(word in input_lower for word in ["time", "clock", "hour", "what time"]):
                return "time"
            elif any(word in input_lower for word in ["search", "find", "product", "buy", "laptop", "phone"]):
                return "search_products"
            elif any(word in input_lower for word in ["profile", "account", "my info", "user"]):
                return "get_user_info"
            elif any(word in input_lower for word in ["where", "location", "address", "place"]):
                return "location"
            elif any(word in input_lower for word in ["help", "assist", "support", "what can you do"]):
                return "help"
            elif any(word in input_lower for word in ["bye", "goodbye", "exit", "quit"]):
                return "goodbye"
            elif "?" in processed_input:
                return "question"
            else:
                return "general"
        except Exception as e:
            print(f"Rule-based intent recognition error: {e}")
            return "general"
    
    # ========================================================================
    # 3. ENHANCED CONTEXT MEMORY
    # ========================================================================
    def _update_memory(self, user_input: str, intent: str, processed_input: str):
        """Enhanced memory with more context"""
        try:
            memory_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "processed_input": processed_input,
                "intent": intent,
                "sentiment": self.state.get("user_sentiment", "neutral"),
                "conversation_id": len(self.memory) + 1,
                "response_time": time.time()
            }
            self.memory.append(memory_entry)
            
            # Keep last 20 interactions
            if len(self.memory) > 20:
                self.memory.pop(0)
        except Exception as e:
            print(f"Memory update error: {e}")
    
    # ========================================================================
    # 4. ENHANCED DECISION MAKING
    # ========================================================================
    def _make_decision(self, intent: str, processed_input: str) -> str:
        """Enhanced decision making with context"""
        try:
            # Consider conversation history
            recent_intents = [m["intent"] for m in self.memory[-3:]]
            
            action_map = {
                "greeting": "greet_user",
                "weather": "get_weather",
                "time": "get_time",
                "search_products": "search_products",
                "get_user_info": "get_user_info",
                "location": "handle_location",
                "help": "provide_help",
                "goodbye": "say_goodbye",
                "question": "answer_question",
                "general": "general_chat"
            }
            
            action = action_map.get(intent, "general_chat")
            
            # Context-aware modifications
            if intent == "greeting" and "greeting" in recent_intents:
                action = "greet_returning_user"
            elif intent == "weather" and not self.state.get("user_location"):
                action = "ask_location_for_weather"
            
            return action
            
        except Exception as e:
            print(f"Decision making error: {e}")
            return "general_chat"
    
    # ========================================================================
    # 5. ENHANCED TOOL EXECUTION
    # ========================================================================
    def _execute_tool(self, action: str, processed_input: str) -> Dict[str, Any]:
        """Enhanced tool execution with real APIs"""
        try:
            if action == "greet_user":
                greeting = self.knowledge["greeting"][self.state["conversation_count"] % len(self.knowledge["greeting"])]
                return {"type": "greeting", "data": greeting}
            
            elif action == "greet_returning_user":
                name = self.state.get("user_name", "friend")
                return {"type": "greeting", "data": f"Hello again, {name}! How can I help you today?"}
            
            elif action == "get_weather":
                return self._get_weather_data(processed_input)
            
            elif action == "ask_location_for_weather":
                return {"type": "location_request", "data": "I'd be happy to check the weather for you! What city would you like to know about?"}
            
            elif action == "get_time":
                current_time = datetime.now().strftime("%I:%M %p")
                current_date = datetime.now().strftime("%B %d, %Y")
                return {"type": "time", "data": f"It's currently {current_time} on {current_date}"}
            
            elif action == "search_products":
                return self._search_products_api(processed_input)
            
            elif action == "get_user_info":
                return self._get_user_profile_api()
            
            elif action == "provide_help":
                return {"type": "help", "data": self.knowledge["help"]}
            
            elif action == "say_goodbye":
                goodbye = self.knowledge["goodbye"][0]
                return {"type": "goodbye", "data": goodbye}
            
            elif action == "answer_question":
                return self._answer_question_llm(processed_input)
            
            else:
                return {"type": "general", "data": "I understand you're trying to communicate with me. How can I help you today?"}
        
        except Exception as e:
            print(f"Tool execution error: {e}")
            return {"type": "error", "data": "I encountered an issue processing your request."}
    
    def _get_weather_data(self, processed_input: str) -> Dict[str, Any]:
        """Get mock weather data - no API needed"""
        try:
            # Extract city from input (simple approach)
            city = self._extract_city(processed_input) or self.state.get("user_location", "London")
            
            # Mock weather data - no API calls needed
            mock_weather = {
                "london": {"temp": 15, "desc": "partly cloudy"},
                "new york": {"temp": 22, "desc": "sunny"},
                "paris": {"temp": 18, "desc": "light rain"},
                "tokyo": {"temp": 25, "desc": "clear sky"},
                "default": {"temp": 20, "desc": "pleasant"}
            }
            
            city_lower = city.lower()
            weather = mock_weather.get(city_lower, mock_weather["default"])
            
            weather_info = f"The weather in {city} is {weather['desc']} with a temperature of {weather['temp']}°C"
            return {"type": "weather", "data": weather_info}
                
        except Exception as e:
            print(f"Weather error: {e}")
            return {"type": "weather", "data": "I'm having trouble getting weather data right now."}
    
    def _search_products_api(self, query: str) -> Dict[str, Any]:
        """Mock Product Search API"""
        try:
            # Mock product database
            products = {
                "laptop": [
                    {"name": "MacBook Pro", "price": 1999, "rating": 4.8},
                    {"name": "Dell XPS 13", "price": 1299, "rating": 4.5},
                    {"name": "ThinkPad X1", "price": 1599, "rating": 4.6}
                ],
                "phone": [
                    {"name": "iPhone 15", "price": 999, "rating": 4.7},
                    {"name": "Samsung Galaxy S24", "price": 899, "rating": 4.6},
                    {"name": "Google Pixel 8", "price": 699, "rating": 4.4}
                ],
                "headphones": [
                    {"name": "AirPods Pro", "price": 249, "rating": 4.5},
                    {"name": "Sony WH-1000XM5", "price": 399, "rating": 4.8},
                    {"name": "Bose QuietComfort", "price": 329, "rating": 4.6}
                ]
            }
            
            # Simple search logic
            query_lower = query.lower()
            for category, items in products.items():
                if category in query_lower:
                    result = f"Found {len(items)} {category}s:\n"
                    for item in items:
                        result += f"• {item['name']} - ${item['price']} (⭐{item['rating']})\n"
                    return {"type": "products", "data": result}
            
            return {"type": "products", "data": "Sorry, I couldn't find any products matching your search."}
            
        except Exception as e:
            print(f"Product search error: {e}")
            return {"type": "products", "data": "I'm having trouble searching products right now."}
    
    def _get_user_profile_api(self) -> Dict[str, Any]:
        """Mock User Profile API"""
        try:
            # Mock user data based on session
            user_name = self.state.get("user_name", "Guest")
            
            mock_profile = {
                "name": user_name,
                "preferences": ["electronics", "books"],
                "purchase_history": ["MacBook Pro", "iPhone 14"],
                "loyalty_points": 1250,
                "member_since": "2023"
            }
            
            result = f"Profile for {mock_profile['name']}:\n"
            result += f"• Loyalty Points: {mock_profile['loyalty_points']}\n"
            result += f"• Member Since: {mock_profile['member_since']}\n"
            result += f"• Recent Purchases: {', '.join(mock_profile['purchase_history'])}\n"
            result += f"• Interests: {', '.join(mock_profile['preferences'])}"
            
            return {"type": "profile", "data": result}
            
        except Exception as e:
            print(f"User profile error: {e}")
            return {"type": "profile", "data": "I'm having trouble accessing your profile right now."}
    
    def _extract_city(self, text: str) -> Optional[str]:
        """Simple city extraction from text"""
        # This is a simplified approach - in production, use NER
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                return words[i + 1].title()
        return None
    
    def _answer_question_llm(self, question: str) -> Dict[str, Any]:
        """Answer questions using LLM"""
        if not self.openai_client:
            return {"type": "question", "data": "I'd like to help answer your question, but I need access to AI capabilities."}
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Give brief, accurate answers."},
                    {"role": "user", "content": question}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            answer = response.choices[0].message.content.strip()
            return {"type": "question", "data": answer}
            
        except Exception as e:
            print(f"LLM question answering error: {e}")
            return {"type": "question", "data": "I'm having trouble processing your question right now."}
    
    # ========================================================================
    # 6. ENHANCED RESPONSE GENERATION
    # ========================================================================
    def _generate_response_llm(self, result: Dict[str, Any], intent: str, user_input: str) -> str:
        """LLM-powered response generation"""
        if not self.openai_client:
            return self._generate_response_simple(result, intent)
        
        try:
            base_response = result.get("data", "")
            
            # Get conversation context
            recent_context = ""
            if len(self.memory) > 1:
                recent_context = f"Recent conversation: {self.memory[-1]['user_input']}"
            
            prompt = f"""You are a friendly AI assistant. 

User said: "{user_input}"
Intent: {intent}
Base response: "{base_response}"
{recent_context}

Create a natural, helpful response. Keep it conversational and brief (1-2 sentences max)."""

            response = self.openai_client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM response generation error: {e}")
            return self._generate_response_simple(result, intent)
    
    def _generate_response_simple(self, result: Dict[str, Any], intent: str) -> str:
        """Fallback simple response generation"""
        try:
            response_data = result.get("data", "I'm not sure how to respond to that.")
            
            # Add personality based on sentiment
            sentiment = self.state.get("user_sentiment", "neutral")
            if sentiment == "positive":
                response_data = f"😊 {response_data}"
            elif sentiment == "negative":
                response_data = f"I understand. {response_data}"
            
            return response_data
        except Exception as e:
            print(f"Simple response generation error: {e}")
            return "I'm having trouble generating a response right now."
    
    # ========================================================================
    # 7. ENHANCED STATE MANAGEMENT
    # ========================================================================
    def _update_state(self, intent: str, action: str, processed_input: str):
        """Enhanced state management"""
        try:
            self.state["current_intent"] = intent
            self.state["last_action"] = action
            self.state["conversation_count"] += 1
            self.state["last_update"] = datetime.now().isoformat()
            
            # Extract user name
            if "my name is" in processed_input.lower():
                words = processed_input.lower().split()
                try:
                    name_index = words.index("is") + 1
                    if name_index < len(words):
                        self.state["user_name"] = words[name_index].capitalize()
                except ValueError:
                    pass
            
            # Extract location for weather
            if intent == "weather" and any(word in processed_input.lower() for word in ["in", "at", "for"]):
                city = self._extract_city(processed_input)
                if city:
                    self.state["user_location"] = city
                    
        except Exception as e:
            print(f"State management error: {e}")
    
    # ========================================================================
    # 8. ERROR HANDLING (built into methods above)
    # ========================================================================
    
    # ========================================================================
    # 9. ENHANCED OUTPUT DELIVERY
    # ========================================================================
    def _deliver_output(self, response: str) -> str:
        """Enhanced output formatting"""
        try:
            # Add emoji based on response type
            if any(word in response.lower() for word in ["weather", "temperature"]):
                emoji = "🌤️"
            elif any(word in response.lower() for word in ["time", "clock"]):
                emoji = "🕐"
            elif any(word in response.lower() for word in ["hello", "hi"]):
                emoji = "👋"
            elif any(word in response.lower() for word in ["goodbye", "bye"]):
                emoji = "👋"
            else:
                emoji = "🤖"
            
            return f"{emoji} Agent: {response}"
        except Exception as e:
            print(f"Output delivery error: {e}")
            return f"🤖 Agent: {response}"
    
    # ========================================================================
    # 10. ENHANCED LEARNING/FEEDBACK
    # ========================================================================
    def _learn_from_interaction(self, user_input: str, intent: str, response: str):
        """Enhanced learning with pattern recognition"""
        try:
            if not hasattr(self, 'learning_data'):
                self.learning_data = {"patterns": {}, "preferences": {}, "performance": {}}
            
            # Track intent patterns
            if intent not in self.learning_data["patterns"]:
                self.learning_data["patterns"][intent] = {"count": 0, "examples": [], "success_rate": 0.0}
            
            self.learning_data["patterns"][intent]["count"] += 1
            self.learning_data["patterns"][intent]["examples"].append({
                "input": user_input,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only recent examples
            if len(self.learning_data["patterns"][intent]["examples"]) > 10:
                self.learning_data["patterns"][intent]["examples"].pop(0)
            
            # Track user preferences
            if self.state.get("user_name"):
                user_name = self.state["user_name"]
                if user_name not in self.learning_data["preferences"]:
                    self.learning_data["preferences"][user_name] = {"favorite_topics": [], "interaction_style": "neutral"}
                
                self.learning_data["preferences"][user_name]["favorite_topics"].append(intent)
                
        except Exception as e:
            print(f"Learning error: {e}")
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get detailed agent statistics"""
        return {
            "basic_stats": {
                "conversations": self.state["conversation_count"],
                "memory_size": len(self.memory),
                "session_duration": str(datetime.now() - datetime.fromisoformat(self.state["session_start"])),
                "llm_enabled": bool(self.openai_client)
            },
            "current_state": self.state,
            "learning_data": getattr(self, 'learning_data', {}),
            "capabilities": {
                "weather_api": bool(self.config.weather_api_key),
                "openai_api": bool(self.openai_client),
                "memory_size": len(self.memory)
            }
        }
    
    def configure(self, **kwargs):
        """Update agent configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Reinitialize OpenAI client if API key changed
        if 'openai_api_key' in kwargs and HAS_OPENAI:
            self.openai_client = OpenAI(api_key=self.config.openai_api_key)

# ============================================================================
# DEMO APPLICATION
# ============================================================================

def setup_config():
    """Configuration with LLM + 2 Mock APIs"""
    config = AgentConfig()
    
    # Enable LLM if API key available
    config.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if config.openai_api_key:
        config.use_llm = True
        print("🧠 LLM enabled with OpenAI")
    else:
        config.use_llm = False
        print("🤖 LLM disabled - using rule-based responses")
    
    # Use mock APIs (no real API keys needed)
    config.weather_api_key = ""  # Mock weather API
    
    print("🌤️ Weather API: Mock data")
    print("📊 Product API: Mock data") 
    print("🚀 Ready to demonstrate LLM + 2 Mock APIs!")
    
    return config

def run_enhanced_demo():
    """Interactive demo of the enhanced AI agent"""
    print("🚀 Enhanced AI Agent Demo")
    print("=" * 50)
    print("Features: LLM integration, real weather data, enhanced memory")
    print("Try: 'hello', 'what's the weather in London?', 'what time is it?', 'why is the sky blue?'")
    print("Commands: 'stats', 'config', 'reset', 'quit'")
    print()
    
    config = setup_config()
    agent = EnhancedAIAgent(config)
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                response = agent.run("goodbye")
                print(response)
                break
            elif user_input.lower() == 'stats':
                stats = agent.get_enhanced_stats()
                print(f"📊 Enhanced Stats:\n{json.dumps(stats, indent=2)}")
                continue
            elif user_input.lower() == 'config':
                print(f"⚙️ Current Config:")
                print(f"  LLM Enabled: {bool(agent.openai_client)}")
                print(f"  Weather API: {bool(agent.config.weather_api_key)}")
                print(f"  Model: {agent.config.model}")
                continue
            elif user_input.lower() == 'reset':
                agent = EnhancedAIAgent(config)
                print("🔄 Agent reset!")
                continue
            elif not user_input:
                continue
            
            # Run the enhanced agent
            response = agent.run(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_enhanced_demo()
