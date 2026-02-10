# from __future__ import annotations

# from enum import Enum
# from typing import Any, Dict, Optional, List
# from pydantic import BaseModel, Field


# class Platform(str, Enum):
#     FACEBOOK = "facebook"
#     INSTAGRAM = "instagram"
#     X = "x"
#     LINKEDIN = "linkedin"
#     GITHUB = "github"
#     TIKTOK = "tiktok"
#     YOUTUBE = "youtube"
#     SNAPCHAT = "snapchat"
#     DISCORD = "discord"
#     TELEGRAM = "telegram"
#     EMAIL = "email"
#     WEBSITE = "website"
#     OTHER = "other"


# class UiCard(BaseModel):
#     display_name: Optional[str] = None
#     handle_or_id: Optional[str] = None
#     avatar_url: Optional[str] = None
#     snippet: Optional[str] = None
#     platform_label: Optional[str] = None


# class PublicEvidence(BaseModel):
#     canonical_url: Optional[str] = None
#     username: Optional[str] = None
#     display_name: Optional[str] = None
#     bio: Optional[str] = None
#     avatar_url: Optional[str] = None

#     created_at: Optional[str] = None
#     follower_count: Optional[int] = None
#     following_count: Optional[int] = None
#     post_count: Optional[int] = None
#     verified: Optional[bool] = None

#     external_links: List[str] = Field(default_factory=list)
#     raw_excerpt: Optional[str] = None
#     field_confidence: Dict[str, float] = Field(default_factory=dict)


# class CollectionMode(str, Enum):
#     IN_APP_ONLY = "in_app_only"
#     PUBLIC_WEB = "public_web"
#     OAUTH_USER_CONSENT = "oauth_user_consent"
#     MANUAL_PROOF = "manual_proof"


# class IdentityClaim(BaseModel):
#     platform: Platform
#     claimed: str
#     ui: UiCard


# class IdentityEvidence(BaseModel):
#     claim: IdentityClaim
#     mode: CollectionMode = CollectionMode.IN_APP_ONLY
#     public: Optional[PublicEvidence] = None
#     errors: List[str] = Field(default_factory=list)


# class RiskReason(BaseModel):
#     code: str
#     message: str
#     severity: str = "medium"


# class RiskResult(BaseModel):
#     substitution_risk: float = Field(ge=0.0, le=1.0)
#     confidence: float = Field(ge=0.0, le=1.0)
#     reasons: List[RiskReason] = Field(default_factory=list)
#     per_identity: Dict[str, Any] = Field(default_factory=dict)


from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    X = "x"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    SNAPCHAT = "snapchat"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBSITE = "website"
    OTHER = "other"


class UiCard(BaseModel):
    display_name: Optional[str] = None
    handle_or_id: Optional[str] = None
    avatar_url: Optional[str] = None
    snippet: Optional[str] = None
    platform_label: Optional[str] = None


class PublicEvidence(BaseModel):
    canonical_url: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    created_at: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    verified: Optional[bool] = None

    # ✅ Phase 6.3: expose cache information cleanly
    # social_url.py already attempts to set this field.
    fetch_cached: Optional[bool] = None

    external_links: List[str] = Field(default_factory=list)
    raw_excerpt: Optional[str] = None
    field_confidence: Dict[str, float] = Field(default_factory=dict)


class CollectionMode(str, Enum):
    IN_APP_ONLY = "in_app_only"
    PUBLIC_WEB = "public_web"
    OAUTH_USER_CONSENT = "oauth_user_consent"
    MANUAL_PROOF = "manual_proof"


class IdentityClaim(BaseModel):
    platform: Platform
    claimed: str
    ui: UiCard


class IdentityEvidence(BaseModel):
    claim: IdentityClaim
    mode: CollectionMode = CollectionMode.IN_APP_ONLY
    public: Optional[PublicEvidence] = None
    errors: List[str] = Field(default_factory=list)


class RiskReason(BaseModel):
    code: str
    message: str
    severity: str = "medium"


class RiskResult(BaseModel):
    substitution_risk: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[RiskReason] = Field(default_factory=list)
    per_identity: Dict[str, Any] = Field(default_factory=dict)
