from pathlib import Path
import time
p = Path('/app/backend/open_webui/routers/retrieval.py')
text = p.read_text()
# backup
bak = p.with_suffix(p.suffix + f'.bak_{int(time.time())}')
bak.write_text(text)
old = '\n    if len(urls) == 0:\n        raise HTTPException(\n            status_code=status.HTTP_404_NOT_FOUND,\n            detail=ERROR_MESSAGES.DEFAULT("No results found from web search"),\n        )\n'
if old in text:
    insert = '''\n    # DEBUG ADD: log summary of search_results before returning 404\n    try:\n        log.error("WEBSEARCH DEBUG: web search queries: %s", getattr(form_data, 'queries', None))\n        log.error("WEBSEARCH DEBUG: search_results raw type: %s", type(search_results))\n        for i, res in enumerate(search_results):\n            try:\n                count = len(res) if res is not None and hasattr(res, '__len__') else (0 if res is None else 'iterable')\n            except Exception:\n                count = 'unknown'\n            log.error("WEBSEARCH DEBUG:   query[%d] results_count: %s", i, count)\n            if count and count != 0:\n                try:\n                    first = res[0] if hasattr(res, '__getitem__') else None\n                    if first is not None:\n                        log.error("WEBSEARCH DEBUG:     first item link/title: %s | %s", getattr(first, 'link', None), getattr(first, 'title', None))\n                except Exception as e:\n                    log.error("WEBSEARCH DEBUG:     first item inspect error: %s", e)\n    except Exception as e:\n        log.exception("Error while logging search_results summary: %s", e)\n\n    if len(urls) == 0:\n        raise HTTPException(\n            status_code=status.HTTP_404_NOT_FOUND,\n            detail=ERROR_MESSAGES.DEFAULT("No results found from web search"),\n        )\n'''
    text = text.replace(old, insert)
    p.write_text(text)
    print('patched')
else:
    print('marker not found')
