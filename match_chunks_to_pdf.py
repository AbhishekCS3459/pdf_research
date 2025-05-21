import logging
from pathlib import Path
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

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

def match_chunks_to_pdf(chunks, pdf_file_path):
    """
    Matches the provided chunks to the PDF content and extracts metadata.

    Parameters:
        chunks (list of str): The text chunks to match.
        pdf_file_path (str): Path to the PDF file.

    Returns:
        list of dict: A list of matched metadata for each chunk.
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
    matched_results = []

    for chunk in chunks:
        for text_element in document.texts:
            if chunk in text_element.text:
                metadata = {
                    "chunk": chunk,
                    "page_no": text_element.prov[0].page_no,
                    "heading": text_element.label if text_element.label == "section_header" else None,
                    "bounding_box": {
                        "l": text_element.prov[0].bbox.l,
                        "t": text_element.prov[0].bbox.t,
                        "r": text_element.prov[0].bbox.r,
                        "b": text_element.prov[0].bbox.b
                    },
                    "page_width": text_element.prov[0].bbox.r - text_element.prov[0].bbox.l,
                    "page_height": text_element.prov[0].bbox.t - text_element.prov[0].bbox.b,
                }
                matched_results.append(metadata)

    return matched_results

if __name__ == "__main__":
    # Example usage
    example_chunks = ["6 Results", "6.1 Machine Translation"]
    pdf_path = "input/single_page.pdf"

    results = match_chunks_to_pdf(example_chunks, pdf_path)
    for result in results:
        print("\nMatched Chunk Metadata:")
        print(f"  Chunk: {result['chunk']}")
        print(f"  Page Number: {result['page_no']}")
        print(f"  Heading: {result['heading']}")
        print("  Bounding Box:")
        print(f"    Left: {result['bounding_box']['l']}")
        print(f"    Top: {result['bounding_box']['t']}")
        print(f"    Right: {result['bounding_box']['r']}")
        print(f"    Bottom: {result['bounding_box']['b']}")
        print(f"  Page Width: {result['page_width']}")
        print(f"  Page Height: {result['page_height']}")
