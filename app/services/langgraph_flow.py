# app/services/langgraph_flow.py
import logging
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # In-memory checkpointing for demo

from app.services.groq_client import chat_llm # Use the initialized ChatGroq instance
from app.utils.contract_templates import get_contract_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state structure for the graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    document_context: Annotated[Optional[str], operator.setitem] # Store extracted text
    task_description: Annotated[Optional[str], operator.setitem] # What the user wants to do
    contract_details: Annotated[Optional[Dict[str, Any]], operator.setitem] # Info for contract generation

# Define the nodes in the graph
async def call_llm(state: AgentState):
    """Invokes the LLM with the current state messages."""
    if not chat_llm:
         return {"messages": [AIMessage(content="LLM is not available.")]}
    try:
        # Add document context to the prompt if available
        messages_to_send = list(state['messages'])
        context = state.get('document_context')
        task = state.get('task_description')

        # Construct a better prompt including context and task
        current_prompt = messages_to_send[-1].content
        system_prompt = "You are LegalMind, an AI legal assistant. Be helpful, concise, and informative. Avoid giving legal advice."
        prompt_with_context = f"{system_prompt}\n\n"

        if context:
             prompt_with_context += f"**Document Context:**\n{context}\n\n"
        if task:
             prompt_with_context += f"**User's Goal:** {task}\n\n"

        prompt_with_context += f"**User's Query:**\n{current_prompt}"

        # Replace last human message with the enriched one for clarity in history
        # Or prepend a system message with context? Let's try modifying the last user msg for now.
        # messages_to_send[-1] = HumanMessage(content=prompt_with_context)
        # Alternatively, send context in a system message? Let's just rely on the LLM understanding the structured input.
        # We might need a RAG setup for better context handling on large docs.

        # For now, let's just add context to the latest query if present
        final_user_query = current_prompt
        if context:
            final_user_query = f"Based on the following document context:\n---\n{context}\n---\n\n{current_prompt}"

        messages_to_send = [SystemMessage(content=system_prompt)] + messages_to_send[:-1] + [HumanMessage(content=final_user_query)]

        logger.info(f"Calling LLM. State includes context: {bool(context)}, task: {bool(task)}")
        response = await chat_llm.ainvoke(messages_to_send)
        logger.info("LLM call successful.")
        return {"messages": [response]} # Append AI response to messages
    except Exception as e:
        logger.error(f"Error calling LLM in LangGraph: {e}", exc_info=True)
        return {"messages": [AIMessage(content="Sorry, I encountered an error processing your request.")]}

async def generate_contract_node(state: AgentState):
    """Generates a contract based on type and details."""
    if not chat_llm:
         return {"messages": [AIMessage(content="LLM is not available for contract generation.")]}

    contract_type = state.get("contract_details", {}).get("type", "unknown")
    user_details = state.get("contract_details", {}).get("details", "")
    logger.info(f"Generating contract of type: {contract_type}")

    base_prompt = get_contract_prompt(contract_type)
    if not base_prompt:
         logger.warning(f"No template found for contract type: {contract_type}")
         return {"messages": [AIMessage(content=f"Sorry, I don't have a template for a '{contract_type}' contract.")]}

    # Construct a more detailed prompt for the LLM
    full_prompt = f"{base_prompt}\n\nPlease incorporate the following details provided by the user:\n{user_details}\n\nGenerate the contract text:"

    try:
        response = await chat_llm.ainvoke([
            SystemMessage(content="You are an AI assistant tasked with generating contract text based on templates and user-provided details. Fill in placeholders where details are missing."),
            HumanMessage(content=full_prompt)
        ])
        logger.info("Contract generation successful.")
        # Add the generated contract as an AI message
        return {"messages": [AIMessage(content=f"Here is the draft {contract_type.replace('_', ' ').title()}:\n\n```\n{response.content}\n```\nPlease review this draft carefully. It is AI-generated and may require review by a legal professional.")]}
    except Exception as e:
        logger.error(f"Error generating contract: {e}", exc_info=True)
        return {"messages": [AIMessage(content="Sorry, I encountered an error generating the contract.")]}


# Define the graph structure
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("llm_call", call_llm)
workflow.add_node("generate_contract", generate_contract_node)

# Define edges and conditional logic (simplified: always call LLM for now)
# A real app would have a router node analyzing intent first.
workflow.set_entry_point("llm_call") # Simplified: start with LLM call

# Conditional routing could be added here:
# workflow.add_conditional_edges(...)

# For this simple version, assume chat is always LLM call, generation is separate or triggered by LLM analysis.
# Let's make the entry point decision external for now (based on endpoint called).
# We'll build separate entry points/graphs if needed or add routing later.

# For now, just connect LLM call to end (simple chat)
workflow.add_edge("llm_call", END)
workflow.add_edge("generate_contract", END) # Contract generation also ends the flow for now

# Compile the graph
# Add memory for simple state persistence across calls within a "session"
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
logger.info("LangGraph workflow compiled.")

# Function to run the graph (simplified interface)
async def run_chat_flow(user_input: str, session_id: str, doc_context: Optional[str] = None):
    """Runs the chat part of the flow."""
    config = {"configurable": {"thread_id": session_id}}
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    if doc_context:
         # Add context to the initial state for this run
         initial_state["document_context"] = doc_context
         initial_state["task_description"] = "Analyze document or answer question based on it."

    logger.info(f"Running chat flow for session {session_id}. Context present: {bool(doc_context)}")
    final_state = await app_graph.ainvoke(initial_state, config=config)
    # Return only the latest AI message
    ai_message = next((m for m in reversed(final_state['messages']) if isinstance(m, AIMessage)), None)
    return ai_message.content if ai_message else "No response generated."

async def run_contract_flow(contract_type: str, details: str, session_id: str):
    """Runs the contract generation part of the flow."""
    config = {"configurable": {"thread_id": f"{session_id}_contract"}} # Separate thread for contract gen?
    initial_state = {
         "messages": [], # No chat history needed here directly
         "contract_details": {"type": contract_type, "details": details}
     }
    # We need to route to the 'generate_contract' node.
    # Since our graph is simple, we can call the node function directly or modify the graph invocation.
    # Let's refine the graph to handle this.

    # Rebuild graph with routing (Conceptual)
    # Add router node -> decides if chat or contract
    # For now, we'll just invoke the contract node logic via the LLM node for simplicity
    # by crafting a specific input state.

    # Simplified approach: Trigger contract generation via LLM call node
    # This isn't ideal LangGraph usage but works for this structure.
    # A better way is conditional edges based on state analysis.

    prompt_for_llm = f"Generate a {contract_type} contract with these details: {details}"
    generation_state = {
        "messages": [HumanMessage(content=prompt_for_llm)], # Use LLM to kick off generation
        "task_description": f"Generate {contract_type}"
    }

    # Override the graph's entry point? No, let's adjust state/prompt.
    # Option 1: Call generate_contract_node directly (not using graph state/memory well)
    # Option 2: Use the LLM node but prime it for generation (using this)
    # Option 3: Proper routing node (Best practice, more complex setup)

    # Using Option 2 - let the LLM handle the generation request
    # We need to ensure the call_llm function can understand this.
    # Let's add specific prompt instructions.
    system_prompt_gen = f"You are tasked with generating a {contract_type} contract."
    instruction_prompt = get_contract_prompt(contract_type)
    if not instruction_prompt:
        return f"Sorry, contract type '{contract_type}' is not supported."

    user_details_prompt = f"Please incorporate these user details:\n{details}\n\nGenerate the full contract text."

    # Combine prompts for the LLM call
    messages_for_gen = [
        SystemMessage(content=system_prompt_gen),
        HumanMessage(content=instruction_prompt + "\n\n" + user_details_prompt)
    ]

    logger.info(f"Running contract generation via LLM for session {session_id}")
    try:
        if not chat_llm:
            return "LLM is not available for contract generation."
        response = await chat_llm.ainvoke(messages_for_gen)
        logger.info("Contract generation LLM call successful.")
        # Format the response similar to the dedicated node
        return f"Here is the draft {contract_type.replace('_', ' ').title()}:\n\n```\n{response.content}\n```\nPlease review this draft carefully. It is AI-generated and may require review by a legal professional."

    except Exception as e:
        logger.error(f"Error generating contract via LLM: {e}", exc_info=True)
        return "Sorry, I encountered an error generating the contract."
