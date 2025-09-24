import os
from dotenv import load_dotenv
from src.langgraphagent.llms.llmgroq import GroqLLM
from src.langgraphagent.graph.graph_builder import GraphBuilder
from io import BytesIO
from PIL import Image as PILImage

# The following imports are only needed if you are running this code
# in an interactive environment like a Jupyter notebook or Google Colab.
# from IPython.display import Image, display

print("Generating Mermaid graph diagram...")

# Load environment variables (to get the API key)
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    # Use a dummy key if not found, as the LLM isn't actually called.
    print("Warning: GROQ_API_KEY not found in .env. Using a dummy key.")
    groq_api_key = "dummy_key"

# 1. Initialize the LLM configuration.
llm_config = GroqLLM()
model = llm_config.get_llm_model()

# 2. Build the graph structure using the GraphBuilder class.
graph_builder = GraphBuilder(model)
agentic_graph = graph_builder.build_graph()

# 3. Get the graph's PNG image data as bytes using Mermaid.
png_bytes = agentic_graph.get_graph().draw_mermaid_png()

# 4. Save the image bytes to a file.
output_filename = "agent_graph_mermaid.png"
image = PILImage.open(BytesIO(png_bytes))
image.save(output_filename)

print(f"\nSuccess! Graph diagram saved to '{output_filename}'")

# 5. How to display in a notebook (as requested)
# The `display` function is specifically for interactive environments.
# To use it, you would uncomment the following lines in your notebook:
#
# print("\nDisplaying image in notebook:")
# display(Image(png_bytes))

print("\n--- End of Script ---\n")

