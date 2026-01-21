from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools import DuckDuckGoSearchResults


search_tool = DuckDuckGoSearchResults(
    num_results=10,
)