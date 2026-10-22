"""Streamlit chat interface for the elementary math tutor."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import configure_logging, load_config
from app.inference import MultiTurnMathSession
from app.model_loader import load_model
from app.prompts import PROMPT_MODES

configure_logging()
st.set_page_config(page_title="Gia s\u01b0 To\u00e1n ti\u1ec3u h\u1ecdc", page_icon="\U0001f4da")
st.title("Gia s\u01b0 To\u00e1n ti\u1ec3u h\u1ecdc")


@st.cache_resource(show_spinner=False)
def get_model():
    config = load_config()
    return config, *load_model(config)


def reset_session(mode: str) -> None:
    config, model, tokenizer = get_model()
    st.session_state.chat_session = MultiTurnMathSession(model, tokenizer, PROMPT_MODES[mode], config)
    st.session_state.chat_history = []
    st.session_state.mode = mode


config, model, tokenizer = get_model()
mode_options = list(PROMPT_MODES)
selected_mode = st.selectbox("Ch\u1ebf \u0111\u1ed9 h\u1ecdc", mode_options, key="selected_mode")
if "chat_session" not in st.session_state:
    reset_session(selected_mode)
elif st.session_state.get("mode") != selected_mode:
    reset_session(selected_mode)

if st.button("L\u00e0m m\u1edbi h\u1ed9i tho\u1ea1i", type="secondary"):
    reset_session(selected_mode)
    st.rerun()

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_text = st.chat_input("Nh\u1eadp \u0111\u1ec1 b\u00e0i ho\u1eb7c c\u00e2u tr\u1ea3 l\u1eddi ti\u1ebfp theo c\u1ee7a em...")
if user_text:
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Gia s\u01b0 AI \u0111ang so\u1ea1n c\u00e2u g\u1ee3i \u00fd c\u1ee5 th\u1ec3..."):
            response = st.session_state.chat_session.send_message(user_text)
        st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
