import os
from typing import TypedDict, Annotated, Dict, List, Optional, Any, Tuple
import operator
from dotenv import load_dotenv

# LangChain and LangGraph imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import SqliteSaver

# Import tools
from app.utils.zillow_api import search_properties
from app.utils.google_maps_api import search_places
from app.utils.rag_system import query_vector_db

# Load environment variables
load_dotenv()

# Define the state for our agent system
class AgentState(TypedDict):
    """State for the agent system"""
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    intent: Optional[str]
    map_data: Optional[Dict[str, Any]]
    property_data: Optional[List[Dict[str, Any]]]
    local_data: Optional[List[Dict[str, Any]]]
    rag_data: Optional[str]

# Initialize LLM models
def get_frontier_llm():
    """Get the frontier LLM for main interactions"""
    # Try to use Anthropic Claude first, fall back to OpenAI, then Google
    if os.getenv("ANTHROPIC_API_KEY"):
        return ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0.7)
    elif os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o", temperature=0.7)
    else:
        return ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)

def get_smaller_llm():
    """Get a smaller, cheaper LLM for intermediate steps"""
    # Try to use OpenAI first, fall back to Google, then Anthropic
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    elif os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.7)
    else:
        return ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.7)

# Define the agent nodes
def intent_classifier(state: AgentState) -> Dict[str, Any]:
    """Classify the user's intent to determine which agent to use"""
    smaller_llm = get_smaller_llm()
    
    # Create a prompt for intent classification
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an intent classifier for an international student advisor system. 
        Classify the user query into one of the following categories:
        - PROPERTY_SEARCH: Queries about finding housing, apartments, or accommodation
        - LOCAL_ADVICE: Queries about local services, restaurants, transportation, or amenities
        - STUDENT_GUIDANCE: Queries about legal matters, cultural adaptation, or student-specific advice
        - GENERAL: Any other general queries
        
        Respond with ONLY the category name."""),
        HumanMessage(content="{query}")
    ])
    
    # Create the chain
    chain = prompt | smaller_llm | StrOutputParser()
    
    # Run the chain
    intent = chain.invoke({"query": state["user_query"]})
    
    # Return the intent
    return {"intent": intent.strip()}

def route_based_on_intent(state: AgentState) -> str:
    """Route to the appropriate agent based on intent"""
    intent = state["intent"]
    
    if intent == "PROPERTY_SEARCH":
        return "property_agent"
    elif intent == "LOCAL_ADVICE":
        return "local_agent"
    elif intent == "STUDENT_GUIDANCE":
        return "rag_agent"
    else:
        return "main_agent"

def property_agent(state: AgentState) -> Dict[str, Any]:
    """Agent for handling property search queries"""
    smaller_llm = get_smaller_llm()
    
    # Create a prompt for extracting search parameters
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a property search assistant. 
        Extract the search parameters from the user query.
        Return a JSON object with the following fields:
        - location: The city or neighborhood
        - min_price: Minimum price (if specified)
        - max_price: Maximum price (if specified)
        - bedrooms: Number of bedrooms (if specified)
        - property_type: Type of property (apartment, house, etc.)"""),
        HumanMessage(content="{query}")
    ])
    
    # Create the chain
    chain = prompt | smaller_llm | StrOutputParser()
    
    # Run the chain
    params_str = chain.invoke({"query": state["user_query"]})
    
    # Search for properties using the Zillow API
    try:
        property_data = search_properties(params_str)
        
        # Update map data with property locations
        map_data = {
            "center": property_data[0]["location"] if property_data else None,
            "markers": [
                {
                    "position": p["location"],
                    "title": p["address"],
                    "info": f"{p['price']} - {p['bedrooms']} bed, {p['bathrooms']} bath"
                }
                for p in property_data
            ]
        }
        
        return {
            "property_data": property_data,
            "map_data": map_data
        }
    except Exception as e:
        return {
            "property_data": [],
            "map_data": None,
            "messages": [AIMessage(content=f"I encountered an error searching for properties: {str(e)}")]
        }

def local_agent(state: AgentState) -> Dict[str, Any]:
    """Agent for handling local advice queries"""
    smaller_llm = get_smaller_llm()
    
    # Create a prompt for extracting search parameters
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a local advisor assistant.
        Extract the search parameters from the user query.
        Return a JSON object with the following fields:
        - location: The city or neighborhood
        - place_type: Type of place (restaurant, grocery, etc.)
        - radius: Search radius in meters (default 1000)"""),
        HumanMessage(content="{query}")
    ])
    
    # Create the chain
    chain = prompt | smaller_llm | StrOutputParser()
    
    # Run the chain
    params_str = chain.invoke({"query": state["user_query"]})
    
    # Search for places using the Google Maps API
    try:
        local_data = search_places(params_str)
        
        # Update map data with place locations
        map_data = {
            "center": local_data[0]["location"] if local_data else None,
            "markers": [
                {
                    "position": p["location"],
                    "title": p["name"],
                    "info": f"{p['address']} - Rating: {p['rating']}"
                }
                for p in local_data
            ]
        }
        
        return {
            "local_data": local_data,
            "map_data": map_data
        }
    except Exception as e:
        return {
            "local_data": [],
            "map_data": None,
            "messages": [AIMessage(content=f"I encountered an error searching for local places: {str(e)}")]
        }

def rag_agent(state: AgentState) -> Dict[str, Any]:
    """Agent for handling student guidance queries using RAG"""
    smaller_llm = get_smaller_llm()
    
    # Query the vector database
    try:
        rag_data = query_vector_db(state["user_query"])
        
        return {
            "rag_data": rag_data
        }
    except Exception as e:
        return {
            "rag_data": None,
            "messages": [AIMessage(content=f"I encountered an error retrieving information: {str(e)}")]
        }

def main_agent(state: AgentState) -> Dict[str, Any]:
    """Main agent for generating the final response"""
    frontier_llm = get_frontier_llm()
    
    # Create a prompt for the final response
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are InternationAlly, an AI-powered trusted international student advisor.
        Your goal is to help international students feel comfortable and confident in their new foreign environment.
        Be empathetic, informative, and supportive in your responses.
        
        If property data is available, incorporate it into your response.
        If local place data is available, incorporate it into your response.
        If RAG data is available, use it to provide accurate information.
        
        Always maintain a helpful, friendly tone and provide actionable advice."""),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content="""
        User Query: {user_query}
        
        Property Data: {property_data}
        Local Data: {local_data}
        RAG Data: {rag_data}
        
        Please provide a helpful response to the user query.
        """)
    ])
    
    # Create the chain
    chain = prompt | frontier_llm | StrOutputParser()
    
    # Run the chain
    response = chain.invoke({
        "messages": state["messages"],
        "user_query": state["user_query"],
        "property_data": state.get("property_data", []),
        "local_data": state.get("local_data", []),
        "rag_data": state.get("rag_data", "")
    })
    
    # Return the response
    return {
        "messages": [AIMessage(content=response)]
    }

# Build the graph
def build_agent_graph():
    """Build the agent graph using LangGraph"""
    # Create a memory system
    memory = SqliteSaver.from_conn_string("sqlite:///agent_memory.db")
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_classifier", intent_classifier)
    workflow.add_node("property_agent", property_agent)
    workflow.add_node("local_agent", local_agent)
    workflow.add_node("rag_agent", rag_agent)
    workflow.add_node("main_agent", main_agent)
    
    # Add edges
    workflow.add_edge("intent_classifier", route_based_on_intent)
    workflow.add_edge("property_agent", "main_agent")
    workflow.add_edge("local_agent", "main_agent")
    workflow.add_edge("rag_agent", "main_agent")
    workflow.add_edge("main_agent", END)
    
    # Set the entry point
    workflow.set_entry_point("intent_classifier")
    
    # Compile the graph
    return workflow.compile(checkpointer=memory)

# Initialize the agent graph
agent_graph = build_agent_graph()

def process_user_query(query: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Process a user query and return the response and map data"""
    # Initialize the state
    state = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "intent": None,
        "map_data": None,
        "property_data": None,
        "local_data": None,
        "rag_data": None
    }
    
    # Run the graph
    for step in agent_graph.stream(state):
        pass
    
    # Get the final state
    final_state = step
    
    # Extract the response and map data
    response = final_state["messages"][-1].content
    map_data = final_state.get("map_data")
    
    return response, map_data
