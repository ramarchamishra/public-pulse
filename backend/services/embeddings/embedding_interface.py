from abc import ABC, abstractmethod

import numpy as np


class EmbeddingInterface(ABC):

    @abstractmethod
    def encode(
        self,
        texts: list[str]
    ) -> np.ndarray:
        """
        Convert text into vector embeddings.
        """
        pass