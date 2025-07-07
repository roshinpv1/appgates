#!/usr/bin/env python3

import markdown
from weasyprint import HTML
import os

def convert_markdown_to_pdf(markdown_file, output_file):
    """Convert markdown file to PDF"""
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    
    # Add some basic styling
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #eee; }}
            h3 {{ color: #7f8c8d; }}
            code {{ background: #f8f9fa; padding: 2px 5px; border-radius: 3px; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f8f9fa; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    HTML(string=styled_html).write_pdf(output_file)

if __name__ == "__main__":
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input and output files
    markdown_file = os.path.join(current_dir, "validation_documentation.md")
    output_file = os.path.join(current_dir, "validation_documentation.pdf")
    
    # Convert markdown to PDF
    convert_markdown_to_pdf(markdown_file, output_file)
    print(f"PDF generated successfully: {output_file}") 