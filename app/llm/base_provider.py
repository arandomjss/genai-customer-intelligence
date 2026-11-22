"""
Base interface for LLM providers.

The extraction pipeline should depend on this interface rather than
directly depending on a specific LLM provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLLMProvider(ABC):
    """Common interface for all LLM providers."""

    @abstractmethod
    def extract(
        self,
        review_text: str,
        review_id: str | None = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from a review.

        Parameters
        ----------
        review_text:
            Customer review text.

        review_id:
            Optional identifier for logging/debugging.

        Returns
        -------
        Dict[str, Any]
            Structured extraction result.
        """
        raise NotImplementedError
