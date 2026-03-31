import asyncio
import argparse
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent import researcher_agent
from langchain_core.messages import HumanMessage

async def run_research(topic: str):
    """Run the research agent on a given topic."""
    print(f"\n[bold blue]Starting research on:[/bold blue] {topic}\n")
    
    # Initial state for the researcher agent
    initial_state = {
        "research_topic": topic,
        "researcher_messages": [HumanMessage(content=f"Please research the following topic: {topic}")],
        "tool_call_iterations": 0,
        "raw_notes": []
    }
    
    try:
        # We use astream to see the progress of the agent
        # stream_mode="updates" allows us to see when nodes complete
        async for event in researcher_agent.astream(initial_state, stream_mode="updates"):
            for node_name, output in event.items():
                if node_name == "llm_call":
                    # Check if the LLM made tool calls
                    last_message = output["researcher_messages"][-1]
                    if last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            print(f"[yellow]Agent is using tool:[/yellow] {tool_call['name']}")
                            if tool_call['name'] == 'think_tool':
                                print(f"  [italic]Thought:[/italic] {tool_call['args'].get('thought', '')}")
                            elif tool_call['name'] == 'tavily_search':
                                print(f"  [italic]Query:[/italic] {tool_call['args'].get('query', '')}")
                    else:
                        print("[green]Agent has finished gathering information.[/green]")
                
                elif node_name == "tool_node":
                    print("[blue]Tool execution complete.[/blue]")
                
                elif node_name == "compress_research":
                    print("\n" + "="*50)
                    print("FINAL RESEARCH REPORT")
                    print("="*50)
                    print(output["compressed_research"])
                    print("="*50 + "\n")
                    
    except Exception as e:
        print(f"[red]An error occurred during research:[/red] {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Run the Autonomus Brief Research Agent")
    parser.add_argument("topic", type=str, help="The research topic to investigate")
    
    args = parser.parse_args()
    
    # Check for required API keys
    # These are used by the agent and its tools
    import os
    missing_keys = []
    if not os.getenv("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY")
    # if not os.getenv("tavily_search_API_KEY"):
    #     missing_keys.append("tavily_search_API_KEY")
    # Try to import rich for better formatting, fallback to print if not available
    try:
        from rich import print
        
        if missing_keys:
            print(f"Warning: Missing environment variables: {', '.join(missing_keys)}")
            print("The agent might fail if these are required for the selected models/tools.")

    except ImportError:
        # Define a simple print if rich is not available
        pass

    asyncio.run(run_research(args.topic))

if __name__ == "__main__":
    main()
