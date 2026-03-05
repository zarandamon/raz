# raz/core/domain/models.py
# Canonical core models (no *Ref classes for now).
# Keep these pure: no DB, no vendor SDKs, no filesystem logic.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Literal


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


EntityType = str  # e.g. "shot", "asset", "sequence", "folder", "video", "image"
DccName = str     # e.g. "houdini", "maya", "blender", "unreal", "nuke"


# ---------------------------------------------------------------------------
# Core identity models
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str
    root: str  # filesystem path as string (no pathlib to keep cross-host simple)
    settings: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Project.id must be non-empty")
        if not self.name:
            raise ValueError("Project.name must be non-empty")
        if not self.root:
            raise ValueError("Project.root must be non-empty")


@dataclass(frozen=True, slots=True)
class User:
    id: str
    name: str
    email: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("User.id must be non-empty")
        if not self.name:
            raise ValueError("User.name must be non-empty")


# ---------------------------------------------------------------------------
# Production tracking models
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Entity:
    """
    Generic entity to support: shots, assets, sequences, folders, videos, etc.
    Keep it generic; specialize later via helper APIs or type registries.
    """
    id: str
    project_id: str
    type: EntityType
    name: str
    parent_id: Optional[str] = None  # sequence->shot, folder->asset, etc.
    data: Dict[str, Any] = field(default_factory=dict)  # custom attributes
    meta: Dict[str, Any] = field(default_factory=dict)  # vendor IDs, etc.

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Entity.id must be non-empty")
        if not self.project_id:
            raise ValueError("Entity.project_id must be non-empty")
        if not self.type:
            raise ValueError("Entity.type must be non-empty")
        if not self.name:
            raise ValueError("Entity.name must be non-empty")


@dataclass(frozen=True, slots=True)
class Task:
    """
    Task tied to an entity + step/task naming.
    In early phases you can keep status as a free string.
    """
    id: str
    project_id: str
    entity_id: str
    step: str         # e.g. "light"
    name: str         # e.g. "main"
    status: str = "todo"
    assignee_ids: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Task.id must be non-empty")
        if not self.project_id:
            raise ValueError("Task.project_id must be non-empty")
        if not self.entity_id:
            raise ValueError("Task.entity_id must be non-empty")
        if not self.step:
            raise ValueError("Task.step must be non-empty")
        if not self.name:
            raise ValueError("Task.name must be non-empty")


# ---------------------------------------------------------------------------
# Context (runtime "where am I")
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Context:
    """
    Runtime context used by engine/apps/services.
    Keep it lightweight and serializable.
    """
    project_id: str
    entity_id: Optional[str] = None
    step: str = "master"
    task: str = "main"
    user_id: Optional[str] = None
    profile: str = "local"  # e.g. local / delegated / studio / remote
    meta: Dict[str, Any] = field(default_factory=dict)  # vendor IDs, etc.

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("Context.project_id must be non-empty")
        if not self.step:
            raise ValueError("Context.step must be non-empty")
        if not self.task:
            raise ValueError("Context.task must be non-empty")


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    """
    Stored/serialized version of Context for DB records, manifests, etc.
    Same fields as Context, but used as "write once" snapshot.
    """
    project_id: str
    entity_id: Optional[str]
    step: str
    task: str
    user_id: Optional[str]
    profile: str
    meta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_context(cls, ctx: Context) -> "ContextSnapshot":
        return cls(
            project_id=ctx.project_id,
            entity_id=ctx.entity_id,
            step=ctx.step,
            task=ctx.task,
            user_id=ctx.user_id,
            profile=ctx.profile,
            meta=dict(ctx.meta),
        )


# ---------------------------------------------------------------------------
# Workfiles + pipeline backbone (Product -> Version -> Representation)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Workfile:
    id: str
    project_id: str
    context: ContextSnapshot
    path: str
    version: int
    dcc: DccName
    created_at: datetime = field(default_factory=utcnow)
    created_by: Optional[str] = None  # user_id
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Workfile.id must be non-empty")
        if not self.project_id:
            raise ValueError("Workfile.project_id must be non-empty")
        if not self.path:
            raise ValueError("Workfile.path must be non-empty")
        if self.version < 1:
            raise ValueError("Workfile.version must be >= 1")
        if not self.dcc:
            raise ValueError("Workfile.dcc must be non-empty")


@dataclass(frozen=True, slots=True)
class Product:
    """
    Logical deliverable stream for an entity (often scoped by step/task).
    Examples: "usd", "render", "abc_cache", "playblast"
    """
    id: str
    project_id: str
    entity_id: str
    name: str
    kind: str = "generic"
    data: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Product.id must be non-empty")
        if not self.project_id:
            raise ValueError("Product.project_id must be non-empty")
        if not self.entity_id:
            raise ValueError("Product.entity_id must be non-empty")
        if not self.name:
            raise ValueError("Product.name must be non-empty")


@dataclass(frozen=True, slots=True)
class Version:
    id: str
    project_id: str
    product_id: str
    number: int                      # v001 => 1
    status: str = "wip"
    context: Optional[ContextSnapshot] = None
    created_at: datetime = field(default_factory=utcnow)
    created_by: Optional[str] = None  # user_id
    comment: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Version.id must be non-empty")
        if not self.project_id:
            raise ValueError("Version.project_id must be non-empty")
        if not self.product_id:
            raise ValueError("Version.product_id must be non-empty")
        if self.number < 1:
            raise ValueError("Version.number must be >= 1")


@dataclass(frozen=True, slots=True)
class Representation:
    """
    Concrete file(s) representing a Version.
    Examples: name="exr", ext="exr", files=[...]
              name="mov", ext="mov", path="..."
              name="usd", ext="usd", path="..."
    """
    id: str
    project_id: str
    version_id: str
    name: str
    path: str
    ext: str
    files: List[str] = field(default_factory=list)  # optional for sequences
    size_bytes: Optional[int] = None
    hash: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Representation.id must be non-empty")
        if not self.project_id:
            raise ValueError("Representation.project_id must be non-empty")
        if not self.version_id:
            raise ValueError("Representation.version_id must be non-empty")
        if not self.name:
            raise ValueError("Representation.name must be non-empty")
        if not self.path:
            raise ValueError("Representation.path must be non-empty")
        if not self.ext:
            raise ValueError("Representation.ext must be non-empty")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("Representation.size_bytes must be >= 0")


# ---------------------------------------------------------------------------
# Transfer / ingest packaging (for Syncthing/watchfolder, vendor portal, etc.)
# ---------------------------------------------------------------------------

PackageKind = Literal["publish", "fetch", "submission"]
PackageItemRole = Literal["workfile", "representation", "source", "dependency", "other"]


@dataclass(frozen=True, slots=True)
class PackageItem:
    role: PackageItemRole
    path: str                 # path inside the package or absolute, depending on strategy
    size_bytes: Optional[int] = None
    hash: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("PackageItem.role must be non-empty")
        if not self.path:
            raise ValueError("PackageItem.path must be non-empty")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("PackageItem.size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """
    Manifest describing a transfer package.
    The transfer adapter decides how packages are physically stored/transferred.
    """
    id: str
    project_id: str
    kind: PackageKind
    context: Optional[ContextSnapshot] = None
    items: List[PackageItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)
    checksums: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("PackageManifest.id must be non-empty")
        if not self.project_id:
            raise ValueError("PackageManifest.project_id must be non-empty")
        if self.kind not in ("publish", "fetch", "submission"):
            raise ValueError(f"PackageManifest.kind invalid: {self.kind}")


# ---------------------------------------------------------------------------
# Review (optional early, useful later)
# ---------------------------------------------------------------------------

ReviewStatus = Literal["open", "in_review", "approved", "rejected", "closed"]


@dataclass(frozen=True, slots=True)
class Note:
    id: str
    author_id: Optional[str]
    text: str
    created_at: datetime = field(default_factory=utcnow)
    timecode: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Note.id must be non-empty")
        if not self.text:
            raise ValueError("Note.text must be non-empty")


@dataclass(frozen=True, slots=True)
class ReviewItem:
    id: str
    project_id: str
    entity_id: str
    version_id: Optional[str] = None
    title: str = ""
    status: ReviewStatus = "open"
    media_representation_ids: List[str] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)
    created_by: Optional[str] = None  # user_id
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ReviewItem.id must be non-empty")
        if not self.project_id:
            raise ValueError("ReviewItem.project_id must be non-empty")
        if not self.entity_id:
            raise ValueError("ReviewItem.entity_id must be non-empty")
        if self.status not in ("open", "in_review", "approved", "rejected", "closed"):
            raise ValueError(f"ReviewItem.status invalid: {self.status}")