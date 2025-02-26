"""Second step of the workflow - Analysis and Chat."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from llmling_agent import ChatMessage
import streamlit as st

from components.sidebar import render_agent_sidebar
from components.state import state


if TYPE_CHECKING:
    from llmling_agent import Agent
    from streamlit.delta_generator import DeltaGenerator


async def process_chat_message(
    agent: Agent[None],
    prompt: str,
    message_placeholder: DeltaGenerator,
) -> str:
    """Process a chat message and stream the response."""
    response_parts: list[str] = []
    async with agent.run_stream(prompt) as stream:
        async for chunk in stream.stream():
            message_placeholder.markdown(chunk)
            response_parts.append(chunk)

    return "".join(response_parts)


async def main_async() -> None:
    """Async main function for Step 2."""
    # Check if we have form data
    if "completed_form" not in st.session_state:
        msg = "Keine Daten von Schritt 1 vorhanden. Bitte gehen Sie zurück zu Schritt 1."
        st.error(msg)
        if st.button("Zurück zu Schritt 1"):
            st.switch_page("pages/step1.py")
        return
    await state.initialize()
    st.title("Schritt 2: Analyse und Dialog")
    chat_agent = state.chat_agent
    render_agent_sidebar(chat_agent)
    with st.expander("Kontext aus Schritt 1", expanded=True):
        st.markdown(state.completed_form.format_context())
    # Display chat history
    for message in state.chat_messages:
        with st.chat_message(message.role):
            st.markdown(message.content)

    # Chat input
    if prompt := st.chat_input("Ihre Frage..."):
        # Add user message to chat history
        chat_message = ChatMessage(content=prompt, role="user")
        state.chat_messages.append(chat_message)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                # Prepare prompt with context for the first message
                if len(state.chat_messages) <= 1:
                    context = state.completed_form.format_context()
                    full_prompt = f"{context}\n\nFrage: {prompt}"
                else:
                    full_prompt = prompt

                # Stream the response
                with st.spinner("Denke nach..."):
                    full_response = await process_chat_message(
                        chat_agent,
                        full_prompt,
                        message_placeholder,
                    )
                msg = ChatMessage(content=full_response, role="assistant")
                state.chat_messages.append(msg)

        except Exception as e:  # noqa: BLE001
            error_msg = f"Ein Fehler ist aufgetreten: {e!s}"
            st.error(error_msg)


def main() -> None:
    """Main entry point for Step 2."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
