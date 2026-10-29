"""streamlit_app.py — the browser chat UI for our agent."""

import streamlit as st

from app.agent import ask_agent

st.set_page_config(page_title="TechStore Assistant", page_icon="🛍️")
st.title("🛍️ TechStore Assistant")
st.caption("Ask me about our products (prices, stock, brands) or our policies (shipping, returns, warranty).")

mode_label = st.sidebar.radio(
    "Mode de réponse",
    ("Local — sans IA", "OpenAI — clé API requise"),
    index=0,
)
mode = "local" if mode_label.startswith("Local") else "openai"
if mode == "local":
    st.sidebar.caption("La FAQ et la base locale sont utilisées. Aucun appel réseau n'est effectué.")
else:
    st.sidebar.caption("Ce mode nécessite une clé OpenAI valide.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about products or policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_agent(prompt, mode=mode)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
