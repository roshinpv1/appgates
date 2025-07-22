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
    with open('/Users/roshinpv/Documents/next/appgates/gates/patterns/pattern_library.json', 'r') as f:
        data = json.load(f)

    for gate in data['gates']:
        print(f"Processing gate: {gate}")
        for lang in data['gates'][gate].get('patterns', {}):
            print(f"  Language: {lang}")
            print(f"    Pattern Match\tActual Pattern")
            for pat in data['gates'][gate]['patterns'][lang]:
                orig = pat['pattern']
                new_pat = rewrite_pattern(orig)
                print(f"    {orig}\t{new_pat}")
                pat['original_pattern'] = orig
                pat['pattern'] = new_pat

    with open('/Users/roshinpv/Documents/next/appgates/gates/patterns/pattern_library.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Generate HTML report
    html = [
        '<html><head><title>Pattern Report</title></head><body>',
        '<h1>Pattern Report</h1>',
        '<table border="1" cellpadding="5" cellspacing="0">',
        '<tr><th>Gate</th><th>Language</th><th>Pattern Match</th><th>Actual Pattern</th></tr>'
    ]
    for gate in data['gates']:
        for lang in data['gates'][gate].get('patterns', {}):
            for pat in data['gates'][gate]['patterns'][lang]:
                orig = pat.get('original_pattern', pat['pattern'])
                new_pat = pat['pattern']
                html.append(f'<tr><td>{gate}</td><td>{lang}</td><td>{orig}</td><td>{new_pat}</td></tr>')
    html.append('</table></body></html>')
    with open('/Users/roshinpv/Documents/next/appgates/gates/patterns/pattern_report.html', 'w') as f:
        f.write('\n'.join(html))
    print("Done!")

if __name__ == "__main__":
    main() 