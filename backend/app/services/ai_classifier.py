from abc import ABC, abstractmethod
from typing import Any, Dict, List

class AIClassifierProvider(ABC):
    @abstractmethod
    def classify_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image and return classification results.
        Returns:
            Dict containing:
                - category (str)
                - confidence (float)
                - detections (List[Dict])
        """
        pass

class YOLOv8Classifier(AIClassifierProvider):
    SUPPORTED_CATEGORIES = [
        "Plastic",
        "Paper",
        "Glass",
        "Metal",
        "Cardboard",
        "E-Waste",
        "Battery",
        "Unknown"
    ]

    def classify_image(self, image_path: str) -> Dict[str, Any]:
        # TODO: Implement actual YOLOv8 inference here.
        # For now, returning a mock response as required (Do not call AI yet).
        
        mock_category = "Unknown"
        mock_confidence = 0.0
        mock_detections = []
        
        return {
            "category": mock_category,
            "confidence": mock_confidence,
            "detections": mock_detections,
        }

def get_classifier() -> AIClassifierProvider:
    return YOLOv8Classifier()
