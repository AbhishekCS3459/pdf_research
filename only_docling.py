import json
import logging
import time
from pathlib import Path

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

_log = logging.getLogger(__name__)

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

def export_outputs(output_dir: Path, doc_filename: str, document):
    outputs = {
        ".json": json.dumps(document.export_to_dict(), indent=2),
        ".txt": document.export_to_text(),
        ".md": document.export_to_markdown(),
        ".doctags": document.export_to_document_tokens(),
    }

    for ext, content in outputs.items():
        out_path = output_dir / f"{doc_filename}{ext}"
        with out_path.open("w", encoding="utf-8") as fp:
            fp.write(content)
        _log.info(f"Exported {ext} to {out_path}")

def main():
    configure_logging()
    input_doc_path = Path("input/single_page.pdf")

    if not input_doc_path.exists():
        _log.error(f"Input file not found: {input_doc_path}")
        return

    _log.info("Starting document conversion pipeline...")

    pipeline_options = prepare_pipeline_options()

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    start_time = time.time()
    try:
        conv_result = doc_converter.convert(input_doc_path)
    except Exception as e:
        _log.exception(f"Error during document conversion: {e}")
        return
    end_time = time.time() - start_time

    _log.info(f"Document converted in {end_time:.2f} seconds.")

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = conv_result.input.file.stem

    export_outputs(output_dir, doc_filename, conv_result.document)

if __name__ == "__main__":
    main()
