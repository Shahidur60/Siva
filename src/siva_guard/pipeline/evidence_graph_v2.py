# # src/siva_guard/pipeline/evidence_graph_v2.py
# from __future__ import annotations

# from dataclasses import dataclass
# from typing import Any, Dict, List, Optional

# import networkx as nx

# from siva_guard.pipeline.identifiers import parse_claimed
# from siva_guard.pipeline.similarity import confusability
# from siva_guard.pipeline.linkout import extract_linkouts
# from siva_guard.pipeline.avatar_hash import hash_avatar_url
# from siva_guard.pipeline.reverse_links import fetch_outbound_links


# def _safe_str(s: Optional[str]) -> str:
#     return (s or "").strip()


# @dataclass
# class GraphV2Result:
#     graph: nx.Graph
#     nodes_out: List[Dict[str, Any]]
#     edges_out: List[Dict[str, Any]]
#     metrics: Dict[str, Any]


# def build_evidence_graph_v2(per_identity: Dict[str, Any]) -> GraphV2Result:
#     """
#     Phase 6 evidence graph builder (v2):
#     - Platform-aware handle parsing (uses parse_claimed(claimed, platform=...))
#     - Crosslink scoring (bio links + @handles + reverse website links)
#     - Avatar hashing (exact sha256 match only; deterministic)

#     per_identity expects entries like:
#       {
#         "<claimed_key>": {
#           "platform": "...",
#           "claimed": "...",
#           "has_public": bool,
#           "ui": {...},
#           "public": {...},   # or "public_evidence"
#           "errors": [...]
#         }
#       }
#     """
#     G = nx.Graph()

#     node_ids: List[str] = []
#     node_features: Dict[str, Dict[str, Any]] = {}

#     # ---- Nodes ----
#     for node_id, item in per_identity.items():
#         platform = item.get("platform")
#         claimed = item.get("claimed") or (item.get("claim", {}) or {}).get("claimed") or node_id
#         has_public = bool(item.get("has_public", False))

#         # Prefer public evidence when present; otherwise fall back to UI
#         pub = item.get("public") or item.get("public_evidence") or {}
#         ui = item.get("ui") or {}

#         display_name = _safe_str(pub.get("display_name")) or _safe_str(ui.get("display_name"))
#         bio = _safe_str(pub.get("bio")) or _safe_str(ui.get("snippet"))
#         avatar_url = _safe_str(pub.get("avatar_url")) or _safe_str(ui.get("avatar_url"))

#         # Phase 6: platform-aware parsing
#         parsed = parse_claimed(claimed, platform=platform)

#         # Bio linkouts (urls/domains/@handles)
#         linkouts = extract_linkouts(bio) if bio else extract_linkouts(None)

#         # Avatar hash (exact sha256 match only)
#         avatar_hash = hash_avatar_url(avatar_url) if avatar_url else None

#         # Phase 6: reverse website links (best-effort)
#         reverse_domains: List[str] = []
#         reverse_error: Optional[str] = None
#         reverse_cached: Optional[bool] = None
#         reverse_url: Optional[str] = None

#         if linkouts.urls:
#             reverse_url = linkouts.urls[0]  # first URL as website candidate
#             rr = fetch_outbound_links(reverse_url)
#             reverse_domains = rr.outbound_domains
#             reverse_error = rr.error
#             reverse_cached = rr.fetch_cached

#         feats = {
#             "platform": platform,
#             "claimed": claimed,
#             "has_public": has_public,
#             "display_name": display_name or None,
#             "bio": bio or None,
#             "avatar_url": avatar_url or None,

#             "parsed_kind": parsed.kind,
#             "parsed_domain": parsed.domain,
#             "parsed_handle": parsed.handle,
#             "norm": parsed.normalized,

#             "bio_link_domains": linkouts.domains,
#             "bio_link_handles": linkouts.handles,

#             "reverse_link_url": reverse_url,
#             "reverse_link_domains": reverse_domains,
#             "reverse_link_error": reverse_error,
#             "reverse_fetch_cached": reverse_cached,

#             "avatar_sha256": (avatar_hash.sha256 if avatar_hash else None),
#             "avatar_hash_error": (
#                 avatar_hash.error if avatar_hash else ("avatar_url_missing" if not avatar_url else None)
#             ),
#         }

#         G.add_node(node_id, **feats)
#         node_ids.append(node_id)
#         node_features[node_id] = feats

#     # ---- Edges (pairwise) ----
#     edges_out: List[Dict[str, Any]] = []
#     confusable_pairs = 0
#     name_mismatch_pairs = 0
#     avatar_mismatch_pairs = 0
#     crosslink_hits = 0

#     for i in range(len(node_ids)):
#         for j in range(i + 1, len(node_ids)):
#             a = node_ids[i]
#             b = node_ids[j]
#             A = node_features[a]
#             B = node_features[b]

#             # Handle similarity (preferred)
#             handle_a = A.get("parsed_handle") or ""
#             handle_b = B.get("parsed_handle") or ""
#             ha = handle_a if handle_a else (A.get("norm") or "")
#             hb = handle_b if handle_b else (B.get("norm") or "")

#             handle_sim = confusability(ha, hb)["ratio"]

#             # Display name similarity
#             dn_a = A.get("display_name") or ""
#             dn_b = B.get("display_name") or ""
#             name_sim = confusability(dn_a, dn_b)["ratio"] if (dn_a and dn_b) else None

#             # Avatar match (exact hash match only)
#             av_a = A.get("avatar_sha256")
#             av_b = B.get("avatar_sha256")
#             avatar_match = (av_a is not None and av_b is not None and av_a == av_b)

#             # ---- Phase 6: crosslink scoring (0..1) ----
#             score = 0.0

#             da = set(A.get("bio_link_domains") or [])
#             db = set(B.get("bio_link_domains") or [])
#             dom_a = A.get("parsed_domain")
#             dom_b = B.get("parsed_domain")

#             # direct bio-to-other domain (strong)
#             if dom_a and dom_a in db:
#                 score += 0.5
#             if dom_b and dom_b in da:
#                 score += 0.5

#             # direct bio @handle mention (weaker)
#             ha_set = set(A.get("bio_link_handles") or [])
#             hb_set = set(B.get("bio_link_handles") or [])
#             ha_l = handle_a.lower() if handle_a else ""
#             hb_l = handle_b.lower() if handle_b else ""

#             if ha_l and ha_l in hb_set:
#                 score += 0.25
#             if hb_l and hb_l in ha_set:
#                 score += 0.25

#             # reverse website links: website links out to the other identity's domain (strong)
#             ra = set(A.get("reverse_link_domains") or [])
#             rb = set(B.get("reverse_link_domains") or [])
#             if dom_b and dom_b in ra:
#                 score += 0.5
#             if dom_a and dom_a in rb:
#                 score += 0.5

#             if score > 1.0:
#                 score = 1.0

#             crosslink = score >= 0.5
#             if crosslink:
#                 crosslink_hits += 1

#             # thresholds (deterministic constants)
#             confusable = handle_sim >= 0.92
#             if confusable:
#                 confusable_pairs += 1

#             if name_sim is not None and name_sim < 0.60 and confusable:
#                 # Confusable handles but names differ a lot → suspicious
#                 name_mismatch_pairs += 1

#             if (av_a is not None and av_b is not None) and (not avatar_match) and confusable:
#                 avatar_mismatch_pairs += 1

#             G.add_edge(
#                 a,
#                 b,
#                 handle_similarity=handle_sim,
#                 name_similarity=name_sim,
#                 avatar_match=(avatar_match if (av_a is not None and av_b is not None) else None),
#                 crosslink=crosslink,
#                 crosslink_score=score,
#             )

#             edges_out.append(
#                 {
#                     "src": a,
#                     "dst": b,
#                     "handle_similarity": handle_sim,
#                     "name_similarity": name_sim,
#                     "avatar_match": (avatar_match if (av_a is not None and av_b is not None) else None),
#                     "crosslink": crosslink,
#                     "crosslink_score": score,
#                 }
#             )

#     # ---- Metrics ----
#     total = len(node_ids) if node_ids else 1
#     public_coverage = sum(1 for n in node_ids if node_features[n].get("has_public")) / float(total)

#     metrics = {
#         "num_identities": len(node_ids),
#         "public_coverage": public_coverage,
#         "confusable_pairs": confusable_pairs,
#         "name_mismatch_pairs": name_mismatch_pairs,
#         "avatar_mismatch_pairs": avatar_mismatch_pairs,
#         "crosslink_hits": crosslink_hits,
#     }

#     # output nodes
#     nodes_out: List[Dict[str, Any]] = []
#     for nid in node_ids:
#         d = node_features[nid].copy()
#         d["id"] = nid
#         nodes_out.append(d)

#     return GraphV2Result(graph=G, nodes_out=nodes_out, edges_out=edges_out, metrics=metrics)
# src/siva_guard/pipeline/evidence_graph_v2.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import networkx as nx

from siva_guard.pipeline.identifiers import parse_claimed
from siva_guard.pipeline.similarity import confusability
from siva_guard.pipeline.linkout import extract_linkouts
from siva_guard.pipeline.avatar_hash import hash_avatar_url
from siva_guard.pipeline.reverse_links import fetch_outbound_links
from siva_guard.pipeline.name_clean import clean_display_name


def _safe_str(s: Optional[str]) -> str:
    return (s or "").strip()


def _domains_from_urls(urls: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for u in urls or []:
        try:
            host = (urlparse(u).netloc or "").lower().strip()
            if host and host not in seen:
                seen.add(host)
                out.append(host)
        except Exception:
            continue
    return out


@dataclass
class GraphV2Result:
    graph: nx.Graph
    nodes_out: List[Dict[str, Any]]
    edges_out: List[Dict[str, Any]]
    metrics: Dict[str, Any]


def build_evidence_graph_v2(per_identity: Dict[str, Any]) -> GraphV2Result:
    """
    Phase 6 evidence graph builder (v2), updated for Phase 7:
    - Adds display_name_clean (platform-aware cleaning)
    - Uses display_name_clean in name similarity
    - Incorporates PublicEvidence.external_links domains into crosslink scoring
    """
    G = nx.Graph()

    node_ids: List[str] = []
    node_features: Dict[str, Dict[str, Any]] = {}

    # ---- Nodes ----
    for node_id, item in per_identity.items():
        platform = item.get("platform")
        claimed = item.get("claimed") or (item.get("claim", {}) or {}).get("claimed") or node_id
        has_public = bool(item.get("has_public", False))

        # Prefer public evidence when present; otherwise fall back to UI
        pub = item.get("public") or item.get("public_evidence") or {}
        ui = item.get("ui") or {}

        display_name = _safe_str(pub.get("display_name")) or _safe_str(ui.get("display_name"))
        bio = _safe_str(pub.get("bio")) or _safe_str(ui.get("snippet"))
        avatar_url = _safe_str(pub.get("avatar_url")) or _safe_str(ui.get("avatar_url"))

        # Phase 7.2: external_links from public evidence (if schema/tool supports it)
        external_links = pub.get("external_links") or []
        if not isinstance(external_links, list):
            external_links = []
        external_link_domains = _domains_from_urls([str(u) for u in external_links if u])

        # Phase 7.3: cleaned display name for comparisons
        display_name_clean = clean_display_name(display_name, platform=str(platform or ""))

        # Phase 6: platform-aware parsing
        parsed = parse_claimed(claimed, platform=platform)

        # Bio linkouts (urls/domains/@handles)
        linkouts = extract_linkouts(bio) if bio else extract_linkouts(None)

        # Avatar hash (exact sha256 match only)
        avatar_hash = hash_avatar_url(avatar_url) if avatar_url else None

        # Phase 6: reverse website links (best-effort)
        reverse_domains: List[str] = []
        reverse_error: Optional[str] = None
        reverse_cached: Optional[bool] = None
        reverse_url: Optional[str] = None

        if linkouts.urls:
            reverse_url = linkouts.urls[0]  # first URL as website candidate
            rr = fetch_outbound_links(reverse_url)
            reverse_domains = rr.outbound_domains
            reverse_error = rr.error
            reverse_cached = rr.fetch_cached

        feats = {
            "platform": platform,
            "claimed": claimed,
            "has_public": has_public,

            "display_name": display_name or None,
            "display_name_clean": display_name_clean or None,
            "bio": bio or None,
            "avatar_url": avatar_url or None,

            "parsed_kind": parsed.kind,
            "parsed_domain": parsed.domain,
            "parsed_handle": parsed.handle,
            "norm": parsed.normalized,

            "bio_link_domains": linkouts.domains,
            "bio_link_handles": linkouts.handles,

            # Phase 7.2 inputs
            "external_links": external_links,
            "external_link_domains": external_link_domains,

            "reverse_link_url": reverse_url,
            "reverse_link_domains": reverse_domains,
            "reverse_link_error": reverse_error,
            "reverse_fetch_cached": reverse_cached,

            "avatar_sha256": (avatar_hash.sha256 if avatar_hash else None),
            "avatar_hash_error": (
                avatar_hash.error if avatar_hash else ("avatar_url_missing" if not avatar_url else None)
            ),
        }

        G.add_node(node_id, **feats)
        node_ids.append(node_id)
        node_features[node_id] = feats

    # ---- Edges (pairwise) ----
    edges_out: List[Dict[str, Any]] = []
    confusable_pairs = 0
    name_mismatch_pairs = 0
    avatar_mismatch_pairs = 0
    crosslink_hits = 0

    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            a = node_ids[i]
            b = node_ids[j]
            A = node_features[a]
            B = node_features[b]

            # Handle similarity (preferred)
            handle_a = A.get("parsed_handle") or ""
            handle_b = B.get("parsed_handle") or ""
            ha = handle_a if handle_a else (A.get("norm") or "")
            hb = handle_b if handle_b else (B.get("norm") or "")

            handle_sim = confusability(ha, hb)["ratio"]

            # Display name similarity (use cleaned names first)
            dn_a = A.get("display_name_clean") or A.get("display_name") or ""
            dn_b = B.get("display_name_clean") or B.get("display_name") or ""
            name_sim = confusability(dn_a, dn_b)["ratio"] if (dn_a and dn_b) else None

            # Avatar match (exact hash match only)
            av_a = A.get("avatar_sha256")
            av_b = B.get("avatar_sha256")
            avatar_match = (av_a is not None and av_b is not None and av_a == av_b)

            # ---- Crosslink scoring (0..1) ----
            score = 0.0

            da = set(A.get("bio_link_domains") or [])
            db = set(B.get("bio_link_domains") or [])
            ea = set(A.get("external_link_domains") or [])
            eb = set(B.get("external_link_domains") or [])

            dom_a = A.get("parsed_domain")
            dom_b = B.get("parsed_domain")

            # direct bio-to-other domain (strong)
            if dom_a and dom_a in db:
                score += 0.5
            if dom_b and dom_b in da:
                score += 0.5

            # external-links-to-other domain (medium)
            if dom_a and dom_a in eb:
                score += 0.35
            if dom_b and dom_b in ea:
                score += 0.35

            # direct bio @handle mention (weaker)
            ha_set = set(A.get("bio_link_handles") or [])
            hb_set = set(B.get("bio_link_handles") or [])
            ha_l = handle_a.lower() if handle_a else ""
            hb_l = handle_b.lower() if handle_b else ""

            if ha_l and ha_l in hb_set:
                score += 0.25
            if hb_l and hb_l in ha_set:
                score += 0.25

            # reverse website links: website links out to the other identity's domain (strong)
            ra = set(A.get("reverse_link_domains") or [])
            rb = set(B.get("reverse_link_domains") or [])
            if dom_b and dom_b in ra:
                score += 0.5
            if dom_a and dom_a in rb:
                score += 0.5

            if score > 1.0:
                score = 1.0

            crosslink = score >= 0.5
            if crosslink:
                crosslink_hits += 1

            # thresholds (deterministic constants)
            confusable = handle_sim >= 0.92
            if confusable:
                confusable_pairs += 1

            if name_sim is not None and name_sim < 0.60 and confusable:
                name_mismatch_pairs += 1

            if (av_a is not None and av_b is not None) and (not avatar_match) and confusable:
                avatar_mismatch_pairs += 1

            G.add_edge(
                a,
                b,
                handle_similarity=handle_sim,
                name_similarity=name_sim,
                avatar_match=(avatar_match if (av_a is not None and av_b is not None) else None),
                crosslink=crosslink,
                crosslink_score=score,
            )

            edges_out.append(
                {
                    "src": a,
                    "dst": b,
                    "handle_similarity": handle_sim,
                    "name_similarity": name_sim,
                    "avatar_match": (avatar_match if (av_a is not None and av_b is not None) else None),
                    "crosslink": crosslink,
                    "crosslink_score": score,
                }
            )

    # ---- Metrics ----
    total = len(node_ids) if node_ids else 1
    public_coverage = sum(1 for n in node_ids if node_features[n].get("has_public")) / float(total)

    metrics = {
        "num_identities": len(node_ids),
        "public_coverage": public_coverage,
        "confusable_pairs": confusable_pairs,
        "name_mismatch_pairs": name_mismatch_pairs,
        "avatar_mismatch_pairs": avatar_mismatch_pairs,
        "crosslink_hits": crosslink_hits,
    }

    # output nodes
    nodes_out: List[Dict[str, Any]] = []
    for nid in node_ids:
        d = node_features[nid].copy()
        d["id"] = nid
        nodes_out.append(d)

    return GraphV2Result(graph=G, nodes_out=nodes_out, edges_out=edges_out, metrics=metrics)
