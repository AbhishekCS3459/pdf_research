import logging
from pathlib import Path
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import re

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def prepare_pipeline_options() -> PdfPipelineOptions:
    options = PdfPipelineOptions()
    options.do_ocr = True
    options.do_table_structure = True
    options.table_structure_options.do_cell_matching = True
    return options

def normalize_text(text):
    # Lowercase, remove excessive whitespace, normalize line breaks
    return re.sub(r'\s+', ' ', text).strip().lower()

def match_chunks_to_pdf(chunks, pdf_file_path):
    """
    Matches the provided chunks to the PDF content and extracts metadata.
    Handles multi-page, multi-section, and multi-bbox chunks.
    """
    pdf_path = Path(pdf_file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file_path}")

    configure_logging()
    logging.info("Starting PDF processing...")

    pipeline_options = prepare_pipeline_options()

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    try:
        conv_result = doc_converter.convert(pdf_path)
    except Exception as e:
        logging.exception(f"Error during document conversion: {e}")
        return []

    document = conv_result.document

    # Step 1: Build a flat text and mapping from each character to its source
    flat_text = ""
    char_map = []  # Each entry: (text_element_idx, char_idx_in_element)
    element_meta = []  # For quick lookup: (page_no, bbox, section_header)

    # Track the current section header for each text element
    current_section = None
    for idx, text_element in enumerate(document.texts):
        # Find the nearest previous section header
        if getattr(text_element, "label", None) == "section_header":
            current_section = text_element.text
        element_meta.append({
            "page_no": text_element.prov[0].page_no,
            "bbox": text_element.prov[0].bbox,
            "section_header": current_section,
            "text_element_idx": idx,
        })
        for char_idx, char in enumerate(text_element.text):
            flat_text += char
            char_map.append({
                "text_element_idx": idx,
                "char_idx_in_element": char_idx,
            })
        # Add a space between elements for normalization
        flat_text += " "
        char_map.append({
            "text_element_idx": idx,
            "char_idx_in_element": len(text_element.text),  # virtual space
        })

    norm_flat_text = normalize_text(flat_text)

    results = []
    for chunk in chunks:
        norm_chunk = normalize_text(chunk)
        match = re.search(re.escape(norm_chunk), norm_flat_text)
        if not match:
            # Try a fuzzy match (allowing for minor whitespace differences)
            # For simplicity, skip fuzzy here, but can use difflib or rapidfuzz for production
            continue

        start, end = match.start(), match.end()
        # Map back to char_map to get all involved text elements
        involved_elements = set()
        involved_pages = set()
        involved_bboxes = []
        involved_sections = set()
        matched_text = flat_text[start:end]

        for i in range(start, end):
            mapping = char_map[i]
            idx = mapping["text_element_idx"]
            meta = element_meta[idx]
            involved_elements.add(idx)
            involved_pages.add(meta["page_no"])
            involved_bboxes.append(meta["bbox"])
            if meta["section_header"]:
                involved_sections.add(meta["section_header"])

        # Merge consecutive bboxes on the same page for clarity
        bbox_info = []
        for idx in sorted(involved_elements):
            meta = element_meta[idx]
            bbox = meta["bbox"]
            bbox_info.append({
                "page_no": meta["page_no"],
                "bbox": {
                    "l": bbox.l,
                    "t": bbox.t,
                    "r": bbox.r,
                    "b": bbox.b
                }
            })

        results.append({
            "matched_text": matched_text.strip(),
            "pages": sorted(list(involved_pages)),
            "bounding_boxes": bbox_info,
            "section_headers": list(involved_sections)
        })

    return results

if __name__ == "__main__":
    # Example usage
        # Example chunk for match_chunks_to_pdf.py
    # example_chunks = [
    #     (
    #         "We set the maximum output length during "
    #         "inference to input length + 50, but terminate early when possible",
    #         "We set the maximum output length during inference to input length + 50, but terminate early when possible"
    #     )
    # ]
    example_chunks = [
        (
            "To evaluate the importance of different components of the Transformer, we varied our base model "
            "in different ways, measuring the change in performance on English-to-German translation on the "
            "development set, newstest2013. We used beam search as described in the previous section, but no "
            "checkpoint averaging. We present these results in Table 3. "
            "In Table 3 rows (A), we vary the number of attention heads and the attention key and value dimensions, "
            "keeping the amount of computation constant, as described in Section 3.2.2. While single-head "
            "attention is 0.9 BLEU worse than the best setting, quality also drops off with too many heads"
        )
    ]
    
#     example_chunks = [
#     (
#         "To evaluate the importance of different components of the Transformer, we varied our base model "
#         "in different ways, measuring the change in performance on English-to-German translation on the "
#         "development set, newstest2013. We used beam search as described in the previous section, but no "
#         "checkpoint averaging. We present these results in Table 3. "
#         "In Table 3 rows (A), we vary the number of attention heads and the attention key and value dimensions, "
#         "keeping the amount of computation constant, as described in Section 3.2.2. While single-head "
#         "attention is 0.9 BLEU worse than the best setting, quality also drops off with too many heads"
#     )
# ]
    # example_chunks = [
    #     (
    #         "To evaluate the importance of different components of the Transformer, we varied our base model "
    #         "in different ways, measuring the change in performance on English-to-German translation on the "
    #         "development set, newstest2013. We used beam search as described in the previous section, but no "
    #         "checkpoint averaging. We present these results in Table 3. "
    #         "In Table 3 rows (A), we vary the number of attention heads and the attention key"
    #     )
    # ]   
    # example_chunks = [
    #     "6 Results",
    #     "6.1 Machine Translation",
    #     # Add a paragraph or multi-section chunk here for testing
    # ]
    pdf_path = "input/single_page.pdf"

    results = match_chunks_to_pdf(example_chunks, pdf_path)
    for result in results:
        print("\nMatched Chunk Metadata:")
        print(f"  Matched Text: {result['matched_text']}")
        print(f"  Pages: {result['pages']}")
        print(f"  Section Headers: {result['section_headers']}")
        print(f"  Bounding Boxes:")
        for bbox in result['bounding_boxes']:
            print(f"    Page {bbox['page_no']}: {bbox['bbox']}")
