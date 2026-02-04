"""
Data models for the Methane Mask Annotator.

Contains Shape, SyringeVersion, and AnnotationSession classes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Set, Tuple

import numpy as np


@dataclass
class Shape:
    """Represents a drawn shape (polygon, freehand path, rectangle, or brush)."""
    shape_type: str  # 'polygon', 'freehand', 'rectangle', 'brush'
    points: List[Tuple[int, int]]  # List of (x, y) coordinates
    radius: Optional[int] = None  # Only for 'brush' type

    def to_numpy(self) -> np.ndarray:
        """Convert points to numpy array for cv2.fillPoly."""
        return np.array(self.points, dtype=np.int32)


@dataclass
class SyringeVersion:
    """A syringe mask version that applies from a specific image index."""
    start_index: int  # Image index from which this syringe applies
    shapes: List[Shape] = field(default_factory=list)

    def to_dict(self) -> dict:
        shapes_data = []
        for s in self.shapes:
            shape_dict = {"type": s.shape_type, "points": s.points}
            if s.radius is not None:
                shape_dict["radius"] = s.radius
            shapes_data.append(shape_dict)
        return {
            "start_index": self.start_index,
            "shapes": shapes_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SyringeVersion':
        shapes = []
        for s in data.get("shapes", []):
            shape = Shape(
                shape_type=s["type"],
                points=[tuple(p) for p in s["points"]],
                radius=s.get("radius")
            )
            shapes.append(shape)
        return cls(
            start_index=data.get("start_index", 0),
            shapes=shapes
        )


@dataclass
class AnnotationSession:
    """Holds the current annotation session state."""
    images_folder: str = ""
    masks_folder: str = ""
    image_list: List[str] = field(default_factory=list)
    current_index: int = 0
    syringe_versions: List[SyringeVersion] = field(default_factory=list)
    skipped_images: Set[str] = field(default_factory=set)
    review_images: Set[str] = field(default_factory=set)

    def get_syringe_for_index(self, index: int) -> List[Shape]:
        """Get the syringe shapes that apply to a given image index."""
        if not self.syringe_versions:
            return []

        # Find the version with the highest start_index that is <= index
        applicable_version = None
        for version in self.syringe_versions:
            if version.start_index <= index:
                if applicable_version is None or version.start_index > applicable_version.start_index:
                    applicable_version = version

        return applicable_version.shapes if applicable_version else []

    def add_syringe_version(self, start_index: int, shapes: List[Shape]):
        """Add a new syringe version starting from the given index."""
        # Remove any existing version at this exact index
        self.syringe_versions = [v for v in self.syringe_versions if v.start_index != start_index]
        # Add new version
        self.syringe_versions.append(SyringeVersion(start_index=start_index, shapes=shapes))
        # Sort by start_index
        self.syringe_versions.sort(key=lambda v: v.start_index)

    def clear_current_syringe(self, current_index: int):
        """Clear the syringe version that applies to the current index."""
        applicable = None
        for version in self.syringe_versions:
            if version.start_index <= current_index:
                if applicable is None or version.start_index > applicable.start_index:
                    applicable = version

        if applicable:
            self.syringe_versions.remove(applicable)

    def to_dict(self) -> dict:
        """Convert session to dictionary for JSON serialization."""
        return {
            "images_folder": self.images_folder,
            "masks_folder": self.masks_folder,
            "current_index": self.current_index,
            "syringe_versions": [v.to_dict() for v in self.syringe_versions],
            "skipped_images": list(self.skipped_images),
            "review_images": list(self.review_images),
            "last_saved": datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AnnotationSession':
        """Create session from dictionary."""
        session = cls()
        session.images_folder = data.get("images_folder", "")
        session.masks_folder = data.get("masks_folder", "")
        session.current_index = data.get("current_index", 0)

        # Handle both old format (syringe_shapes) and new format (syringe_versions)
        if "syringe_versions" in data:
            session.syringe_versions = [
                SyringeVersion.from_dict(v) for v in data.get("syringe_versions", [])
            ]
        elif "syringe_shapes" in data:
            # Migrate old format: treat old shapes as version starting at index 0
            old_shapes = [
                Shape(shape_type=s["type"], points=[tuple(p) for p in s["points"]])
                for s in data.get("syringe_shapes", [])
            ]
            if old_shapes:
                session.syringe_versions = [SyringeVersion(start_index=0, shapes=old_shapes)]

        session.skipped_images = set(data.get("skipped_images", []))
        session.review_images = set(data.get("review_images", []))
        return session
