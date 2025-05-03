import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

def collect_py_files(directory):
    py_files = []
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                if '__pycache__' not in full_path:
                    py_files.append(full_path)
    return py_files

def generate_pdf(py_files, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=20, leftMargin=20,
                            topMargin=20, bottomMargin=20)
    story = []

    styles = getSampleStyleSheet()
    code_style = ParagraphStyle('Code',
                                parent=styles['Normal'],
                                fontName='Courier',
                                fontSize=8,
                                leading=10,
                                alignment=TA_LEFT)

    base_path = os.path.commonpath(py_files) if py_files else ""

    for file_path in py_files:
        rel_path = os.path.relpath(file_path, base_path)
        story.append(Paragraph(f"<b>File: {rel_path}</b>", styles['Heading3']))
        story.append(Spacer(1, 4 * mm))

        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            story.append(Preformatted(code, code_style))
            story.append(Spacer(1, 10 * mm))

    doc.build(story)

def main():
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Enter the directory containing Python files: ").strip()

    if not os.path.isdir(directory):
        print("❌ Invalid directory path.")
        return

    py_files = collect_py_files(directory)
    if not py_files:
        print("⚠️ No valid Python files found.")
        return

    output_pdf = os.path.join(directory, "Collected_Python_Code.pdf")
    generate_pdf(py_files, output_pdf)
    print(f"\n✅ PDF successfully generated at:\n{output_pdf}")

if __name__ == "__main__":
    main()
