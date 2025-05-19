import os
import re

def parse_doctags(content: str) -> str:
    """
    Recursively parse doctags content and convert to Markdown.
    """
    tag_pattern = re.compile(r"<(?P<tag>\w+)(?:\s[^>]*)?>(?P<content>.*?)</\1>", re.DOTALL)

    def replace_tag(match):
        tag = match.group("tag")
        inner_content = match.group("content").strip()
        # Recursively process inner content
        processed_content = parse_doctags(inner_content)

        if tag == "section_header_level_1":
            return f"# {processed_content}"
        elif tag == "section_header_level_2":
            return f"## {processed_content}"
        elif tag == "text":
            return processed_content
        elif tag == "caption":
            return f"_{processed_content}_"
        elif tag == "page_break":
            return "---"
        elif tag == "unordered_list":
            return processed_content
        elif tag == "list_item":
            return f"- {processed_content}"
        elif tag == "picture":
            return ""  # Placeholder for images
        elif tag == "page_footer":
            return ""  # Skip footers
        else:
            # Default fallback
            return processed_content

    # Process all tags recursively
    while True:
        content, count = tag_pattern.subn(replace_tag, content)
        if count == 0:
            break

    return content

def parse_doctags_file(doctags_path: str) -> str:
    with open(doctags_path, "r", encoding="utf-8") as f:
        content = f.read()

    markdown_content = parse_doctags(content)

    # Remove any remaining tags
    residual_tag_pattern = re.compile(r"<[^>]+>")
    markdown_content = residual_tag_pattern.sub("", markdown_content)

    # Normalize whitespace
    lines = [line.strip() for line in markdown_content.splitlines()]
    markdown_lines = [line for line in lines if line]
    return "\n\n".join(markdown_lines)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "output", "Research_Paper_on_Artificial_Intelligence.doctags")
    output_path = os.path.join(base_dir, "README.md")

    markdown_content = parse_doctags_file(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"✅ README.md generated at {output_path}")

if __name__ == "__main__":
    main()
