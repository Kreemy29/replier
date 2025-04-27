import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
from app.services.reply import make_reply
from app.config import FALLBACK_COMMENTS

@pytest.fixture
def mock_post():
    return {
        "postId": "123",
        "original": {"username": "test_user", "text": "Original post"},
        "target": {"username": "target_user", "text": "Target comment"}
    }

@pytest.mark.asyncio
async def test_fallback_without_api_key(monkeypatch, mock_post):
    monkeypatch.setattr("app.config.DEEPSEEK_API_KEY", None)
    response = await make_reply(mock_post)
    assert response in FALLBACK_COMMENTS

@pytest.mark.asyncio
async def test_api_error_fallback(mocker, mock_post):
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(side_effect=aiohttp.ClientError())
    mocker.patch("aiohttp.ClientSession", return_value=mock_session)
    
    response = await make_reply(mock_post)
    assert response in FALLBACK_COMMENTS
