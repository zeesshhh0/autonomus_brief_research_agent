from src.agent.utils.state import AgentState
from src.agent.utils.nodes import research_node

from dotenv import load_dotenv

load_dotenv()


def test_research_node():
  state = {"topic": "AI", "research_constraints": {"audience": "Engineer"}}
  output = research_node(state)
  assert type(output) == dict
  
  return output

test_research_node()