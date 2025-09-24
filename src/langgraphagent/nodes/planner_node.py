from langchain_core.messages import HumanMessage
from src.langgraphagent.state.state import State

class PlannerNode:
    """
    Node 1: The Planner
    Creates a step-by-step plan to write and test the parser.
    """
    def __init__(self, model):
        self.llm = model

    def process(self, state: State) -> dict:
        """
        Processes the current state to generate a plan.
        """
        print("--- PLANNING ---")
        messages = [
            HumanMessage(
                content=f"""Your task is to create a Python script that parses a PDF bank statement for '{state['target_bank']}'.

                Here is the context:
                1.  The parser must first analyze the PDF to **find the transaction table headers** (e.g., 'Date', 'Description', 'Debit Amt', etc.) and then extract the data. The column names must be derived from the PDF itself.
                2.  You must create a function `parse(pdf_path: str) -> pd.DataFrame`.
                3.  This function will be saved in `custom_parsers/{state['target_bank']}_parser.py`.
                4.  The final output DataFrame must exactly match the data in `data/{state['target_bank']}/result.csv`.
                5.  You must use the `pdfplumber` library for parsing the PDF.

                Create a concise, step-by-step plan to implement this intelligent parsing logic. Do not write the code itself yet.
                """
            )
        ]
        response = self.llm.invoke(messages)
        return {"plan": response.content}

