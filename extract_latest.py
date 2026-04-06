import re, json, sys

with open(r'C:\Users\tjqud\Desktop\TRACKING\Weekly_Tracking\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

def extract_js_object(html, var_name):
    """Extract a JS object by brace-counting."""
    marker = f'const {var_name} = ' + '{'
    start = html.find(marker)
    if start == -1:
        # try without space around =
        marker = f'const {var_name}=' + '{'
        start = html.find(marker)
    if start == -1:
        return None

    brace_start = html.index('{', start)
    depth = 0
    i = brace_start
    while i < len(html):
        if html[i] == '{':
            depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                return html[brace_start:i+1]
        i += 1
    return None

# Extract DATA
data_str = extract_js_object(html, 'DATA')
# Extract AMZN
amzn_str = extract_js_object(html, 'AMZN')

# JS object -> JSON: need to handle unquoted keys and trailing commas
def js_to_json(s):
    # Replace single quotes with double quotes (if any)
    # Actually, looking at the data it seems already JSON-compatible with double quotes
    # But JS allows unquoted keys - let's handle that
    # Also handle trailing commas

    # Remove trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)

    # The data appears to use double-quoted keys already based on the preview
    return s

DATA = None
AMZN = None

if data_str:
    try:
        DATA = json.loads(js_to_json(data_str))
    except json.JSONDecodeError as e:
        print(f"JSON parse error for DATA: {e}", file=sys.stderr)
        # Try to show where it fails
        print(f"Error at position {e.pos}, around: ...{data_str[max(0,e.pos-50):e.pos+50]}...", file=sys.stderr)

if amzn_str:
    try:
        AMZN = json.loads(js_to_json(amzn_str))
    except json.JSONDecodeError as e:
        print(f"JSON parse error for AMZN: {e}", file=sys.stderr)

output = {}

# ===== WEEKLY DATES from Spotify =====
if DATA and 'spotify' in DATA:
    dates = sorted(DATA['spotify'].keys())
    output['weekly_dates_count'] = len(dates)
    output['latest_2_dates'] = dates[-2:]

    latest = dates[-1]
    prev = dates[-2]

    # Spotify latest
    latest_spotify = DATA['spotify'][latest]
    prev_spotify = DATA['spotify'][prev]

    # Sort by value
    sp_items = []
    for artist, info in latest_spotify.items():
        prev_val = prev_spotify.get(artist, {}).get('value', None)
        delta = info['value'] - prev_val if prev_val else None
        sp_items.append({
            'artist': artist,
            'value': info['value'],
            'wow': info.get('wow', 0),
            'delta': round(delta, 1) if delta is not None else None
        })

    sp_items.sort(key=lambda x: x['value'], reverse=True)
    output['spotify'] = {
        'latest_date': latest,
        'prev_date': prev,
        'top15_by_listeners': sp_items[:15],
        'top10_by_wow_growth': sorted([x for x in sp_items if x['wow'] and x['wow'] > 0], key=lambda x: x['wow'], reverse=True)[:10],
        'top5_by_wow_decline': sorted([x for x in sp_items if x['wow'] and x['wow'] < 0], key=lambda x: x['wow'])[:5],
        'top10_by_delta': sorted([x for x in sp_items if x['delta'] is not None], key=lambda x: x['delta'], reverse=True)[:10]
    }

# ===== TIKTOK =====
if DATA and 'tiktok_videos' in DATA:
    output['tiktok'] = {}
    for cat, cat_data in DATA['tiktok_videos'].items():
        dates = sorted(cat_data.keys())
        latest = dates[-1]
        prev = dates[-2] if len(dates) > 1 else None

        latest_entries = cat_data[latest]
        items = []
        for tag, info in latest_entries.items():
            prev_val = cat_data.get(prev, {}).get(tag, {}).get('value', None) if prev else None
            delta = info['value'] - prev_val if prev_val is not None else None
            items.append({
                'tag': tag,
                'value': info['value'],
                'wow': info.get('wow', 0),
                'delta': round(delta, 1) if delta is not None else None
            })

        top_val = sorted(items, key=lambda x: x['value'], reverse=True)[:10]
        top_delta = sorted([x for x in items if x['delta'] is not None], key=lambda x: x['delta'], reverse=True)[:10]
        top_wow = sorted([x for x in items if x['wow'] and x['wow'] > 0], key=lambda x: x['wow'], reverse=True)[:10]
        bottom_wow = sorted([x for x in items if x['wow'] and x['wow'] < 0], key=lambda x: x['wow'])[:5]

        output['tiktok'][cat] = {
            'latest_date': latest,
            'prev_date': prev,
            'total_tags': len(items),
            'top10_by_value': top_val,
            'top10_by_delta': top_delta,
            'top10_by_wow_growth': top_wow,
            'bottom5_by_wow_decline': bottom_wow
        }

# ===== DELTA WEEKLY =====
if DATA and 'delta_weekly' in DATA:
    dates = sorted(DATA['delta_weekly'].keys())
    latest = dates[-1]
    prev = dates[-2] if len(dates) > 1 else None
    output['delta_weekly'] = {
        'latest_date': latest,
        'prev_date': prev,
        'latest_data': DATA['delta_weekly'][latest],
    }
    if prev:
        output['delta_weekly']['prev_data'] = DATA['delta_weekly'][prev]

# ===== AMAZON =====
if AMZN:
    output['amazon'] = {}
    for brand, brand_data in AMZN.items():
        if isinstance(brand_data, dict):
            keys = sorted(brand_data.keys())
            if keys:
                latest_key = keys[-1]
                prev_key = keys[-2] if len(keys) > 1 else None
                output['amazon'][brand] = {
                    'total_entries': len(keys),
                    'latest_key': latest_key,
                    'latest_data': brand_data[latest_key],
                }
                if prev_key:
                    output['amazon'][brand]['prev_key'] = prev_key
                    output['amazon'][brand]['prev_data'] = brand_data[prev_key]

print(json.dumps(output, ensure_ascii=False, indent=2))
