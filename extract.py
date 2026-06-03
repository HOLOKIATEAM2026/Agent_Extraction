import re
import os

html_path = r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Extract CSS
style_match = re.search(r"<style>(.*?)</style>", content, re.DOTALL)
css = style_match.group(1) if style_match else ""

os.makedirs(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\css", exist_ok=True)
with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\css\style.css", "w", encoding="utf-8") as f:
    css_cleaned = re.sub(r"/\* ─── ROUTING VIEWS ─── \*/.*?\.view-section\.active\s*\{\s*display:\s*block;\s*opacity:\s*1;\s*\}", "", css, flags=re.DOTALL)
    f.write(css_cleaned.strip())

# 2. Base HTML components
head = content.split("<style>")[0] + '<link rel="stylesheet" href="css/style.css">\n</head>\n<body>\n<div class="grid-bg"></div>\n'

nav_match = re.search(r"<nav>.*?</nav>", content, re.DOTALL)
nav_base = nav_match.group(0)
nav_base = nav_base.replace('href="#home"', 'href="index.html"')
nav_base = nav_base.replace('href="#diagnostic"', 'href="diagnostic.html"')
nav_base = nav_base.replace('href="#multi"', 'href="multi.html"')
nav_base = nav_base.replace('href="#chat"', 'href="chat.html"')
nav_base = nav_base.replace('href="#historique"', 'href="historique.html"')

def get_nav_for_page(page_name):
    nav = nav_base
    if page_name == "home":
        nav = nav.replace('href="index.html"', 'href="index.html" style="color:var(--blue);font-weight:500;"')
    elif page_name == "diagnostic":
        nav = nav.replace('href="diagnostic.html"', 'href="diagnostic.html" style="color:var(--blue);font-weight:500;"')
    elif page_name == "multi":
        nav = nav.replace('href="multi.html"', 'href="multi.html" style="color:var(--blue);font-weight:500;"')
    elif page_name == "chat":
        nav = nav.replace('href="chat.html"', 'href="chat.html" style="color:var(--blue);font-weight:500;"')
    elif page_name == "historique":
        nav = nav.replace('href="historique.html"', 'href="historique.html" style="color:var(--blue);font-weight:500;"')
    return nav

# Extract HTML sections
view_home = re.search(r'<div id="view-home".*?</div>\s*<div id="view-diagnostic"', content, re.DOTALL).group(0).replace('<div id="view-diagnostic"', '').strip()
view_diagnostic = re.search(r'<div id="view-diagnostic".*?</div> <!-- /view-diagnostic -->', content, re.DOTALL).group(0).strip()
view_multi = re.search(r'<div id="view-multi".*?</div>\s*<div id="view-chat"', content, re.DOTALL).group(0).replace('<div id="view-chat"', '').strip()
view_chat = re.search(r'<div id="view-chat".*?</div>\s*<div id="view-historique"', content, re.DOTALL).group(0).replace('<div id="view-historique"', '').strip()
view_historique = re.search(r'<div id="view-historique".*?</div>\s*<script>', content, re.DOTALL).group(0).replace('<script>', '').strip()

def clean_view_wrapper(html_str):
    html_str = re.sub(r'^<div id="view-[a-z]+" class="view-section[^"]*">\s*', '', html_str)
    html_str = re.sub(r'</div>\s*(<!-- /view-diagnostic -->)?\s*$', '', html_str)
    return html_str

view_home = clean_view_wrapper(view_home)
view_diagnostic = clean_view_wrapper(view_diagnostic)
view_multi = clean_view_wrapper(view_multi)
view_chat = clean_view_wrapper(view_chat)
view_historique = clean_view_wrapper(view_historique)

# Extract JS
js_match = re.search(r"<script>(.*?)</script>", content, re.DOTALL)
js = js_match.group(1) if js_match else ""

os.makedirs(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js", exist_ok=True)

diag_js = re.search(r"(const fileInput = .*?btnCopy\.textContent = oldText, 2000\);\s*\}\);)", js, re.DOTALL).group(1)
diag_js += """
(() => {
  const storedStatus = getStored("holokia_status");
  if (storedStatus) {
    statusText.style.display = "block";
    statusText.textContent = storedStatus;
  }
  const isProcessing = getStored("holokia_processing") === "1";
  const jobId = getStored("holokia_job_id");
  const lastResult = getStoredJson("holokia_last_result");

  if (isProcessing && jobId) {
    btnExtract.disabled = true;
    setFormLocked(true);
    btnExtract.textContent = "TRAITEMENT...";
    resultsSection.style.display = "none";
    pollJobStatus(jobId);
    return;
  }

  if (lastResult) {
    showResults(lastResult, { scroll: false });
  }
})();
"""

chat_js = re.search(r"(// CHAT LOGIC.*?)(?=\n// MULTI-DOCS LOGIC)", js, re.DOTALL).group(1)
multi_js = re.search(r"(// MULTI-DOCS LOGIC.*?)(?=const observer = new IntersectionObserver)", js, re.DOTALL).group(1)
common_js = re.search(r"(const observer = new IntersectionObserver.*?\n},{threshold:0\.3\}\);\ndocument\.querySelectorAll\('\.tech-panel'\)\.forEach\(p => benchObs\.observe\(p\)\);)", js, re.DOTALL).group(1)

hist_js = re.search(r"(let allExtractions = \[\];.*?\n\}\);\n)", js, re.DOTALL).group(1)
hist_js += "loadHistorique();\n"

with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js\diagnostic.js", "w", encoding="utf-8") as f:
    f.write(diag_js.strip())
with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js\chat.js", "w", encoding="utf-8") as f:
    f.write(chat_js.strip())
with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js\multi.js", "w", encoding="utf-8") as f:
    f.write(multi_js.strip())
with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js\historique.js", "w", encoding="utf-8") as f:
    f.write(hist_js.strip())
with open(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html\js\common.js", "w", encoding="utf-8") as f:
    f.write(common_js.strip())

footer = "\n</body>\n</html>"

def create_page(filename, nav_id, content_html, scripts):
    filepath = os.path.join(r"c:\Users\boubk\Downloads\S8\Stage\RAG\html", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(head)
        f.write(get_nav_for_page(nav_id) + "\n\n")
        f.write(content_html + "\n\n")
        f.write('<script src="js/common.js"></script>\n')
        for script in scripts:
            f.write(f'<script src="js/{script}"></script>\n')
        f.write(footer)

create_page("index.html", "home", view_home, [])
create_page("diagnostic.html", "diagnostic", view_diagnostic, ["diagnostic.js"])
create_page("multi.html", "multi", view_multi, ["multi.js"])
create_page("chat.html", "chat", view_chat, ["chat.js"])
create_page("historique.html", "historique", view_historique, ["historique.js"])

print("Successfully separated all files!")
