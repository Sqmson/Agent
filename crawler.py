import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

BASE = "https://www.nita.go.ug"
visited = set()
to_visit = [BASE]
scraped = ""
LIMIT = 50

def clean(text):
    return text.replace('\xa0', ' ').strip()

async def crawl():
    global scraped
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        while to_visit and len(visited) < LIMIT:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                await page.goto(url, timeout=60000, wait_until="networkidle")
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Extract content likely to be dynamically posted
                title = soup.find("h1")
                if title:
                    scraped += f"# {clean(title.text)}\n\n"

                for tag in soup.find_all(["h2", "h3", "p", "li"]):
                    text = clean(tag.get_text())
                    if len(text) > 40:
                        scraped += f"{text}\n\n"

                print(f"[✓] Crawled {url} ({len(visited)}/{LIMIT})")

                # Follow internal links only
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    parsed = urlparse(href)
                    if parsed.scheme in ["http", "https"] or not parsed.netloc:
                        abs_url = urljoin(BASE, href)
                        if abs_url.startswith(BASE) and abs_url not in visited:
                            to_visit.append(abs_url)

            except Exception as e:
                print(f"[X] Error at {url}: {e}")

        await browser.close()

# Run the crawler
asyncio.run(crawl())

# Save to .txt (best for RAG/document parsing)
with open("context.txt", "w", encoding="utf-8") as f:
    f.write(scraped)

print("✅ Finished: Content saved to nita_crawled_output.txt")
