from pathlib import Path
p = Path('/app/backend/open_webui/routers/retrieval.py')
s = p.read_text()
old = 'log.debug("web search queries: %s", getattr(form_data, \'queries\', None))'
if old in s:
    s = s.replace('log.debug("web search queries: %s", getattr(form_data, \'queries\', None))', 'log.error("WEBSEARCH DEBUG: web search queries: %s", getattr(form_data, \'queries\', None))')
    s = s.replace('log.debug("search_results raw type: %s", type(search_results))', 'log.error("WEBSEARCH DEBUG: search_results raw type: %s", type(search_results))')
    s = s.replace('log.debug("  query[%d] results_count: %s", i, count)', 'log.error("WEBSEARCH DEBUG:   query[%d] results_count: %s", i, count)')
    s = s.replace('log.debug("    first item link/title: %s | %s", getattr(first, \'link\', None), getattr(first, \'title\', None))', 'log.error("WEBSEARCH DEBUG:     first item link/title: %s | %s", getattr(first, \'link\', None), getattr(first, \'title\', None))')
    s = s.replace('log.debug("    first item inspect error: %s", e)', 'log.error("WEBSEARCH DEBUG:     first item inspect error: %s", e)')
    p.write_text(s)
    print('promoted')
else:
    print('marker not found')
