from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np


class Vector:
    """
    Represents an embedding with metadata.
    """

    def __init__(self, values: List[float], model_name: str):
        self.values = np.array(
            values, dtype=np.float32
        )  # Convert to NumPy array for numerical operations
        self.model_name = model_name
        self.size = len(values)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the vector to a dictionary for storage or serialization."""
        return {
            "model_name": self.model_name,
            "size": self.size,
            "values": self.values.tolist(),  # Convert back to list for serialization
        }

    def __repr__(self) -> str:
        return f"Vector(size={self.size}, model_name={self.model_name})"


class BaseEmbeddingModel(ABC):
    """
    Abstract base class for embedding models. All embedding models should inherit from this.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[Vector]:
        """
        Generate embeddings for a list of text inputs.
        """
        pass

    def __repr__(self) -> str:
        return f"BaseEmbeddingModel(model_name={self.model_name})"
