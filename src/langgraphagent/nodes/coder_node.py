from langchain_core.messages import HumanMessage
from src.langgraphagent.state.state import State
from src.langgraphagent.tools.file_tools import write_code_to_file

class CoderNode:
    """
    Node 2: The Coder
    Generates the Python code based on the plan.
    """
    def __init__(self, model):
        self.llm = model

    def process(self, state: State) -> dict:
        """
        Generates Python code based on the provided plan.
        """
        print("--- GENERATING CODE ---")
        messages = [
            HumanMessage(
                content=f"""Based on this plan:
                '{state['plan']}'

                Please now write the complete Python code for the parser.
                The code must be a single block to be written to `custom_parsers/{state['target_bank']}_parser.py`.
                It must contain the function `parse(pdf_path: str) -> pd.DataFrame`.
                Assume required libraries like pandas and PyPDF2 are installed.
                Provide only the raw Python code, without markdown formatting or explanations.
                """
            )
        ]
        response = self.llm.invoke(messages)
        code = response.content.strip().replace("```python", "").replace("```", "")
        write_code_to_file(state["target_bank"], code)
        return {"generated_code": code}
