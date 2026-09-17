#!/usr/bin/env python3
"""Generate the committed static pages using only Python's standard library."""
import argparse
from html import escape
import json
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html', 'research.html', 'publications.html')


def load(name):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'{name}.json: duplicate key {key!r}')
            result[key] = value
        return result
    return json.loads((ROOT / 'data' / f'{name}.json').read_text(encoding='utf-8'),
                      object_pairs_hook=unique_keys)


def text(value):
    if not isinstance(value, str):
        raise ValueError(f'Expected text, got {value!r}')
    return escape(value, quote=False)


def attributes(values):
    return ''.join(f' {key}="{escape(value, quote=True)}"' for key, value in values.items())


def link(value):
    if set(value) - {'text', 'href', 'target', 'rel'}:
        raise ValueError(f'Unknown link fields: {value}')
    if not value['href'].startswith(('https://', 'http://', './')):
        raise ValueError(f'Unsupported link URL: {value["href"]}')
    return '<a' + attributes({k: v for k, v in value.items() if k != 'text'}) + '>' + text(value['text']) + '</a>'


def paragraph(value):
    if isinstance(value, str):
        content = text(value)
    else:
        content = ''.join(text(part) if isinstance(part, str) else
                          '<br>' if part == {'break': True} else link(part)
                          for part in value)
    return '<p>' + content + '</p>'


def section(title, content):
    return '    <section>\n      <h2>' + text(title) + '</h2>\n' + content + '\n    </section>'


def render_home(sections):
    result = []
    for entry in sections:
        if 'items' in entry:
            items = []
            for item in entry['items']:
                heading = '<h3>' + text(item['title']) + '</h3>' if 'title' in item else ''
                items.append('<li>' + heading + ''.join(map(paragraph, item['paragraphs'])) + '</li>')
            content = '<ul>\n' + '\n'.join(items) + '\n</ul>'
        else:
            content = '\n'.join(map(paragraph, entry['paragraphs']))
        result.append(section(entry['title'], content))
    return '\n\n'.join(result)


def citation(entry):
    if set(entry) - {'authors', 'title', 'publication', 'link'}:
        raise ValueError(f'Unknown citation fields: {entry}')
    content = (text(entry['authors']) + ' <span class="citation-title">'
               + text(entry['title']) + '</span> ' + text(entry['publication']))
    if 'link' in entry:
        content += ' ' + link(entry['link'])
    return '<p class="citation">' + content + '</p>'


def render_publications(data):
    seen = []
    sections = []
    for category in data['categories']:
        ids = category['publications']
        seen.extend(ids)
        items = ['<li>' + citation(data['entries'][pid]) + '</li>' for pid in ids]
        sections.append(section(category['title'], '<ol>\n' + '\n'.join(items) + '\n</ol>'))
    if len(seen) != len(set(seen)) or set(seen) != set(data['entries']):
        raise ValueError('Each publication must appear in exactly one category')
    return '\n\n'.join(sections)


def render_research(topics, publications):
    sections = []
    for topic in topics:
        images = []
        for image in topic['images']:
            if set(image) != {'src', 'alt', 'width'}:
                raise ValueError(f'Expected image src, alt and width: {image}')
            if not (ROOT / image['src']).is_file():
                raise ValueError(f'Missing image: {image["src"]}')
            images.append('<img' + attributes(image) + '>')
        content = '\n'.join(images)
        if topic['group_images']:
            content = '<div>\n' + content + '\n</div>'
        content = '<div class="horizontal-center">\n' + content + '\n</div>\n'
        content += '\n'.join(map(paragraph, topic['paragraphs']))
        content += '\n<h3>' + text(topic['related_heading']) + '</h3>\n'
        for reference in topic['related_work']:
            entry = dict(publications[reference['id']])
            entry.update(reference.get('overrides', {}))
            content += citation(entry) + '\n'
        sections.append(section(topic['title'], content.rstrip()))
    return '\n\n'.join(sections)


def build():
    site, home, research, publications = (load(name) for name in ('site', 'home', 'research', 'publications'))
    template = Template((ROOT / 'templates/page.html').read_text(encoding='utf-8'))
    styles = (ROOT / 'templates/styles.css').read_text(encoding='utf-8')
    research_styles = (ROOT / 'templates/research.css').read_text(encoding='utf-8')
    contents = (render_home(home), render_research(research, publications['entries']), render_publications(publications))
    return {name: template.substitute(
        title=text(site['title']), heading=text(site['heading']),
        navigation=' '.join(link(item).replace('<a ', '<a aria-current="page" ', 1)
                            if item['href'] == './' + name else link(item)
                            for item in site['navigation']),
        styles=styles + (research_styles if name == 'research.html' else ''), content=content)
        for name, content in zip(PAGES, contents)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if committed HTML differs from generated output')
    args = parser.parse_args()
    try:
        pages = build()  # Validate every page before writing any output.
        stale = []
        for name, content in pages.items():
            path = ROOT / name
            if args.check:
                if not path.exists() or path.read_text(encoding='utf-8') != content:
                    stale.append(name)
            else:
                path.write_text(content, encoding='utf-8')
        if stale:
            parser.exit(1, 'Outdated HTML: ' + ', '.join(stale) + '\nRun python3 scripts/build.py\n')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Build failed: {error}\n')
    print('Generated HTML is up to date.' if args.check else 'Generated ' + ', '.join(pages))


if __name__ == '__main__':
    main()
