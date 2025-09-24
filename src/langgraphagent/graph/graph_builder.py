from langgraph.graph import StateGraph, END, START
from src.langgraphagent.state.state import State
from src.langgraphagent.nodes.planner_node import PlannerNode
from src.langgraphagent.nodes.coder_node import CoderNode
from src.langgraphagent.nodes.tester_node import TesterNode
from src.langgraphagent.nodes.corrector_node import CorrectorNode

def should_continue(state: State) -> str:
    """
    Conditional Edge: Decides whether to end, retry, or declare failure.
    """
    if state.get("error_message") is None:
        print("--- TASK COMPLETE ---")
        return "end"
    elif state.get("retries_left", 0) > 0:
        print(f"--- RETRYING ({state['retries_left']} attempts left) ---")
        return "continue"
    else:
        print("--- TASK FAILED (Max retries reached) ---")
        return "end"

class GraphBuilder:
    """
    Builds the LangGraph agent graph.
    """
    def __init__(self, model):
        self.llm = model
        self.graph_builder = StateGraph(State)

    def build_graph(self):
        """
        Constructs the agent graph by defining nodes and edges.
        """
        # Initialize node classes
        planner_node = PlannerNode(self.llm)
        coder_node = CoderNode(self.llm)
        tester_node = TesterNode()
        corrector_node = CorrectorNode(self.llm)

        # Add nodes to the graph
        self.graph_builder.add_node("planner", planner_node.process)
        self.graph_builder.add_node("coder", coder_node.process)
        self.graph_builder.add_node("tester", tester_node.process)
        self.graph_builder.add_node("corrector", corrector_node.process)

        # Define the graph's flow (edges)
        self.graph_builder.add_edge(START, "planner")
        self.graph_builder.add_edge("planner", "coder")
        self.graph_builder.add_edge("coder", "tester")
        self.graph_builder.add_conditional_edges(
            "tester",
            should_continue,
            {
                "continue": "corrector",
                "end": END,
            },
        )
        self.graph_builder.add_edge("corrector", "tester")

        # Compile and return the graph
        return self.graph_builder.compile()
