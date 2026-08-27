from markdown import markdown
from xhtml2pdf import pisa

def md_to_pdf(md_path: str, pdf_path: str, css_path: str = "./add_tools_helpers/styles.css"):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    html_body = markdown(
        md_text,
        extensions=["fenced_code", "tables", "toc"]
    )

    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
        {css}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    with open(pdf_path, "wb") as pdf_file:
        pisa.CreatePDF(full_html, dest=pdf_file)

def readme_to_xlm(readme_path: str, xlm_path: str):
    import subprocess

    try:
        subprocess.run(
            ["pandoc", readme_path, "-o", xlm_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert {readme_path} to XML: {e.stderr.decode()}")

user_manual_md = "C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Tercera versión/docs/user_manual.md"
user_manual_pdf = "C:/Users/aisha/OneDrive/Escritorio/tesis/Implementación/2. Desarrollo/Tercera versión/docs/user_manual.pdf"
md_to_pdf(user_manual_md, user_manual_pdf)