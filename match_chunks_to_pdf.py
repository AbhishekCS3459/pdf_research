import logging
from pathlib import Path
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.chunking import HybridChunker
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

def match_chunks_to_pdf(input_chunks, pdf_file_path):
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
    print("Start-------------------------")
    print(doc_converter)
    print("End-------------------------")
    try:
        conv_result = doc_converter.convert(pdf_path)
        document = conv_result.document
        # Use HybridChunker to chunk the document
        chunker = HybridChunker()
        docling_chunks = chunker.chunk(document)
        print("\n--- HybridChunker Chunks ---\n")
        for i, c in enumerate(docling_chunks):
            print(f"Chunk {i}: {c.text[:200]}{'...' if len(c.text) > 200 else ''}")
        print("\n--- End of HybridChunker Chunks ---\n")
    except Exception as e:
        logging.exception(f"Error during document conversion: {e}")
        return []

    # Now match user chunks to the HybridChunker chunks for optimal matching
    results = []
    for chunk in input_chunks:
        norm_chunk = normalize_text(chunk)
        best_match = None
        best_score = 0
        for doc_chunk in docling_chunks:
            norm_doc_chunk = normalize_text(doc_chunk.text)
            # Try both containment and overlap for better matching
            if norm_chunk in norm_doc_chunk or norm_doc_chunk in norm_chunk:
                # Score: proportion of overlap
                overlap = min(len(norm_chunk), len(norm_doc_chunk))
                score = overlap / max(len(norm_chunk), len(norm_doc_chunk))
                if score > best_score:
                    best_score = score
                    best_match = doc_chunk
        if best_match:
            # Extract metadata from the best matching docling chunk
            pages = set()
            bboxes = []
            sections = set()
            for prov in getattr(best_match, 'prov', []):
                pages.add(prov.page_no)
                bboxes.append({
                    "page_no": prov.page_no,
                    "bbox": {
                        "l": prov.bbox.l,
                        "t": prov.bbox.t,
                        "r": prov.bbox.r,
                        "b": prov.bbox.b
                    }
                })
            if hasattr(best_match, 'section_header') and best_match.section_header:
                sections.add(best_match.section_header)
            results.append({
                "matched_text": best_match.text.strip(),
                "pages": sorted(list(pages)),
                "bounding_boxes": bboxes,
                "section_headers": list(sections)
            })
        else:
            # If no match, add a result with empty fields for visibility
            results.append({
                "matched_text": "",
                "pages": [],
                "bounding_boxes": [],
                "section_headers": []
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
