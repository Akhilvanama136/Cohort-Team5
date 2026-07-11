import os
import json
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Helpers for PDF-derived cleaned text
# ---------------------------------------------------------------------------

def load_and_parse_cleaned_file(file_path: str):
    """
    Reads a cleaned text file and parses it page by page.
    Yields tuple of (page_num, page_text).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r'---\s*PAGE\s+(\d+)\s*---'
    parts = re.split(pattern, content)

    if len(parts) < 3:
        yield (1, content.strip())
        return

    for i in range(1, len(parts), 2):
        try:
            page_num = int(parts[i])
        except ValueError:
            page_num = (i // 2) + 1
        page_text = parts[i + 1].strip()
        if page_text:
            yield (page_num, page_text)


# ---------------------------------------------------------------------------
# Helpers for structured JSON datasets (medpath_rag_dataset.json)
# ---------------------------------------------------------------------------

def _flatten_value(value, depth=0) -> str:
    """Recursively convert any nested JSON value into readable prose."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        lines = []
        for item in value:
            lines.append(_flatten_value(item, depth + 1))
        return "\n".join(f"• {l}" if depth == 0 else l for l in lines)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            label = k.replace("_", " ").title()
            body = _flatten_value(v, depth + 1)
            parts.append(f"{label}: {body}")
        return "\n".join(parts)
    return str(value)


def _build_section_text(section_name: str, section_data, disease_name: str) -> str:
    """Build a readable paragraph from a single section of a disease entry."""
    header = f"{disease_name} — {section_name.replace('_', ' ').title()}"
    body = _flatten_value(section_data)
    return f"{header}\n\n{body}"


def extract_json_dataset_texts(json_path: str):
    """
    Walk a medpath_rag_dataset.json file and yield
    (disease_name, category, section_name, text) tuples.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    diseases = data.get("diseases", {})
    for category, category_diseases in diseases.items():
        for disease_key, disease_data in category_diseases.items():
            # Human-readable disease name
            name_info = disease_data.get("basic_information", {})
            disease_name = name_info.get("disease_name", disease_key.replace("_", " ").title())

            for section_name, section_data in disease_data.items():
                text = _build_section_text(section_name, section_data, disease_name)
                if text.strip():
                    yield (disease_name, category, section_name, text)


# ---------------------------------------------------------------------------
# Main chunking pipeline
# ---------------------------------------------------------------------------

def generate_chunks(
    cleaned_dir: str = "cleaned_text",
    datasets_dir: str = "datasets",
    output_file: str = "chunks.json",
):
    """
    Reads both:
      1. PDF-derived cleaned text files from cleaned_text/
      2. Structured JSON datasets from datasets/
    Chunks everything to 300-500 words with 100 word overlap and
    saves the result to chunks.json.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=lambda x: len(x.split()),
        separators=["\n\n", "\n", " ", ""],
    )

    all_chunks = []
    chunk_counter = 0

    print("Starting chunk generation...\n")

    # ---- 1. Process PDF-derived cleaned text files ----
    if os.path.exists(cleaned_dir):
        for category in os.listdir(cleaned_dir):
            category_path = os.path.join(cleaned_dir, category)
            if not os.path.isdir(category_path):
                continue
            for file_name in os.listdir(category_path):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(category_path, file_name)
                    original_pdf_name = os.path.splitext(file_name)[0] + ".pdf"
                    print(f"[PDF] Chunking: {file_path}")

                    for page_num, page_text in load_and_parse_cleaned_file(file_path):
                        chunks = text_splitter.split_text(page_text)
                        for chunk_text in chunks:
                            if len(chunk_text.split()) < 15:
                                continue
                            all_chunks.append({
                                "id": f"chunk_{chunk_counter}",
                                "text": chunk_text,
                                "metadata": {
                                    "source": original_pdf_name,
                                    "category": category,
                                    "page": page_num,
                                },
                            })
                            chunk_counter += 1
    else:
        print(f"  [INFO] No cleaned_text directory found — skipping PDF chunks.")

    # ---- 2. Process structured JSON datasets ----
    if os.path.exists(datasets_dir):
        for root, dirs, files in os.walk(datasets_dir):
            for file_name in files:
                if file_name.endswith(".json"):
                    json_path = os.path.join(root, file_name)
                    print(f"[JSON] Chunking: {json_path}")

                    for disease_name, category, section, text in extract_json_dataset_texts(json_path):
                        chunks = text_splitter.split_text(text)
                        for chunk_text in chunks:
                            if len(chunk_text.split()) < 15:
                                continue
                            all_chunks.append({
                                "id": f"chunk_{chunk_counter}",
                                "text": chunk_text,
                                "metadata": {
                                    "source": file_name,
                                    "category": category,
                                    "disease": disease_name,
                                    "section": section,
                                },
                            })
                            chunk_counter += 1
    else:
        print(f"  [INFO] No datasets directory found — skipping JSON chunks.")

    # Save to chunks.json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nChunking completed. Generated {len(all_chunks)} chunks saved to {output_file}.")

if __name__ == "__main__":
    generate_chunks()

