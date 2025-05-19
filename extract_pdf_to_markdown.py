import os
from docling.document_converter import DocumentConverter

def extract_pdf_content(file_path: str) -> str:
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()

def main():
    # Define input/output paths
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input", "sample-4.pdf")
    output_md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")

    # Extract structured Markdown
    markdown_content = extract_pdf_content(file_path)

    # Save to README.md
    with open(output_md_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)

    print(f"✅ PDF content extracted and saved to {output_md_path}")

if __name__ == "__main__":
    main()
