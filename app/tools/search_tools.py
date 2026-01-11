from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

@tool
def web_search_product(query: str):
    """
    Search the web for product reviews, characteristics, or comparisons.
    Use this when the internal catalog info is not enough.
    """
    # Tavily is optimized for agents
    search = TavilySearchResults(max_results=3)
    try:
        results = search.invoke(query)
        # Summarize or return raw results for the LLM to digest
        formatted = "\n".join([f"- [{r['url']}] {r['content']}" for r in results])
        return f"Resultados de la web:\n{formatted}"
    except Exception as e:
        return f"Error en la búsqueda web: {str(e)}"
