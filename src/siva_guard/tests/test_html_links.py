from siva_guard.connectors.html_links import extract_external_links, filter_external_to_host


def test_extract_external_links_basic():
    html = """
    <html>
      <body>
        <a href="https://example.com/a">A</a>
        <a href="/local">Local</a>
        <a href="mailto:test@example.com">Mail</a>
        <a href="javascript:void(0)">JS</a>
      </body>
    </html>
    """
    links = extract_external_links(html, base_url="https://site.com/profile", limit=80)
    assert "https://example.com/a" in links
    assert "https://site.com/local" in links


def test_filter_external_to_host_removes_same_host():
    links = [
        "https://site.com/a",
        "https://other.com/b",
        "https://site.com/c",
    ]
    filtered = filter_external_to_host(links, host="site.com")
    assert "https://other.com/b" in filtered
    assert "https://site.com/a" not in filtered
    assert "https://site.com/c" not in filtered
