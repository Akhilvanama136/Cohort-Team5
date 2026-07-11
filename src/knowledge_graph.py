import json
import os
import re
from typing import Dict, List, Tuple

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "cancer", "medpath_rag_dataset.json"
)

NODE_STYLES = {
    "disease": {"fill": "#ECFDF5", "stroke": "#059669", "text": "#065F46", "r": 45},
    "biomarker": {"fill": "#FFF7ED", "stroke": "#EA580C", "text": "#9A3412", "r": 32},
    "treatment": {"fill": "#EFF6FF", "stroke": "#2563EB", "text": "#1E40AF", "r": 32},
    "symptom": {"fill": "#FAF5FF", "stroke": "#7C3AED", "text": "#5B21B6", "r": 28},
}

EDGE_COLORS = {
    "has_biomarker": "#CBD5E1",
    "treated_by": "#0D9488",
    "presents_with": "#A855F7",
}


def _short_label(text: str, max_len: int = 22) -> str:
    label = re.split(r"[—\(\-\:]", text)[0].strip()
    if len(label) > max_len:
        label = label[: max_len - 1] + "…"
    return label


def _load_dataset() -> dict:
    if not os.path.exists(DATASET_PATH):
        return {"diseases": {}}
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def list_diseases() -> List[Dict[str, str]]:
    data = _load_dataset()
    items = []
    for category, diseases in data.get("diseases", {}).items():
        for key, info in diseases.items():
            name = info.get("basic_information", {}).get("disease_name", key.replace("_", " ").title())
            items.append({"key": key, "category": category, "name": name})
    return sorted(items, key=lambda x: (x["category"], x["name"]))


def build_disease_graph(disease_key: str) -> Tuple[List[dict], List[dict], str]:
    data = _load_dataset()
    disease_data = None
    category = "general"

    for cat, diseases in data.get("diseases", {}).items():
        if disease_key in diseases:
            disease_data = diseases[disease_key]
            category = cat
            break

    if not disease_data:
        return [], [], category

    disease_name = disease_data.get("basic_information", {}).get(
        "disease_name", disease_key.replace("_", " ").title()
    )

    nodes = [{"id": disease_name, "type": "disease", "label": disease_name}]
    edges = []

    biomarkers: List[str] = []
    biomarker_section = disease_data.get("biomarkers", {})
    for field in ("genetic_markers", "diagnostic_biomarkers", "prognostic_biomarkers"):
        for item in biomarker_section.get(field, [])[:2]:
            label = _short_label(item)
            if label and label not in biomarkers:
                biomarkers.append(label)
        if len(biomarkers) >= 3:
            break
    biomarkers = biomarkers[:3]

    treatments: List[str] = []
    treatment_section = disease_data.get("treatment", {})
    for field in ("targeted_therapy", "medications", "immunotherapy", "chemotherapy"):
        for item in treatment_section.get(field, [])[:2]:
            label = _short_label(item)
            if label and label not in treatments:
                treatments.append(label)
        if len(treatments) >= 3:
            break
    treatments = treatments[:3]

    symptoms: List[str] = []
    for item in disease_data.get("clinical_presentation", {}).get("common_symptoms", [])[:2]:
        label = _short_label(item, 20)
        if label and label not in symptoms:
            symptoms.append(label)

    for biomarker in biomarkers:
        nodes.append({"id": biomarker, "type": "biomarker", "label": biomarker})
        edges.append(
            {"source": disease_name, "target": biomarker, "relation": "has_biomarker",
             "description": f"{disease_name} is linked to biomarker {biomarker} in curated pathology data."}
        )

    for symptom in symptoms:
        nodes.append({"id": symptom, "type": "symptom", "label": symptom})
        edges.append(
            {"source": disease_name, "target": symptom, "relation": "presents_with",
             "description": f"Common clinical presentation of {disease_name}: {symptom.lower()}."}
        )

    anchor = biomarkers[0] if biomarkers else disease_name
    for treatment in treatments:
        nodes.append({"id": treatment, "type": "treatment", "label": treatment})
        edges.append(
            {"source": anchor, "target": treatment, "relation": "treated_by",
             "description": f"Evidence-based therapy connecting {anchor} to {treatment}."}
        )

    return nodes, edges, category


def render_graph_svg(nodes: List[dict], edges: List[dict], width: int = 620, height: int = 340) -> str:
    if not nodes:
        return "<p style='color:#64748B;'>No graph data available for this disease.</p>"

    by_type = {"disease": [], "biomarker": [], "treatment": [], "symptom": []}
    for node in nodes:
        by_type.setdefault(node["type"], []).append(node)

    positions: Dict[str, Tuple[int, int]] = {}
    positions[by_type["disease"][0]["id"]] = (110, height // 2)

    def _spread(items: List[dict], x: int, y_start: int = 50, y_end: int = None):
        if not items:
            return
        y_end = y_end or (height - 50)
        if len(items) == 1:
            positions[items[0]["id"]] = (x, (y_start + y_end) // 2)
            return
        step = (y_end - y_start) / (len(items) - 1)
        for i, item in enumerate(items):
            positions[item["id"]] = (x, int(y_start + i * step))

    mid_items = by_type.get("biomarker", []) + by_type.get("symptom", [])
    _spread(mid_items, 300)
    _spread(by_type.get("treatment", []), 500)

    lines = []
    for edge in edges:
        if edge["source"] not in positions or edge["target"] not in positions:
            continue
        x1, y1 = positions[edge["source"]]
        x2, y2 = positions[edge["target"]]
        color = EDGE_COLORS.get(edge["relation"], "#CBD5E1")
        dash = 'stroke-dasharray="4"' if edge["relation"] == "has_biomarker" else ""
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2" {dash}/>'
        )

    circles = []
    for node in nodes:
        if node["id"] not in positions:
            continue
        x, y = positions[node["id"]]
        style = NODE_STYLES.get(node["type"], NODE_STYLES["biomarker"])
        circles.append(f'<circle cx="{x}" cy="{y}" r="{style["r"]}" fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="2"/>')
        font_size = 11 if node["type"] == "disease" else 10
        circles.append(
            f'<text x="{x}" y="{y + 4}" font-family="Outfit, sans-serif" font-weight="700" '
            f'font-size="{font_size}" fill="{style["text"]}" text-anchor="middle">{node["label"]}</text>'
        )

    legend = """
    <div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap; margin-top:1rem; font-size:0.75rem; color:#64748B;">
        <span>🟢 Disease</span><span>🟠 Biomarker</span><span>🔵 Treatment</span><span>🟣 Symptom</span>
    </div>
    """

    return f"""
    <div style="background:white;border:1px solid #E2E8F0;padding:1.5rem;border-radius:16px;text-align:center;">
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="margin:0 auto;display:block;max-width:100%;">
            {''.join(lines)}
            {''.join(circles)}
        </svg>
        {legend}
        <div style="margin-top:0.5rem;color:#64748B;font-size:0.82rem;">
            Built from MedPath-RAG curated disease dataset (biomarkers, treatments, clinical links).
        </div>
    </div>
    """
