from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

FAVICON = 'https://orivector.jp/assets/favicon-512.png'
APPLE = 'https://orivector.jp/assets/apple-touch-icon.png'

EXCLUDES = {
    'root': {'index.html', 'about/index.html'},
    'aws': {'index.html', 'about/index.html'},
    'network': {'index.html', 'articles/index.html'},
    'toeic': {'index.html', 'articles/index.html', 'part5/index.html', 'vocabulary/index.html', 'phrases/index.html'},
}

META_PATTERNS = [
    r'\s*<link\b[^>]*\brel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*>\s*',
    r'\s*<meta\b[^>]*\bproperty=["\']og:image(?::width|:height|:alt)?["\'][^>]*>\s*',
    r'\s*<meta\b[^>]*\bname=["\']twitter:image["\'][^>]*>\s*',
    r'\s*<meta\b[^>]*\bname=["\']twitter:card["\'][^>]*>\s*',
    r'\s*<meta\b[^>]*\bproperty=["\']article:(?:published_time|modified_time)["\'][^>]*>\s*',
]

DATE_BLOCK_RE = re.compile(r'\s*<p\s+class=["\']orivector-article-dates["\'][^>]*>.*?</p>\s*', re.I | re.S)
JSONLD_RE = re.compile(r'(<script\s+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.I | re.S)
H1_RE = re.compile(r'(<h1\b[^>]*>.*?</h1>)', re.I | re.S)


def git_dates(path: Path):
    try:
        out = subprocess.check_output(
            ['git', 'log', '--follow', '--format=%aI', '--', str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except Exception:
        out = []
    if not out:
        return None, None
    return out[-1], out[0]


def is_article(path: Path, site: str) -> bool:
    rel = path.as_posix()
    return rel not in EXCLUDES.get(site, set()) and path.name == 'index.html'


def patch_jsonld(html: str, og: str, published: str | None, modified: str | None) -> str:
    def add_fields(obj):
        if isinstance(obj, dict):
            typ = obj.get('@type')
            types = typ if isinstance(typ, list) else [typ]
            if any(t in ('Article', 'LearningResource', 'TechArticle') for t in types):
                obj['image'] = og
                if published:
                    obj['datePublished'] = published
                if modified:
                    obj['dateModified'] = modified
            for value in obj.values():
                add_fields(value)
        elif isinstance(obj, list):
            for value in obj:
                add_fields(value)

    def repl(match):
        raw = match.group(2).strip()
        try:
            data = json.loads(raw)
        except Exception:
            return match.group(0)
        add_fields(data)
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + match.group(3)

    return JSONLD_RE.sub(repl, html)


def patch_file(path: Path, site: str, og: str):
    original = path.read_text(encoding='utf-8')
    html = original
    for pat in META_PATTERNS:
        html = re.sub(pat, '\n', html, flags=re.I)

    article = is_article(path, site)
    published = modified = None
    if article:
        published, modified = git_dates(path)

    block = [
        '<link rel="icon" type="image/png" sizes="512x512" href="%s">' % FAVICON,
        '<link rel="icon" type="image/svg+xml" href="https://orivector.jp/assets/favicon.svg">',
        '<link rel="apple-touch-icon" sizes="180x180" href="%s">' % APPLE,
        '<meta property="og:image" content="%s">' % og,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="ORIVECTOR study guide">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:image" content="%s">' % og,
    ]
    if article and published and modified:
        block += [
            '<meta property="article:published_time" content="%s">' % published,
            '<meta property="article:modified_time" content="%s">' % modified,
        ]
    seo_block = '\n'.join(block) + '\n'
    if '</head>' in html.lower():
        idx = html.lower().rfind('</head>')
        html = html[:idx] + seo_block + html[idx:]

    html = patch_jsonld(html, og, published if article else None, modified if article else None)

    html = DATE_BLOCK_RE.sub('\n', html)
    if article and published and modified:
        pub_date = published[:10]
        mod_date = modified[:10]
        visible = (
            '<p class="orivector-article-dates" style="margin:.55rem 0 1rem;color:#91a3ba;font-size:12px">'
            f'公開日：<time datetime="{published}">{pub_date}</time>'
            ' ｜ '
            f'更新日：<time datetime="{modified}">{mod_date}</time>'
            '</p>'
        )
        html, count = H1_RE.subn(r'\1\n' + visible, html, count=1)
        if count == 0:
            print(f'WARN: no h1 for date block: {path}')

    if html != original:
        path.write_text(html, encoding='utf-8')
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', choices=['root', 'aws', 'network', 'toeic'], required=True)
    ap.add_argument('--og', required=True)
    args = ap.parse_args()

    changed = []
    for path in sorted(Path('.').rglob('*.html')):
        if '.git' in path.parts:
            continue
        if patch_file(path, args.site, args.og):
            changed.append(path.as_posix())

    print(f'Patched {len(changed)} HTML files.')
    for p in changed:
        print(p)


if __name__ == '__main__':
    main()
