from app.api.chat import ChatRequest
from uuid import UUID
import pytest


def test_chat_request_valid():
    request = ChatRequest(
        session_id=UUID("00000000-0000-0000-0000-000000000000"),
        message="How can I improve activation?"
    )

    assert request.message == "How can I improve activation?"


def test_chat_request_rejects_empty_message():
    with pytest.raises(Exception):
        ChatRequest(
            session_id=UUID("00000000-0000-0000-0000-000000000000"),
            message=""
        )


def test_chat_request_rejects_long_message():
    with pytest.raises(Exception):
        ChatRequest(
            session_id=UUID("00000000-0000-0000-0000-000000000000"),
            message="a" * 5001
        )
