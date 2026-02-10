from __future__ import annotations

from abc import ABC, abstractmethod
from siva_guard.core.schema import IdentityClaim, IdentityEvidence


class Connector(ABC):
    @abstractmethod
    def supports(self, claim: IdentityClaim) -> bool:
        ...

    @abstractmethod
    def collect(self, claim: IdentityClaim) -> IdentityEvidence:
        """
        Best-effort collection.
        Must not raise exceptions; store errors in IdentityEvidence.errors.
        """
        ...
