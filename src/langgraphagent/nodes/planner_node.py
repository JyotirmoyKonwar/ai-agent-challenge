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
                1.  You must create a function `parse(pdf_path: str) -> pd.DataFrame`.
                2.  This function will be saved in `custom_parsers/{state['target_bank']}_parser.py`.
                3.  The function will be tested against `data/{state['target_bank']}/{state['target_bank']}_sample.pdf`.
                4.  The output DataFrame must exactly match `data/{state['target_bank']}/{state['target_bank']}_sample.csv`.

                Create a concise, step-by-step plan to generate and validate the code. Do not write the code itself yet.
                """
            )
        ]
        response = self.llm.invoke(messages)
        return {"plan": response.content}
