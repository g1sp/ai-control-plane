"""Claude API integration."""

import os
from anthropic import Anthropic
from ..config import settings


class ClaudeClient:
    """Client for querying Claude via Anthropic API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.claude_api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not set")
        self.client = Anthropic(api_key=self.api_key)

    def query(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """
        Query Claude API.

        Returns: (response_text, tokens_in, tokens_out)
        """
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )

            response_text = message.content[0].text
            tokens_in = message.usage.input_tokens
            tokens_out = message.usage.output_tokens

            return response_text, tokens_in, tokens_out

        except Exception as e:
            raise Exception(f"Claude query failed: {str(e)}")

    def validate_api_key(self) -> bool:
        """Validate API key is correct."""
        try:
            self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hi"},
                ],
            )
            return True
        except Exception:
            return False
