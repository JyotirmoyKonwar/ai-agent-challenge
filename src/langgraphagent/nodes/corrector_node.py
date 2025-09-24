from langchain_core.messages import HumanMessage
from src.langgraphagent.state.state import State
from src.langgraphagent.tools.file_tools import write_code_to_file

class CorrectorNode:
    """
    Node 4: The Corrector
    If tests fail, this node analyzes the error and proposes a fix.
    """
    def __init__(self, model):
        self.llm = model

    def process(self, state: State) -> dict:
        """
        Analyzes test errors and generates corrected code.
        """
        print("--- SELF-CORRECTING ---")
        retries = state.get("retries_left", 0) - 1
        messages = [
            HumanMessage(
                content=f"""The Python code you generated has failed the tests.

                **Crucial Instruction:** The parser must dynamically identify the table headers (like 'Date', 'Description', 'Debit Amt', etc.) from the PDF content itself before extracting the rows. Do not use a hardcoded list of columns. The final DataFrame must match the structure of `data/{state["target_bank"]}/result.csv`.

                Original Plan: {state['plan']}
                Your Code:
                ```python
                {state['generated_code']}
                ```
                Test Error Message: '{state['error_message']}'

                Analyze the error and the code. Then, write a new, corrected version of the Python code that correctly identifies headers from the PDF.
                Provide only the raw Python code, without markdown formatting or explanations.
                Your goal is to fix the bug so the tests will pass.
                """
            )
        ]
        response = self.llm.invoke(messages)
        code = response.content.strip().replace("```python", "").replace("```", "")
        write_code_to_file(state["target_bank"], code)
        return {"generated_code": code, "retries_left": retries}

