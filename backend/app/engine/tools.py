"""
Tool Implementations
Actual tool handlers for built-in tools
"""
from typing import Dict, Any, List, Optional
import httpx
import json
from duckduckgo_search import DDGS


# ========== Tool Definitions (OpenAI function calling format) ==========

TOOL_DEFINITIONS = {
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo and return relevant results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    "rag_search": {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Search a knowledge base for relevant documents",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "ID of the knowledge base to search"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    "file_reader": {
        "type": "function",
        "function": {
            "name": "file_reader",
            "description": "Read and parse file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "Type of file (text, csv, json)"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    "api_caller": {
        "type": "function",
        "function": {
            "name": "api_caller",
            "description": "Make HTTP API calls to external services",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The API endpoint URL"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE)",
                        "enum": ["GET", "POST", "PUT", "DELETE"]
                    },
                    "headers": {
                        "type": "object",
                        "description": "Request headers"
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body for POST/PUT"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters"
                    }
                },
                "required": ["url"]
            }
        }
    },
    "data_analyzer": {
        "type": "function",
        "function": {
            "name": "data_analyzer",
            "description": "Analyze data and generate statistics/insights",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Array of data objects to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis: summary, statistics, trends",
                        "enum": ["summary", "statistics", "trends"]
                    }
                },
                "required": ["data"]
            }
        }
    },
    "text_summarizer": {
        "type": "function",
        "function": {
            "name": "text_summarizer",
            "description": "Generate a summary of the given text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to summarize"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum summary length in words (default: 200)"
                    }
                },
                "required": ["text"]
            }
        }
    }
}


# ========== Tool Handlers ==========

async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search the web using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        return {"error": str(e), "query": query, "results": []}


async def rag_search(
    query: str,
    knowledge_base_id: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Search a knowledge base (placeholder - integrate with ChromaDB)"""
    # TODO: Integrate with ChromaDB for actual vector search
    return {
        "query": query,
        "knowledge_base_id": knowledge_base_id,
        "documents": [],
        "message": "RAG search not yet configured. Add documents to a knowledge base first."
    }


async def file_reader(file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
    """Read and parse file contents"""
    import os
    
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    try:
        # Auto-detect file type
        if not file_type:
            ext = os.path.splitext(file_path)[1].lower()
            file_type = ext[1:] if ext else "text"
        
        if file_type == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            return {"content": content, "file_type": "json"}
        
        elif file_type == "csv":
            import csv
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return {"content": rows, "file_type": "csv", "row_count": len(rows)}
        
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content, "file_type": "text", "length": len(content)}
    
    except Exception as e:
        return {"error": str(e), "file_path": file_path}


async def api_caller(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Make HTTP API calls"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=body if method.upper() in ["POST", "PUT", "PATCH"] else None,
                params=params
            )
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return {
            "status_code": response.status_code,
            "response": response_data,
            "headers": dict(response.headers)
        }
    
    except Exception as e:
        return {"error": str(e), "url": url}


async def data_analyzer(
    data: List[Dict[str, Any]],
    analysis_type: str = "summary"
) -> Dict[str, Any]:
    """Analyze data and generate insights"""
    if not data:
        return {"error": "No data provided"}
    
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        
        if analysis_type == "summary":
            return {
                "row_count": len(df),
                "columns": list(df.columns),
                "sample": df.head(5).to_dict(orient="records"),
                "dtypes": {k: str(v) for k, v in df.dtypes.items()}
            }
        
        elif analysis_type == "statistics":
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            stats = {}
            for col in numeric_cols:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "std": float(df[col].std())
                }
            return {"statistics": stats, "numeric_columns": numeric_cols}
        
        elif analysis_type == "trends":
            return {
                "row_count": len(df),
                "columns": list(df.columns),
                "message": "Trend analysis requires time-series data with a date column"
            }
        
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    except Exception as e:
        return {"error": str(e)}


async def text_summarizer(text: str, max_length: int = 200) -> Dict[str, Any]:
    """Summarize text (simple extraction-based)"""
    if not text:
        return {"error": "No text provided"}
    
    # Simple extractive summary (first N words)
    words = text.split()
    if len(words) <= max_length:
        return {"summary": text, "original_length": len(words)}
    
    summary = " ".join(words[:max_length]) + "..."
    return {
        "summary": summary,
        "original_length": len(words),
        "summary_length": max_length
    }


# ========== Tool Registry Functions ==========

def get_tool_definitions(tool_names: List[str]) -> List[Dict]:
    """Get OpenAI-format tool definitions for the given tool names"""
    definitions = []
    for name in tool_names:
        if name in TOOL_DEFINITIONS:
            definitions.append(TOOL_DEFINITIONS[name])
    return definitions


def get_tool_handlers(tool_names: List[str]) -> Dict[str, callable]:
    """Get handler functions for the given tool names"""
    handlers = {
        "web_search": web_search,
        "rag_search": rag_search,
        "file_reader": file_reader,
        "api_caller": api_caller,
        "data_analyzer": data_analyzer,
        "text_summarizer": text_summarizer
    }
    
    return {name: handlers[name] for name in tool_names if name in handlers}
