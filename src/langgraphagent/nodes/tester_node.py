from src.langgraphagent.state.state import State
from src.langgraphagent.tools.test_tools import run_tests

class TesterNode:
    """
    Node 3: The Tester
    Runs the tests on the generated code.
    """
    def __init__(self):
        pass

    def process(self, state: State) -> dict:
        """
        Executes tests against the generated code.
        """
        print("--- TESTING CODE ---")
        results = run_tests(state["target_bank"])
        print(f"Test Results: {results}")

        if "successfully" in results:
            return {"error_message": None, "test_results": results}
        else:
            return {"error_message": results, "test_results": results}
