"""
policy_search_tool.py
Full-text search across all policy documents stored in the DB.
Returns matching excerpts with document name and page number.
"""
import sqlite3
import os
import re
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get(
    "HACKATHON_DB",
    os.path.normpath(os.path.join(_HERE, "..", "..", "database", "hackathon", "hackathon.db"))
)


class PolicySearchTool:
    """Searches policy documents by keyword and returns relevant excerpts with page references."""

    def get_instructions(self) -> str:
        return (
            "Use this tool to search Cognizant policy documents. "
            "Provide a 'query' string. Returns matching policy document name, "
            "page number, and relevant text excerpt. Always cite document name and page number in responses."
        )

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", "")).strip()
        max_results = int(args.get("max_results", 5))

        if not query:
            return {"error": "query is required"}

        try:
            conn = sqlite3.connect(DB_PATH)

            # Build keyword search — split query into words
            keywords = [w.lower() for w in re.split(r'\W+', query) if len(w) > 2]
            if not keywords:
                return {"error": "Query too short or has no meaningful keywords"}

            # Score each page by how many keywords it contains
            rows = conn.execute(
                "SELECT document_name, page_number, page_text FROM policy_documents"
            ).fetchall()
            conn.close()

            scored = []
            for doc_name, page_num, text in rows:
                text_lower = text.lower()
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > 0:
                    scored.append((score, doc_name, page_num, text))

            if not scored:
                return {
                    "results": [],
                    "message": f"No policy documents found matching '{query}'."
                }

            # Sort by score descending, take top N
            scored.sort(key=lambda x: -x[0])
            results = []
            for score, doc_name, page_num, text in scored[:max_results]:
                # Extract a relevant snippet (~500 chars) around first keyword hit
                snippet = text[:600].replace('\n', ' ').strip()
                results.append({
                    "document_name": doc_name,
                    "page_number": page_num,
                    "relevance_score": score,
                    "excerpt": snippet,
                    "citation": f"[{doc_name}, Page {page_num}]"
                })

            return {
                "query": query,
                "total_matches": len(scored),
                "results": results,
                "instruction": "Always include document name and page number when citing policy information."
            }
        except Exception as e:
            return {"error": str(e)}
