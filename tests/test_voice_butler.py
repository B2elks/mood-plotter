import json
from unittest.mock import patch, MagicMock

from voice_butler import analyze_response, ButlerResult


def _mock_chat_completion(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def test_analyze_response_parses_json_from_llm():
    fake = _mock_chat_completion(json.dumps({
        "image_prompt": "a peaceful forest in soft watercolor",
        "butler_ack": "Förträffligt min herre, kortet är på väg",
    }))

    with patch("voice_butler._call_openai", return_value=fake):
        result = analyze_response("Trött och stressad", api_key="k")

    assert isinstance(result, ButlerResult)
    assert result.image_prompt == "a peaceful forest in soft watercolor"
    assert result.butler_ack == "Förträffligt min herre, kortet är på väg"


def test_analyze_response_uses_fallback_on_empty_text():
    result = analyze_response("", api_key="k")
    assert "watercolor" in result.image_prompt.lower() or "landscape" in result.image_prompt.lower()
    assert "min herre" in result.butler_ack.lower() or "herre" in result.butler_ack.lower()


def test_analyze_response_uses_fallback_on_llm_error():
    with patch("voice_butler._call_openai", side_effect=RuntimeError("boom")):
        result = analyze_response("trött", api_key="k")

    assert result.image_prompt
    assert result.butler_ack


def test_analyze_response_uses_fallback_on_invalid_json():
    fake = _mock_chat_completion("not valid json at all")
    with patch("voice_butler._call_openai", return_value=fake):
        result = analyze_response("trött", api_key="k")

    assert result.image_prompt
    assert result.butler_ack
