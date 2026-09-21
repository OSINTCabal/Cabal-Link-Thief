#!/usr/bin/env python3
"""Cabal-Link-Thief - OSINT link and contact information extractor."""

__version__ = "1.0.0"

import asyncio
import json
import re
import socket
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse


# ANSI Color Codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

    GREY = '\033[90m'


# Spinner animation
class Spinner:
    SPINNERS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    @staticmethod
    def spin():
        for spinner in Spinner.SPINNERS:
            yield spinner
    
    @staticmethod
    async def show_spinner(text, interval=0.1):
        spinner_gen = Spinner.spin()
        while True:
            sys.stdout.write(f'\r{next(spinner_gen)} {text}')
            sys.stdout.flush()
            await asyncio.sleep(interval)


# Terminal animation effects
class Effects:
    BANNER_COLORS = [Colors.CYAN, Colors.MAGENTA, Colors.BLUE, Colors.GREEN]

    @staticmethod
    def banner_reveal(lines, delay=0.04):
        for i, line in enumerate(lines):
            color = Effects.BANNER_COLORS[i % len(Effects.BANNER_COLORS)]
            sys.stdout.write(f'{Colors.BOLD}{color}{line}{Colors.RESET}\n')
            sys.stdout.flush()
            time.sleep(delay)

    # Color map for the alien picture: green blinds, grey computer, green alien
    FACE_ROWS = range(10, 17)
    FACE_COLS = (20, 47)
    HAND_ROW = 20
    HAND_COLS = (40, 44)

    @staticmethod
    def _picture_char_color(i, j):
        if i in Effects.FACE_ROWS and Effects.FACE_COLS[0] <= j <= Effects.FACE_COLS[1]:
            return Colors.GREEN
        if i == Effects.HAND_ROW and Effects.HAND_COLS[0] <= j <= Effects.HAND_COLS[1]:
            return Colors.GREEN
        if 19 <= j <= 58:
            return Colors.GREY
        return Colors.GREEN

    @staticmethod
    def render_picture(lines, delay=0.03):
        for i, line in enumerate(lines):
            out = []
            run_color = None
            for j, ch in enumerate(line):
                color = Effects._picture_char_color(i, j)
                if color != run_color:
                    out.append(color)
                    run_color = color
                out.append(ch)
            out.append(Colors.RESET)
            sys.stdout.write(''.join(out) + '\n')
            sys.stdout.flush()
            time.sleep(delay)

    @staticmethod
    def typewriter(text, color='', delay=0.01):
        for ch in text:
            sys.stdout.write(f'{color}{ch}{Colors.RESET}' if color else ch)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def totals_count_up(total_emails, total_phones, total_social, steps=15, delay=0.04):
        for i in range(1, steps + 1):
            e = int(total_emails * i / steps)
            p = int(total_phones * i / steps)
            s = int(total_social * i / steps)
            line = f" TOTALS: {e} emails | {p} phones | {s} social links ".center(100)
            sys.stdout.write(f'\r{Colors.BOLD}{Colors.GREEN}{line}{Colors.RESET}')
            sys.stdout.flush()
            time.sleep(delay)
        print()


# Colorize text
class Colorize:
    @staticmethod
    def color(text, color_code):
        return f'{color_code}{text}{Colors.RESET}'
    
    @staticmethod
    def header(text):
        return Colorize.color(text, Colors.CYAN + Colors.BOLD)
    
    @staticmethod
    def success(text):
        return Colorize.color(text, Colors.GREEN)
    
    @staticmethod
    def warning(text):
        return Colorize.color(text, Colors.YELLOW)
    
    @staticmethod
    def error(text):
        return Colorize.color(text, Colors.RED)
    
    @staticmethod
    def info(text):
        return Colorize.color(text, Colors.BLUE)
    
    @staticmethod
    def dim(text):
        return Colorize.color(text, Colors.DIM)
    
    @staticmethod
    def subdomain(text):
        return Colorize.color(text, Colors.MAGENTA + Colors.BOLD)
    
    @staticmethod
    def email(text):
        return Colorize.color(text, Colors.GREEN)
    
    @staticmethod
    def phone(text):
        return Colorize.color(text, Colors.CYAN)
    
    @staticmethod
    def social(text):
        return Colorize.color(text, Colors.BLUE)
    
    @staticmethod
    def address(text):
        return Colorize.color(text, Colors.YELLOW)
    
    @staticmethod
    def ip(text):
        return Colorize.color(text, Colors.RED)
    
    @staticmethod
    def name(text):
        return Colorize.color(text, Colors.MAGENTA)
    
    @staticmethod
    def title(text):
        return Colorize.color(text, Colors.CYAN)


BANNER = r"""   ,_       ,_
   ,~-,    .~, .~,                                          /  ;-~,-", "  ;'
  Q| ' ;=-'  |~;  ;========================================o   :   |    ;Q
   |   |     : :  |                                        ;   |   :    :
   |   ;     |    ;                                        :   :   |    |
   |   :     ;     :  ______________________________       |   |   :    :
   |         :   ' | |                              |      ;   :   |    |
   |   |     |     : |  __________________________  |      :   |   :    :
   |   ;   : :      .|  |                        |  |      |   :   |    :
   |   :     ;      ||  |                        |  |      ;   :   :    :
   |         |       ,"   .-""-.^._.-^,.-'"'-.   |  |      |   |   :    :
   |   |     ;    :   ;-\ /    .;-( \ - ;.    \  |  |      |   :   :    :
   |   ;     :     :   \ )\  ; /   ~`    \ ;  /  |  |      ;   |   :    :
   |   :     |      ,   ;)`;_.,;:.  O  .:;,_.'   |  |      :   :   |    :
   |         :         / `. `-.,::.` .::;        |  |      |   |   :    :
   |   |     ;        ; |  `-_ / `"`;:`"` `-      |  |      ;   |   :    :
   |   ;     |        | |    `/     o    ; |     |  |      :   :   |    :
   |   :     ;        | |____/______|____| |_____|  |      |   |   :    :
   |         :        |                  | |        |      ;   :   :    |
   |   |   : |        |                  | |   []   |      :   |   :    :
   |   ;     :    :   |_________________( __)_______|      |   |   :    |
   |   :     ;        |'._;=======;+-,-'`   `.=;__.'       ;   |   :    :
   |         |        |_________|____'-~|  `  :______      :   :   |    |
   |   |     :        |-=-=-=-=-=-=-=-=-/ ',',|=-=-  "-._  |   |   :    :
   |   ;     ;        |=-=-=-=-=-=-=-=-: / / /'-=-=-=- __",;   |   :    :
   |   :     |   '    |_________________"-_`"___________ __|   |   :    :
   |         :        |_________________________________/  ;   :   |    :
   |   |     ;        |                                    :   :   |    :
   |   ;   : |   :    |                                    |   |   :    |
   |   : .   :        |                                    ;   :   :    :
   ; : .~`\' :\| '  _.|                                     \  ;._ ;.   |
   :_,/    '-' '_,-'                                         '~`  "" "-,"

   _____      _           _   _      _       _    
  / ____|    | |         | | | |    (_)     | |   
 | |     __ _| |__   __ _| | | |     _ _ __ | | __
 | |    / _` | '_ \ / _` | | | |    | | '_ \| |/ /
 | |___| (_| | |_) | (_| | | | |____| | | | |   < 
  \_____\__,_|_.__/ \__,_|_| |______|_|_| |_|_|\_\
           _______ _          _  __               
          |__   __| |        (_)/ _|              
             | |  | |__   ___ _| |_               
             | |  | '_ \ / _ \ |  _|              
             | |  | | | |  __/ | |                
             |_|  |_| |_|\___|_|_|"""

COMMON_SUBDOMAINS = [
    "www", "mail", "smtp", "pop", "imap", "ftp",
    "webmail", "admin", "blog", "shop", "store", "api",
    "dev", "test", "staging", "beta", "m", "mobile",
    "app", "apps", "portal", "secure", "login", "account",
    "support", "help", "docs", "status", "health", "news",
    "press", "media", "video", "images", "img", "static",
    "cdn", "assets", "download", "files", "data", "db",
    "mysql", "postgres", "redis", "git", "svn", "code",
    "repo", "ci", "build", "jenkins", "chat", "irc",
    "forums", "community", "social", "links", "about",
    "contact", "connect", "info", "user", "users",
    "service", "services", "cloud", "office", "exchange",
    "outlook", "cpanel", "whm", "sip", "voip", "phone",
    "tel", "directory", "people", "staff", "team",
]

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?'
    r'(?:\(?\d{3}\)?[-.\s]?)'
    r'\d{3}[-.\s]?\d{4}'
)

SOCIAL_PATTERNS = {
    'X/Twitter': re.compile(r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+', re.I),
    'Facebook': re.compile(r'(?:https?://)?(?:www\.)?facebook\.com/[a-zA-Z0-9(\.|\-|_)]+', re.I),
    'LinkedIn': re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|company|school)/[a-zA-Z0-9\-]+', re.I),
    'Instagram': re.compile(r'(?:https?://)?(?:www\.)?instagram\.com/[a-zA-Z0-9._]+', re.I),
    'YouTube': re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:c|user|channel|@)?[a-zA-Z0-9\-]+', re.I),
    'TikTok': re.compile(r'(?:https?://)?(?:www\.)?tiktok\.com/@[a-zA-Z0-9._]+', re.I),
    'Reddit': re.compile(r'(?:https?://)?(?:www\.)?reddit\.com/(?:r|u)/[a-zA-Z0-9_]+', re.I),
    'GitHub': re.compile(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9\-]+', re.I),
}

IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

ADDRESS_PATTERN = re.compile(
    r'\b\d{1,5}\s+[a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|lane|ln|drive|dr|way|boulevard|blvd|plaza|place)\b',
    re.IGNORECASE
)

NAME_PATTERN = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b')

TITLE_PATTERN = re.compile(
    r'\b(?:CEO|CFO|CTO|President|Vice\s+President|VP|Director|Manager|Engineer|Developer|Analyst|Consultant)\b',
    re.IGNORECASE
)

class DomainScanner:
    def __init__(self, domain: str, timeout: float = 10.0, max_concurrent: int = 20):
        self.domain = domain.strip().lower()
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.subdomains: Set[str] = set()
        self.pages_scanned: Set[str] = set()
        self.results: Dict[str, Dict] = defaultdict(lambda: {
            'emails': set(),
            'phones': set(),
            'social': set(),
            'addresses': set(),
            'ips': set(),
            'names': set(),
            'titles': set(),
            'urls': set()
        })

    async def resolve_subdomain(self, subdomain: str) -> Optional[str]:
        try:
            full_domain = f"{subdomain}.{self.domain}"
            for domain_to_try in [full_domain, f"www.{full_domain}"]:
                try:
                    socket.gethostbyname_ex(domain_to_try)
                    return domain_to_try
                except (socket.gaierror, socket.timeout):
                    continue
            return None
        except Exception:
            return None

    async def discover_subdomains(self) -> List[str]:
        print(f"{Colorize.header('[')}1{Colorize.header(']')} {Colorize.info('Resolving subdomains via DNS...')}")

        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        total_subdomains = len(COMMON_SUBDOMAINS)
        found_count = 0
        resolved_count = 0

        async def check_subdomain(sub: str):
            nonlocal found_count, resolved_count
            async with semaphore:
                resolved = await self.resolve_subdomain(sub)
                resolved_count += 1
                if resolved:
                    self.subdomains.add(resolved)
                    found_count += 1
                spinner = Spinner.SPINNERS[resolved_count % len(Spinner.SPINNERS)]
                # Clear spinner line, print any new finding, redraw spinner
                sys.stdout.write(f'\r{" " * 100}\r')
                if resolved:
                    print(f"  {Colorize.success('✓')} {Colorize.subdomain(resolved)} {Colorize.dim(f'({found_count} found)')}")
                sys.stdout.write(f'  {Colorize.info(spinner)} {Colorize.dim(f"Resolving subdomains... {resolved_count}/{total_subdomains} ({found_count} found)")}')
                sys.stdout.flush()

        for sub in COMMON_SUBDOMAINS:
            task = asyncio.create_task(check_subdomain(sub))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            socket.gethostbyname_ex(self.domain)
            self.subdomains.add(self.domain)
            sys.stdout.write(f'\r{" " * 100}\r')
            print(f"  {Colorize.success('✓')} {Colorize.subdomain(self.domain)}")
        except:
            pass

        sys.stdout.write(f'\r{" " * 100}\r')
        Effects.typewriter(f"  DNS discovery complete: {len(self.subdomains)} subdomains found", Colors.GREEN + Colors.BOLD, delay=0.005)
        return sorted(self.subdomains)

    def extract_emails(self, text: str) -> Set[str]:
        return set(EMAIL_PATTERN.findall(text))

    def extract_phones(self, text: str) -> Set[str]:
        phones = set()
        for match in PHONE_PATTERN.finditer(text):
            phone = match.group()
            phone = re.sub(r'[^\d+]', '', phone)
            if phone and len(phone) >= 7:
                phones.add(phone)
        return phones

    def extract_social(self, text: str) -> Set[str]:
        social = set()
        for platform, pattern in SOCIAL_PATTERNS.items():
            for match in pattern.finditer(text):
                social.add(match.group())
        return social

    def extract_ips(self, text: str) -> Set[str]:
        return set(IP_PATTERN.findall(text))

    def extract_addresses(self, text: str) -> Set[str]:
        return set(ADDRESS_PATTERN.findall(text))

    def extract_names(self, text: str) -> Set[str]:
        return set(NAME_PATTERN.findall(text))

    def extract_titles(self, text: str) -> Set[str]:
        return set(TITLE_PATTERN.findall(text))

    def extract_links(self, html: str, base_url: str) -> Set[str]:
        links = set()
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href and not href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    full_url = urljoin(base_url, href)
                    links.add(full_url)
        except:
            pass
        return links

    def get_subdomain_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        if host.endswith(self.domain):
            sub = host[:-len(self.domain)-1] if host != self.domain else self.domain
            return sub if sub else self.domain
        return host

    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            import httpx
            timeout_config = httpx.Timeout(self.timeout)
            async with httpx.AsyncClient(
                timeout=timeout_config,
                follow_redirects=True,
                max_redirects=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as client:
                response = await client.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    return response.text
                return None
        except Exception:
            return None

    async def scan_page(self, url: str, subdomain: str):
        if url in self.pages_scanned:
            return
        self.pages_scanned.add(url)
        html = await self.fetch_page(url)
        if not html:
            return

        extracted = {
            'emails': self.extract_emails(html),
            'phones': self.extract_phones(html),
            'social': self.extract_social(html),
            'addresses': self.extract_addresses(html),
            'ips': self.extract_ips(html),
            'names': self.extract_names(html),
            'titles': self.extract_titles(html),
        }

        sub_key = subdomain
        for key, values in extracted.items():
            if values:
                self.results[sub_key][key].update(values)

        links = self.extract_links(html, url)
        if links:
            self.results[sub_key]['urls'].update(links)

    async def scan_all_pages(self, subdomains: List[str], max_pages: int = 50):
        pages_to_scan = set()
        for subdomain in subdomains:
            for scheme in ['https://', 'http://']:
                url = f"{scheme}{subdomain}"
                pages_to_scan.add(url)
        
        pages_to_scan = list(pages_to_scan)[:max_pages]
        total_pages = len(pages_to_scan)
        scanned_count = 0
        
        print(f"\n{Colorize.header('[')}2{Colorize.header(']')} {Colorize.info(f'Found {len(subdomains)} subdomains. Crawling {total_pages} pages...')}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []

        async def scan_single(url: str):
            nonlocal scanned_count
            async with semaphore:
                subdomain = self.get_subdomain_from_url(url)
                await self.scan_page(url, subdomain)
                scanned_count += 1
                result_counts = self.get_summary().get(subdomain, {})
                total_findings = sum(result_counts.values())
                spinner = Spinner.SPINNERS[scanned_count % len(Spinner.SPINNERS)]
                # Clear spinner line, print findings if any, redraw spinner
                sys.stdout.write(f'\r{" " * 100}\r')
                if total_findings:
                    print(f"  {Colorize.success('✓')} {Colorize.subdomain(subdomain)} {Colorize.success(f'+{total_findings} findings')}")
                sys.stdout.write(f'  {Colorize.info(spinner)} {Colorize.dim(f"Crawling pages... {scanned_count}/{total_pages}")}')
                sys.stdout.flush()

        for url in pages_to_scan:
            task = asyncio.create_task(scan_single(url))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        sys.stdout.write(f'\r{" " * 100}\r')
        Effects.typewriter(f"  Crawl complete: {scanned_count} pages scanned", Colors.GREEN + Colors.BOLD, delay=0.005)
        return len(pages_to_scan)

    def get_all_results(self) -> Dict:
        return dict(self.results)

    def get_summary(self) -> Dict[str, Dict[str, int]]:
        summary = {}
        for subdomain, data in self.results.items():
            summary[subdomain] = {k: len(v) for k, v in data.items()}
        return summary


def print_banner():
    lines = BANNER.splitlines()
    Effects.render_picture(lines[:32])
    Effects.banner_reveal(lines[32:])


def print_results_organized(scanner: DomainScanner):
    results = scanner.get_all_results()
    summary = scanner.get_summary()

    separator = Colorize.color("=" * 100, Colors.DIM)

    print(f"\n{separator}")
    Effects.typewriter(" SCAN RESULTS ORGANIZED BY SUBDOMAIN ".center(100), Colors.CYAN + Colors.BOLD, delay=0.005)
    print(separator)

    total_emails = 0
    total_phones = 0
    total_social = 0

    for subdomain, counts in summary.items():
        data = results[subdomain]
        total_findings = sum(counts.values())
        total_emails += counts.get('emails', 0)
        total_phones += counts.get('phones', 0)
        total_social += counts.get('social', 0)

        print(f"\n{separator}")
        header = f" SUBDOMAIN: {subdomain} "
        Effects.typewriter(header.center(100, "="), Colors.MAGENTA + Colors.BOLD, delay=0.002)
        print(separator)

        if data['emails']:
            print(f"\n {Colorize.header('Emails')} {Colorize.dim(f'[{len(data["emails"])}]')}:")
            for email in sorted(data['emails']):
                print(f"  {Colorize.success('+')} {Colorize.email(email)}")

        if data['phones']:
            print(f"\n {Colorize.header('Phone Numbers')} {Colorize.dim(f'[{len(data["phones"])}]')}:")
            for phone in sorted(data['phones']):
                print(f"  {Colorize.success('+')} {Colorize.phone(phone)}")

        if data['social']:
            print(f"\n {Colorize.header('Social Media Links')} {Colorize.dim(f'[{len(data["social"])}]')}:")
            for social in sorted(data['social']):
                print(f"  {Colorize.success('+')} {Colorize.social(social)}")

        if data['addresses']:
            print(f"\n {Colorize.header('Addresses')} {Colorize.dim(f'[{len(data["addresses"])}]')}:")
            for addr in sorted(data['addresses']):
                print(f"  {Colorize.success('+')} {Colorize.address(addr)}")

        if data['ips']:
            print(f"\n {Colorize.header('IP Addresses')} {Colorize.dim(f'[{len(data["ips"])}]')}:")
            for ip in sorted(data['ips']):
                print(f"  {Colorize.success('+')} {Colorize.ip(ip)}")

        if data['names']:
            print(f"\n {Colorize.header('Names and Key Terms')} {Colorize.dim(f'[{len(data["names"])}]')}:")
            for name in sorted(data['names'])[:20]:
                print(f"  {Colorize.success('+')} {Colorize.name(name)}")
            if len(data['names']) > 20:
                print(f"  {Colorize.dim('... and')} {Colorize.warning(f'{len(data["names"]) - 20} more')}")

        if data['titles']:
            print(f"\n {Colorize.header('Job Titles')} {Colorize.dim(f'[{len(data["titles"])}]')}:")
            for title in sorted(data['titles'])[:20]:
                print(f"  {Colorize.success('+')} {Colorize.title(title)}")
            if len(data['titles']) > 20:
                print(f"  {Colorize.dim('... and')} {Colorize.warning(f'{len(data["titles"]) - 20} more')}")

        if data['urls']:
            print(f"\n {Colorize.header('URLs Found')} {Colorize.dim(f'[{len(data["urls"])}]')}:")
            for url in sorted(data['urls'])[:10]:
                print(f"  {Colorize.success('+')} {url}")
            if len(data['urls']) > 10:
                print(f"  {Colorize.dim('... and')} {Colorize.warning(f'{len(data["urls"]) - 10} more')}")

        if total_findings == 0:
            print(f"\n  {Colorize.warning('No findings for this subdomain')}")

    print(f"\n{separator}")
    Effects.totals_count_up(total_emails, total_phones, total_social)
    print(separator)
    print(f"\n{separator}")
    Effects.typewriter(" DISCLAIMER: Results are based only on publicly accessible content.".center(100), Colors.YELLOW, delay=0.004)
    Effects.typewriter("            A missing result does NOT prove data does not exist.".center(100), Colors.YELLOW, delay=0.004)
    print(separator)


def export_to_json(scanner: DomainScanner, filename: str = None):
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = scanner.domain.replace('.', '_')
        filename = f"{domain_name}_scan_{timestamp}.json"

    results = scanner.get_all_results()
    summary = scanner.get_summary()

    serializable_results = {}
    for subdomain, data in results.items():
        serializable_results[subdomain] = {k: list(v) for k, v in data.items()}

    output = {
        'domain': scanner.domain,
        'scanned_at': datetime.now().isoformat(),
        'subdomains_found': list(scanner.subdomains),
        'pages_scanned': len(scanner.pages_scanned),
        'summary': summary,
        'results': serializable_results
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    return filename


def export_to_markdown(scanner: DomainScanner, filename: str = None):
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = scanner.domain.replace('.', '_')
        filename = f"{domain_name}_scan_{timestamp}.md"

    results = scanner.get_all_results()
    summary = scanner.get_summary()

    with open(filename, 'w') as f:
        f.write(f"# OSINT Scan Report: {scanner.domain}\n\n")
        f.write(f"**Scanned at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Subdomains found:** {len(scanner.subdomains)}\n\n")
        f.write(f"**Pages scanned:** {len(scanner.pages_scanned)}\n\n")
        f.write("---\n\n")
        f.write("## Summary by Subdomain\n\n")
        f.write("| Subdomain | Emails | Phones | Social | Addresses | IPs | Names | Titles | URLs |\n")
        f.write("|-----------|--------|--------|--------|-----------|-----|-------|--------|-----|\n")

        for subdomain, counts in summary.items():
            f.write(f"| {subdomain} | {counts.get('emails', 0)} | {counts.get('phones', 0)} | {counts.get('social', 0)} | {counts.get('addresses', 0)} | {counts.get('ips', 0)} | {counts.get('names', 0)} | {counts.get('titles', 0)} | {counts.get('urls', 0)} |\n")

        f.write("\n---\n\n")

        for subdomain, data in results.items():
            f.write(f"## {subdomain}\n\n")
            if data['emails']:
                f.write("### Emails\n\n")
                for email in sorted(data['emails']):
                    f.write(f"- {email}\n")
                f.write("\n")
            if data['phones']:
                f.write("### Phone Numbers\n\n")
                for phone in sorted(data['phones']):
                    f.write(f"- {phone}\n")
                f.write("\n")
            if data['social']:
                f.write("### Social Media Links\n\n")
                for social in sorted(data['social']):
                    f.write(f"- {social}\n")
                f.write("\n")
            if data['addresses']:
                f.write("### Addresses\n\n")
                for addr in sorted(data['addresses']):
                    f.write(f"- {addr}\n")
                f.write("\n")
            if data['ips']:
                f.write("### IP Addresses\n\n")
                for ip in sorted(data['ips']):
                    f.write(f"- {ip}\n")
                f.write("\n")
            if data['names']:
                f.write("### Names and Key Terms\n\n")
                for name in sorted(data['names'])[:100]:
                    f.write(f"- {name}\n")
                if len(data['names']) > 100:
                    f.write(f"\n... and {len(data['names']) - 100} more\n")
                f.write("\n")
            if data['titles']:
                f.write("### Job Titles\n\n")
                for title in sorted(data['titles'])[:100]:
                    f.write(f"- {title}\n")
                if len(data['titles']) > 100:
                    f.write(f"\n... and {len(data['titles']) - 100} more\n")
                f.write("\n")
            if data['urls']:
                f.write("### URLs\n\n")
                for url in sorted(data['urls'])[:50]:
                    f.write(f"- {url}\n")
                if len(data['urls']) > 50:
                    f.write(f"\n... and {len(data['urls']) - 50} more\n")
                f.write("\n")

        f.write("---\n\n")
        f.write("**Disclaimer:** Results are based only on publicly accessible content. "
                "A missing result does NOT prove data does not exist.\n")
    return filename


async def main():
    print_banner()
    domain = input(f"\n{Colorize.header('Enter a domain to scan: ')}").strip()

    if not domain:
        print(Colorize.error("Error: No domain provided."))
        sys.exit(1)

    print(f"\n{Colorize.info('Scanning:')} {Colorize.subdomain(domain)}")
    print(f"{Colorize.info('Discovering subdomains and crawling pages...')}\n")

    scanner = DomainScanner(domain, timeout=15.0, max_concurrent=30)

    try:
        subdomains = await scanner.discover_subdomains()

        if not subdomains:
            print(f"\n{Colorize.warning('No subdomains discovered.')}")
            separator = Colorize.color("=" * 100, Colors.DIM)
            print(f"\n{separator}")
            print(Colorize.warning(" DISCLAIMER: Results are based only on publicly accessible content.").center(100))
            print(separator)
            sys.exit(0)

        pages_scanned = await scanner.scan_all_pages(subdomains, max_pages=50)
        print_results_organized(scanner)

        separator = Colorize.color("=" * 100, Colors.DIM)
        print(f"\n{separator}")
        save_choice = input(f"{Colorize.header('Do you want to save the results?')} {Colorize.dim('(json/md/both/none): ')}").strip().lower()
        print(separator)

        saved_files = []

        if save_choice in ['json', 'both']:
            json_file = export_to_json(scanner)
            saved_files.append(json_file)
            print(f"\n {Colorize.success('JSON saved to:')} {Colorize.info(json_file)}")

        if save_choice in ['md', 'both']:
            md_file = export_to_markdown(scanner)
            saved_files.append(md_file)
            print(f" {Colorize.success('Markdown saved to:')} {Colorize.info(md_file)}")

        if save_choice == 'both':
            print(f"\n {Colorize.success('Results saved to both JSON and Markdown files')}")
        elif save_choice == 'none':
            print(f"\n {Colorize.warning('Results not saved.')}")
        elif save_choice not in ['json', 'md', 'both', 'none']:
            print(f"\n {Colorize.error('Invalid choice. Results not saved.')}")

    except KeyboardInterrupt:
        print(f"\n\n{Colorize.error('Scan interrupted by user.')}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colorize.error('Error during scan:')} {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        import httpx
        import bs4
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("Please install with: pip install httpx beautifulsoup4")
        sys.exit(1)

    asyncio.run(main())
