# test_improvements.py

"""
Test script to demonstrate the improved intent parsing and memory integration
without requiring voice input.
"""

from intent_parser import IntentParser
from llm_interface import LLMInterface
from enhanced_memory import EnhancedMemory

def test_intent_parsing():
    print("=== Testing Intent Parsing ===\n")
    
    intent_parser = IntentParser()
    
    test_commands = [
        "What's the weather like?",
        "Is it going to rain tomorrow?",
        "How hot is it in Paris?",
        "Schedule a meeting for tomorrow at 3 PM",
        "Add doctor appointment to my calendar",
        "Show me my calendar for today",
        "What meetings do I have upcoming?",
        "Set a timer for 15 minutes",
        "Remind me in 2 hours",
        "What time is it?",
        "What did we talk about yesterday?",
        "Do you remember what I said about the project?",
        "What was that thing you told me earlier?",
        "We were discussing something before",
        "Tell me a joke",
        "Hello there",
        "Goodbye",
        "What's the capital of France?",
        "How do I cook pasta?",
    ]
    
    for command in test_commands:
        intent = intent_parser.parse_intent(command)
        is_memory_related = intent_parser.is_memory_related(command)
        print(f"Command: '{command}'")
        print(f"  Intent: {intent}")
        print(f"  Memory-related: {is_memory_related}")
        print()

def test_memory_integration():
    print("=== Testing Memory Integration ===\n")
    
    memory = EnhancedMemory("test_memory.db")
    llm = LLMInterface(model="mistral", memory=memory)
    
    # Simulate some conversations
    print("1. Simulating initial conversations...")
    
    conversations = [
        ("What's the weather like today?", "The weather is sunny with a temperature of 22°C."),
        ("Remind me about my doctor appointment", "I've noted your doctor appointment. When is it scheduled?"),
        ("It's at 3 PM tomorrow", "Got it! Doctor appointment at 3 PM tomorrow."),
        ("What's a good recipe for pasta?", "Here's a simple pasta recipe: boil water, add pasta, cook for 10-12 minutes..."),
        ("Thanks, that helps!", "You're welcome! Let me know if you need any other cooking tips."),
    ]
    
    for user_msg, assistant_msg in conversations:
        memory.save_interaction(user_msg, assistant_msg, importance=5)
        print(f"Saved: '{user_msg}' -> '{assistant_msg}'")
    
    print("\n2. Testing memory recall...")
    
    # Test recent memory recall
    recent_context = memory.get_short_term_context(limit=3)
    print("Recent context:")
    print(recent_context)
    
    # Test contextual memory search
    print("\n3. Testing contextual memory search...")
    
    search_queries = [
        "doctor appointment",
        "weather",
        "pasta recipe",
        "cooking"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = memory.search_memory(query, limit=2)
        for result in results:
            print(f"  Found: '{result.get('user_input', result.get('content', ''))}' -> '{result.get('response', result.get('content', ''))}'")
    
    # Test contextual memory retrieval
    print("\n4. Testing contextual memory retrieval...")
    
    test_queries = [
        "What did we discuss about the doctor?",
        "Tell me about the weather again",
        "What was that recipe you mentioned?",
        "Something about cooking"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        contextual_memory = memory.get_relevant_context(query, max_items=2)
        print("Contextual memory:")
        print(contextual_memory)
    
    # Clean up
    memory.close()

def test_enhanced_workflow():
    print("=== Testing Enhanced Workflow ===\n")
    
    memory = EnhancedMemory("test_workflow.db")
    llm = LLMInterface(model="mistral", memory=memory)
    intent_parser = IntentParser()
    
    # Simulate a conversation flow
    test_inputs = [
        "What's the weather like?",
        "It's sunny and 25 degrees.",
        "What did you just tell me about the weather?",
        "Do you remember what the temperature was?",
        "Schedule a meeting for tomorrow at 2 PM",
        "What meetings do I have scheduled?",
        "What was that weather information again?",
    ]
    
    print("Simulating conversation flow:\n")
    
    for i, user_input in enumerate(test_inputs):
        print(f"Step {i+1}: User says: '{user_input}'")
        
        # Parse intent
        intent = intent_parser.parse_intent(user_input)
        is_memory_related = intent_parser.is_memory_related(user_input)
        
        print(f"  Detected intent: {intent}")
        print(f"  Memory-related: {is_memory_related}")
        
        # Simulate response based on intent
        if intent == "memory_recall" or is_memory_related:
            print("  -> Using memory search for response")
            contextual_memory = memory.get_relevant_context(user_input, max_items=2)
            print(f"  -> Found contextual memory: {len(contextual_memory)} chars")
        elif intent == "get_weather":
            print("  -> Processing weather request")
            response = "The weather is sunny with a temperature of 25°C."
            memory.save_interaction(user_input, response, importance=6, tags=["weather"])
        elif intent == "calendar_add":
            print("  -> Processing calendar addition")
            response = "I've scheduled your meeting for tomorrow at 2 PM."
            memory.save_interaction(user_input, response, importance=7, tags=["calendar", "scheduling"])
        elif intent == "calendar_view":
            print("  -> Processing calendar view")
            response = "You have a meeting scheduled for tomorrow at 2 PM."
            memory.save_interaction(user_input, response, importance=6, tags=["calendar"])
        else:
            print("  -> Processing general query")
            response = f"I understand you're asking about: {user_input}"
            memory.save_interaction(user_input, response, importance=3, tags=["general"])
        
        print()
    
    # Clean up
    memory.close()

if __name__ == "__main__":
    print("Testing AI Assistant Improvements")
    print("=" * 40)
    
    test_intent_parsing()
    
    test_memory_integration()
    
    test_enhanced_workflow()
    
    print("\n" + "=" * 40)
    print("All tests completed!")
    print("\nKey improvements implemented:")
    print("1. ✅ LLM-based intent parsing with keyword fallback")
    print("2. ✅ Enhanced memory system with contextual search")
    print("3. ✅ Memory-aware LLM interface")
    print("4. ✅ Better handling of memory-related queries")
    print("5. ✅ Improved conversation context management")
