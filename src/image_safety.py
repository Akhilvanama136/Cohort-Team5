"""
Safety guardrails for multimodal medical image analysis.

Prevents dangerous false-negative language (e.g. "lungs clear") when
findings are uncertain or teaching annotations are present on the image.
"""
import base64
import re
from io import BytesIO
from typing import Dict, List

from PIL import Image

# Phrases that falsely reassure — dangerous when findings are uncertain
DANGEROUS_NORMAL_PHRASES = [
    "clear bilaterally",
    "lungs are clear",
    "lung fields are clear",
    "no acute findings",
    "no obvious abnormality",
    "no significant abnormality",
    "within normal limits",
    "unremarkable",
    "appears normal",
    "completely healthy",
    "no abnormalities detected",
]

VISION_SAFETY_RULES = """
CRITICAL SAFETY RULES (you MUST follow):
1. NEVER state organs are "clear", "normal", or "no acute findings" unless you are highly certain.
2. If uncertain, write: "Cannot exclude abnormality — formal radiologist review required."
3. FIRST inspect for arrows, circles, labels, or markers overlaid on the image (common in teaching cases).
4. If markers exist, they indicate the PRIMARY region of interest — describe that region first.
5. Use hedged language ("possible", "suggestive of", "cannot exclude") when confidence is not high.
"""


def detect_possible_annotations(image_b64: str) -> Dict:
    """
    Heuristic: teaching images often contain sharp black arrow/marker pixels.
    Returns whether manual annotations are likely present.
    """
    try:
        raw = base64.b64decode(image_b64)
        img = Image.open(BytesIO(raw)).convert("L")
        pixels = list(img.getdata())
        if not pixels:
            return {"annotations_likely": False, "dark_pixel_ratio": 0.0}

        dark_count = sum(1 for p in pixels if p < 30)
        dark_ratio = dark_count / len(pixels)
        # Arrow overlays are sparse but distinct on X-rays
        annotations_likely = 0.0008 < dark_ratio < 0.06
        return {
            "annotations_likely": annotations_likely,
            "dark_pixel_ratio": round(dark_ratio, 5),
        }
    except Exception:
        return {"annotations_likely": False, "dark_pixel_ratio": 0.0}


def _vision_field(vision_summary: str, field: str) -> str:
    pattern = rf"{field}:\s*(.+?)(?:\n|$)"
    match = re.search(pattern, vision_summary, re.IGNORECASE)
    return match.group(1).strip().lower() if match else ""


def validate_imaging_safety(
    vision_summary: str,
    care_report: str,
    annotation_hint: Dict,
) -> Dict:
    """Cross-check vision screening vs care report for dangerous contradictions."""
    flags: List[str] = []
    vision_lower = vision_summary.lower()
    report_lower = care_report.lower()

    if annotation_hint.get("annotations_likely"):
        flags.append(
            "Possible arrows/markers detected on image — AI must describe the marked region; "
            "do not report as normal."
        )

    if "annotations_present: yes" in vision_lower:
        flags.append("Vision model reported annotations on the image.")

    annotations_target = _vision_field(vision_summary, "ANNOTATION_TARGETS")
    if annotations_target and annotations_target not in ("none", "n/a", ""):
        if annotations_target not in report_lower and "annotation" not in report_lower:
            flags.append(
                f"Care report may not address annotated region: {annotations_target}"
            )

    abnormality = _vision_field(vision_summary, "ABNORMALITY_PRESENT")
    confidence = _vision_field(vision_summary, "CONFIDENCE")
    uncertain_findings = abnormality in ("yes", "uncertain", "") or confidence in ("low", "medium", "")

    for phrase in DANGEROUS_NORMAL_PHRASES:
        if phrase in report_lower and uncertain_findings:
            flags.append(
                f"SAFETY VIOLATION: Report states '{phrase}' but imaging confidence is not high."
            )

    if confidence == "low" and any(p in report_lower for p in ("clear", "normal", "unremarkable")):
        flags.append("Contradiction: low-confidence vision but reassuring language in report.")

    requires_review = (
        bool(flags)
        or confidence in ("low", "medium", "")
        or abnormality in ("yes", "uncertain", "")
        or annotation_hint.get("annotations_likely")
        or "annotations_present: yes" in vision_lower
    )

    imaging_confidence = confidence if confidence in ("low", "medium", "high") else "low"

    return {
        "flags": flags,
        "requires_radiologist_review": requires_review,
        "imaging_confidence": imaging_confidence,
    }


def build_safety_preamble(flags: List[str], vision_summary: str) -> str:
    """Mandatory human-in-the-loop header when imaging safety checks fail."""
    lines = [
        "## ⛔ SAFETY ALERT — DO NOT USE FOR CLINICAL DECISIONS\n",
        "This AI image read **may be wrong**. A licensed radiologist/pathologist must review the scan.\n",
        "**Never** rely on AI text that says 'clear' or 'normal' when the image shows marked regions.\n\n",
    ]
    if flags:
        lines.append("**Safety flags:**\n")
        for flag in flags:
            lines.append(f"- {flag}\n")
        lines.append("\n")

    lines.append("### AI Vision Screening (verify against the image yourself)\n")
    lines.append("```\n")
    lines.append(vision_summary.strip())
    lines.append("\n```\n\n---\n\n")
    return "".join(lines)


def imaging_confidence_percent(confidence: str, has_sources: bool) -> int:
    """Image analysis confidence is always capped low — never show false high confidence."""
    base = {"low": 15, "medium": 35, "high": 55}.get(confidence, 15)
    if has_sources:
        base = min(base + 10, 45)
    return base
