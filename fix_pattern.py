import json
import re

def rewrite_pattern(pat):
    # Only rewrite if '.*' is present and not inside a character class
    if '.*' not in pat:
        return pat
    # Handle common cases
    pat = re.sub(r'([A-Za-z0-9_]+)\.\*\(([A-Za-z0-9_]+)\)', r'\\b\1[A-Za-z0-9_]*\\(\2\\b', pat)
    pat = re.sub(r'([A-Za-z0-9_]+)\.\*([A-Za-z0-9_]+)', r'\\b\1[A-Za-z0-9_]*\2\\b', pat)
    pat = re.sub(r'([A-Za-z0-9_]+)\.\*', r'\\b\1[A-Za-z0-9_]*\\b', pat)
    pat = re.sub(r'\.\*([A-Za-z0-9_]+)', r'\\b[A-Za-z0-9_]*\1\\b', pat)
    return pat

def main():
    with open('gates/patterns/pattern_library.json', 'r') as f:
        data = json.load(f)

    for gate in data['gates']:
        for lang in data['gates'][gate].get('patterns', {}):
            for pat in data['gates'][gate]['patterns'][lang]:
                orig = pat['pattern']
                pat['pattern'] = rewrite_pattern(orig)

    with open('gates/patterns/pattern_library.json', 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main() 