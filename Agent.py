import os
import re

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from datetime import date

load_dotenv()

from RAG import retriever  # noqa: E402  (importing RAG initialises the vector store)

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
NO_DOC_RESULT = "NO_RELEVANT_DOCUMENT_CONTENT"
WEB_UNAVAILABLE = "WEB_SEARCH_UNAVAILABLE"


WEB_PATTERN = re.compile(
    r"\b(news|search the web|search online|on the internet|google|"
    r"up[- ]to[- ]date|right now|latest news|today'?s news)\b",
    re.IGNORECASE,
)
GREETING_RE = re.compile(r"^\s*(hi|hy|hey|hello|salam|assalam\W*o?\W*alaikum)\W*$", re.IGNORECASE)

DOC_PATTERN = re.compile(
    r"\b(my|this|the)\s+(cv|resume|document|pdf|file|paper|report)\b|\bmy\b",
    re.IGNORECASE,
)

def needs_web(question: str) -> bool:
    if DOC_PATTERN.search(question):
        return False
    return bool(WEB_PATTERN.search(question))


# ============ TOOLS ============

@tool
def search_docs(query: str) -> str:
    """Search the uploaded PDF documents and return the most relevant passages."""
    docs = retriever.invoke(query)
    seen, parts = set(), []
    for d in docs:
        text = d.page_content.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        source = d.metadata.get("source", "document")
        page = d.metadata.get("page_label", d.metadata.get("page", "?"))
        parts.append(f"[{source}, page {page}]\n{text}")
    return "\n\n".join(parts) if parts else NO_DOC_RESULT


@tool
def web_search(query: str) -> str:
    """Search the web for current / recent information."""
    if not os.getenv("SERPER_API_KEY"):
        return f"{WEB_UNAVAILABLE}: SERPER_API_KEY is not set."
    try:
        from langchain_community.utilities import GoogleSerperAPIWrapper
        return GoogleSerperAPIWrapper().run(query)
    except Exception as e:  # network / quota / etc.
        return f"{WEB_UNAVAILABLE}: {e}"


# ============ AGENT ============

SYSTEM_PROMPT = """You are DocAgent, a question-answering assistant for uploaded PDF documents.
You are given the user's question and an Observation containing search results.

Rules:
- Answer ONLY from the Observation. Do not add facts, examples or numbers that are not in it.
- If the Observation does not contain the answer, say: "I couldn't find that in the document."
- If the Observation comes from a web search, say the information comes from the web.
- Today's date is {today}. Treat a job or role as current only if its end date is "Present"/"Current" or is after today's date. Otherwise say it is the most recent role and that it ended.
- Address the user as "you" and refer to "the document" (or "your CV"). Never say "I am" about the user's details.
- Be concise."""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT.replace("{today}", date.today().strftime("%B %d, %Y"))

TOOL_RE = re.compile(r"TOOL:\s*([A-Za-z_]+)", re.IGNORECASE)
INPUT_RE = re.compile(r"INPUT:\s*(.+)", re.IGNORECASE)
NOISE_RE = re.compile(r"^\s*(TOOL|INPUT|Action|Action Input|Observation|Thought)\s*:.*$", re.IGNORECASE)


class RoutedAgent:
    def __init__(self, max_iterations: int = 3):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is missing - add it to your .env file")
        self.llm = ChatGroq(model=GROQ_MODEL, api_key=key, temperature=0)
        self.tools = {"search_docs": search_docs, "web_search": web_search}
        self.max_iterations = max_iterations
        print("✓ Manual Routed Agent initialized")

    # ---- helpers ----
    @staticmethod
    def route(question: str) -> str:
        return "web_search" if needs_web(question) else "search_docs"
    @staticmethod
    def parse_tool_call(text: str):
        tool_m, input_m = TOOL_RE.search(text), INPUT_RE.search(text)
        if not tool_m:
            return None
        name = tool_m.group(1).strip().lower()
        query = input_m.group(1).strip().strip("\"'") if input_m else ""
        return name, query

    @staticmethod
    def clean(text: str) -> str:
        lines = [ln for ln in text.splitlines() if not NOISE_RE.match(ln)]
        out = "\n".join(lines).strip()
        return re.sub(r"^Final Answer:\s*", "", out, flags=re.IGNORECASE).strip()

    def _think(self, question: str, scratchpad: str) -> str:
        human = f"Question: {question}"
        if scratchpad:
            human += f"\n\n{scratchpad}\nNow answer the question using only the Observation above."
        return self.llm.invoke([("system", build_system_prompt()), ("human", human)]).content

    @staticmethod
    def _labels(tools_used):
        icons = {"search_docs": "📄 search_docs", "web_search": "🌐 web_search"}
        return [icons.get(t, t) for t in tools_used]

    # ---- main entry ----
    def ask(self, question: str) -> tuple:
        """Returns (answer, tools_used, success)."""
        try:
            if GREETING_RE.match(question):
                return "Hello! How can I help you with your documents today?", [], True
            
            name = self.route(question)
            observation = self.tools[name].invoke(question)
            tools_used = [name]

            if observation == NO_DOC_RESULT:
                return "I couldn't find that in the document.", self._labels(tools_used), True
            if observation.startswith(WEB_UNAVAILABLE):
                return ("Web search isn't available right now. "
                        "Set SERPER_API_KEY in .env to enable it."), self._labels(tools_used), True

            scratchpad = f"Observation (from {name}):\n{observation}\n"
            answer = self._think(question, scratchpad)
            return self.clean(answer), self._labels(tools_used), True
        except Exception as e:
            return f"Error: {e}", [], False


agent = RoutedAgent()


# ============ CLI ============

if __name__ == "__main__":
    print("DocAgent CLI - type 'exit' to quit")
    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit", "bye"}:
            break
        answer, used, ok = agent.ask(q)
        print(f"\nAgent: {answer}\nTools: {', '.join(used)}\n")
