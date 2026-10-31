import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="DocAgent", page_icon="📚", layout="wide")

# ---------- session state ----------
st.session_state.setdefault("messages", [])
st.session_state.setdefault("session_id", uuid.uuid4().hex)
st.session_state.setdefault("uploaded", set())


def api_online() -> bool:
    try:
        return requests.get(f"{API_URL}/health", timeout=3).status_code == 200
    except requests.RequestException:
        return False


def ask_api(question: str):
    """Returns (answer_text, tools_list)."""
    try:
        r = requests.post(
            f"{API_URL}/chat",
            json={"question": question, "session_id": st.session_state.session_id},
            timeout=120,
        )
        if r.status_code == 200:
            data = r.json()
            return data["response"], data.get("tools", [])
        return f"❌ Server error {r.status_code}: {r.text}", []
    except requests.Timeout:
        return "❌ The request timed out.", []
    except requests.RequestException as e:
        return f"❌ Cannot reach the API: {e}", []


# ---------- header ----------
st.title("📚 DocAgent - RAG Chatbot")
st.caption("Ask questions about your PDF documents. Ask for news or say ‘search the web’ to use web search.")

if not api_online():
    st.error("FastAPI server is not running.")
    st.code("python main.py")
    if st.button("🔄 Retry"):
        st.rerun()
    st.stop()

# ---------- sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("📤 Upload document")
    pdf = st.file_uploader("Choose a PDF", type="pdf")

    if pdf is not None:
        key = f"{pdf.name}:{pdf.size}"
        if key not in st.session_state.uploaded:   # upload once, not on every rerun
            with st.spinner("Indexing document..."):
                try:
                    r = requests.post(
                        f"{API_URL}/upload",
                        files={"file": (pdf.name, pdf.getvalue(), "application/pdf")},
                        timeout=300,
                    )
                    if r.status_code == 200:
                        st.session_state.uploaded.add(key)
                        st.success(f"✓ Indexed {r.json().get('chunks', '?')} chunks")
                    else:
                        st.error(r.json().get("detail", r.text))
                except requests.RequestException as e:
                    st.error(f"Upload failed: {e}")
        else:
            st.success("✓ Document ready")

    st.divider()
    st.subheader("📊 Indexed documents")
    try:
        docs = requests.get(f"{API_URL}/documents", timeout=5).json().get("documents", [])
        for d in docs:
            st.write(f"📄 {d}")
        if not docs:
            st.info("No documents indexed yet")
    except Exception:
        st.warning("Could not load documents")

    st.divider()
    if st.button("🧹 Clear chat"):
        st.session_state.messages = []
        st.session_state.session_id = uuid.uuid4().hex
        st.rerun()

# ---------- chat ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("tools"):
            st.caption("🔧 Tools: " + ", ".join(m["tools"]))

if prompt := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, tools = ask_api(prompt)
            answer = answer.replace("$", "\\$")
        st.markdown(answer)
        if tools:
            st.caption("🔧 Tools: " + ", ".join(tools))

    st.session_state.messages.append({"role": "assistant", "content": answer, "tools": tools})
