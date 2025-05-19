import difflib
import os

def load_readme_lines(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_doctags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def find_best_matches(readme_lines, doctag_lines, threshold=0.8):
    matches = []

    for i, readme_line in enumerate(readme_lines, start=1):
        best_score = 0
        best_j = -1
        for j, doctag_line in enumerate(doctag_lines, start=1):
            score = difflib.SequenceMatcher(None, readme_line, doctag_line).ratio()
            if score > best_score:
                best_score = score
                best_j = j
        if best_score >= threshold:
            matches.append((i, best_j, readme_line, doctag_lines[best_j - 1], round(best_score, 3)))

    return matches

def print_matches(matches):
    for readme_idx, doctag_idx, readme_line, doctag_line, score in matches:
        print(f"\nREADME Line {readme_idx} → Doctag Line {doctag_idx} (Score: {score})")
        print(f"  README: {readme_line[:100]}{'...' if len(readme_line) > 100 else ''}")
        print(f"  Doctag: {doctag_line[:100]}{'...' if len(doctag_line) > 100 else ''}")

if __name__ == "__main__":
    readme_path = os.path.join("output", "single_page.md")
    doctags_path = os.path.join("output", "single_page.doctags")

    readme_lines = load_readme_lines(readme_path)
    doctag_lines = load_doctags(doctags_path)

    matches = find_best_matches(readme_lines, doctag_lines)
    print_matches(matches)
