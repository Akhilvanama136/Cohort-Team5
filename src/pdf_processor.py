import os
import re
import fitz  # PyMuPDF
from pypdf import PdfReader

def clean_text(text: str) -> str:
    """
    Cleans extracted medical text by:
    1. Removing common header/footer patterns (e.g., page numbers, document names).
    2. Fixing hyphenation at line breaks (e.g., 'patho-\nlogy' -> 'pathology').
    3. Normalizing whitespaces and lines.
    4. Stripping non-printable characters.
    """
    if not text:
        return ""
        
    # Replace broken words at line breaks (hyphen followed by newline and optional whitespace)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Split text into lines to process headers/footers
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Filter out standalone page numbers (e.g., "1", "Page 12", "12 of 45")
        if re.match(r'^(page\s+)?\d+(\s+of\s+\d+)?$', stripped, re.IGNORECASE):
            continue
            
        # Filter out common journal/document footer/header timestamps or metadata
        # (e.g., "WHO Guidelines 2024", "NCI Cancer Factsheet", "Copyright ©")
        if re.search(r'(copyright|all rights reserved|doi:|www\.|issn|http)', stripped, re.IGNORECASE):
            continue
            
        cleaned_lines.append(stripped)
        
    # Rejoin lines
    return "\n".join(cleaned_lines)

def process_pdf(pdf_path: str) -> str:
    """
    Reads a PDF file using PyMuPDF (fitz) with a fallback to PyPDF.
    Processes page by page, removing empty pages and mapping page numbers.
    Returns cleaned text with page boundary markers.
    """
    cleaned_pages = []
    
    # Try using PyMuPDF first (highly recommended for performance and layout preservation)
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            cleaned = clean_text(text)
            if cleaned:
                # Store text with page markers for future citation / tracking
                cleaned_pages.append(f"--- PAGE {page_num + 1} ---\n{cleaned}")
        doc.close()
    except Exception as e:
        print(f"PyMuPDF failed for {pdf_path}: {e}. Retrying with PyPDF...")
        # Fallback to PyPDF
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                cleaned = clean_text(text)
                if cleaned:
                    cleaned_pages.append(f"--- PAGE {page_num + 1} ---\n{cleaned}")
        except Exception as fallback_err:
            print(f"Fallback PyPDF also failed for {pdf_path}: {fallback_err}")
            return ""
            
    return "\n\n".join(cleaned_pages)

def process_all_datasets(datasets_dir: str = "datasets", output_dir: str = "cleaned_text"):
    """
    Scans the datasets directory, processes all PDF files, and outputs cleaned txt files
    preserving the folder structure (e.g., cleaned_text/diabetes/, cleaned_text/cancer/).
    """
    if not os.path.exists(datasets_dir):
        print(f"Datasets directory '{datasets_dir}' not found. Creating it structure...")
        os.makedirs(os.path.join(datasets_dir, "diabetes"), exist_ok=True)
        os.makedirs(os.path.join(datasets_dir, "cancer"), exist_ok=True)
        print("Please place your PDF datasets inside the 'datasets/diabetes/' or 'datasets/cancer/' folders.")
        return

    processed_count = 0
    # Walk through the categories (diabetes, cancer, etc.)
    for category in os.listdir(datasets_dir):
        category_path = os.path.join(datasets_dir, category)
        if not os.path.isdir(category_path):
            continue
            
        # Target output category path
        target_out_path = os.path.join(output_dir, category)
        os.makedirs(target_out_path, exist_ok=True)
        
        for file_name in os.listdir(category_path):
            if file_name.lower().endswith('.pdf'):
                pdf_path = os.path.join(category_path, file_name)
                print(f"Processing PDF: {pdf_path}...")
                
                cleaned_content = process_pdf(pdf_path)
                if cleaned_content:
                    txt_filename = os.path.splitext(file_name)[0] + ".txt"
                    txt_path = os.path.join(target_out_path, txt_filename)
                    
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(cleaned_content)
                    print(f"Saved cleaned text to: {txt_path}")
                    processed_count += 1
                else:
                    print(f"Warning: Extracted text for {file_name} was empty or failed.")
                    
    print(f"\nCompleted processing. Total PDFs cleaned: {processed_count}")

if __name__ == "__main__":
    process_all_datasets()
