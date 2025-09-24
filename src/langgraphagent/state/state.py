from typing import TypedDict, Optional

class State(TypedDict):
    """
    Representing the structure of the state used in the agent graph.
    """
    target_bank: str
    task: str
    plan: str
    generated_code: str
    test_results: str
    error_message: Optional[str]
    retries_left: int
