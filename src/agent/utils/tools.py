from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import tool
from langchain_docling.loader import DoclingLoader

search_tool = DuckDuckGoSearchResults(
    num_results=10,
)


@tool
def search_wikipedia(topic: str) -> str:
    """
    Search Wikipedia for a given topic.
    Use this tool to retrieve detailed background information, factual summaries, 
    and context about people, places, or concepts.
    """
    # Loading max 3 docs to control context window usage
    docs = WikipediaLoader(query=topic, load_max_docs=3).load()
    
    # Return a clean string representation for the LLM
    return "\n\n".join([d.page_content for d in docs])

@tool
def read_webpage(url: str) -> str:
    """
    Load and parse a document from a given URL.
    Use this tool to extract structured text and content from web pages.
    """
    docs = DoclingLoader(file_path=url).load()
    
    # Return the content of the parsed document
    return "\n\n".join([d.page_content for d in docs])