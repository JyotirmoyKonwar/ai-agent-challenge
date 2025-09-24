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
                
                **Critical Instructions:**
                1.  **Use the `pdfplumber` library.**
                2.  **Your code must first scan the PDF text to dynamically locate the transaction table and identify its headers.** Do not hardcode column names like ['Date', 'Description', ...].
                3.  Once the headers are found, use them to structure the extracted transaction data into a pandas DataFrame.
                4.  The code must be a single block to be written to `custom_parsers/{state['target_bank']}_parser.py`.
                5.  It must contain the function `parse(pdf_path: str) -> pd.DataFrame`.

                Provide only the raw Python code, without any markdown formatting or explanations.
                """
            )
        ]
        response = self.llm.invoke(messages)
        code = response.content.strip().replace("```python", "").replace("```", "")
        write_code_to_file(state["target_bank"], code)
        return {"generated_code": code}

