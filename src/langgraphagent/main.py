import argparse
import os
import sys
from dotenv import load_dotenv

from src.langgraphagent.llms.llmgroq import GroqLLM
from src.langgraphagent.graph.graph_builder import GraphBuilder

def run_agent_app():
    """
    Loads and runs the AI Coder Agent application.
    This function handles CLI input, configures the LLM model,
    and sets up and runs the graph.
    """
    # Load environment variables from a .env file at the project root
    load_dotenv()

    parser = argparse.ArgumentParser(description="AI Agent to generate PDF parsers.")
    parser.add_argument("--target", type=str, required=True, help="The target bank (e.g., 'icici').")
    args = parser.parse_args()
    target_bank = args.target

    print(f"🚀 Starting agent for target: {target_bank}")

    # Check if data directory exists
    data_dir = f"data/{target_bank}"
    if not os.path.exists(data_dir):
         print(f"Error: Data directory '{data_dir}' not found.")
         print("Please ensure you have the sample PDF and CSV files in the correct location and run from the root directory.")
         sys.exit(1)

    try:
        # 1. Configure the LLM
        llm_config = GroqLLM()
        model = llm_config.get_llm_model()

        if not model:
            print("Error: LLM model could not be initialized.")
            return

        # 2. Build the graph
        graph_builder = GraphBuilder(model)
        agent_graph = graph_builder.build_graph()

        # 3. Define initial state and run the agent
        initial_state = {
            "target_bank": target_bank,
            "task": f"Generate a Python parser for {target_bank} bank statements.",
            "retries_left": 3,
        }

        for _ in agent_graph.stream(initial_state):
            # The stream method executes the graph. Print statements within
            # the nodes will show the progress.
            pass

    except Exception as e:
         print(f"\nAn error occurred during agent execution: {e}")
         return

