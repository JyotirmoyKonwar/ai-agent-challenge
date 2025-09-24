import argparse
from dotenv import load_dotenv
from src.langgraphagent.llms.llmgroq import GroqLLM
from src.langgraphagent.graph.graph_builder import GraphBuilder

def run_agent_app():
    """
    Loads and runs the LangGraph AgenticAI application.
    This function initializes the UI, handles user input, configures the LLM model,
    sets up the graph, and runs the agentic process.
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the AI agent to generate a PDF parser.")
    parser.add_argument("--target", type=str, required=True, help="The target bank for the parser (e.g., 'icici').")
    parser.add_argument("--retries", type=int, default=3, help="The maximum number of self-correction attempts.")
    args = parser.parse_args()

    print(f"Starting agent for target: {args.target} with {args.retries} retries...")

    try:
        #LLM configuration
        obj_llm_config = GroqLLM()
        model = obj_llm_config.get_llm_model()

        if not model:
            print("Error: LLM model could not be initialized. Check your API key.")
            return

        #Initializing and setting the graph
        graph_builder = GraphBuilder(model)
        graph = graph_builder.build_graph()

        #Initial states
        initial_state = {
            "target_bank": args.target,
            "plan": "",
            "generated_code": "",
            "error_message": "",
            "retries_left": args.retries,
        }

        final_state = graph.invoke(initial_state)

        print("\n--- AGENT RUN COMPLETE ---")
        if final_state.get("error_message") and final_state.get("retries_left", 0) == 0:
            print("Agent finished with an unresolved error after all retries.")
            print(f"Final Error: {final_state['error_message']}")
        else:
            print("Parser generated successfully at:")
            print(f"custom_parsers/{args.target}_parser.py")

    except Exception as e:
        print(f"\n--- An unexpected error occurred during the agent run ---")
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    run_agent_app()

