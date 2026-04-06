import re, json, sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\tjqud\Desktop\TRACKING\Weekly_Tracking\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

def extract_js_object(html, var_name):
    marker = f'const {var_name} = ' + '{'
    start = html.find(marker)
    if start == -1:
        return None
    brace_start = html.index('{', start)
    depth = 0
    i = brace_start
    while i < len(html):
        if html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                return html[brace_start:i+1]
        i += 1
    return None

def js_to_json(s):
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return s

data_str = extract_js_object(html, 'DATA')
amzn_str = extract_js_object(html, 'AMZN')

DATA = json.loads(js_to_json(data_str)) if data_str else None
AMZN = json.loads(js_to_json(amzn_str)) if amzn_str else None

print("=" * 70)
print("WEEKLY TRACKING DASHBOARD - Latest Data Summary")
print("=" * 70)

# WEEKLY DATES
if DATA and 'spotify' in DATA:
    dates = sorted(DATA['spotify'].keys())
    print(f"\nTotal weeks tracked: {len(dates)}")
    print(f"Date range: {dates[0]} ~ {dates[-1]}")
    print(f"Latest 2 dates: {dates[-2]} and {dates[-1]}")

# ===================== SPOTIFY =====================
if DATA and 'spotify' in DATA:
    dates = sorted(DATA['spotify'].keys())
    latest = dates[-1]
    prev = dates[-2]
    print(f"\n{'='*70}")
    print(f"SPOTIFY (date: {latest} vs {prev})")
    print(f"{'='*70}")

    sp = DATA['spotify'][latest]
    sp_prev = DATA['spotify'][prev]

    items = []
    for artist, info in sp.items():
        pv = sp_prev.get(artist, {}).get('value', None)
        delta = info['value'] - pv if pv else None
        items.append({
            'artist': artist,
            'value': info['value'],
            'wow': info.get('wow', 0),
            'delta': round(delta, 1) if delta is not None else None
        })

    print("\n[Top 15 by Monthly Listeners (만명)]")
    for i, x in enumerate(sorted(items, key=lambda x: x['value'], reverse=True)[:15], 1):
        wow_str = f"{x['wow']*100:+.2f}%" if x['wow'] else ""
        delta_str = f"delta={x['delta']:+.1f}" if x['delta'] is not None else ""
        print(f"  {i:2}. {x['artist']:<20} {x['value']:>10,.1f}  {wow_str:>8}  {delta_str}")

    print("\n[Top 10 WoW Growth %]")
    growing = sorted([x for x in items if x['wow'] and x['wow'] > 0], key=lambda x: x['wow'], reverse=True)[:10]
    for i, x in enumerate(growing, 1):
        print(f"  {i:2}. {x['artist']:<20} {x['value']:>10,.1f}  WoW={x['wow']*100:+.2f}%  delta={x['delta']:+.1f}")

    print("\n[Top 5 WoW Decline %]")
    declining = sorted([x for x in items if x['wow'] and x['wow'] < 0], key=lambda x: x['wow'])[:5]
    for i, x in enumerate(declining, 1):
        print(f"  {i:2}. {x['artist']:<20} {x['value']:>10,.1f}  WoW={x['wow']*100:+.2f}%  delta={x['delta']:+.1f}")

# ===================== TIKTOK =====================
if DATA and 'tiktok_videos' in DATA:
    for cat in DATA['tiktok_videos']:
        cat_data = DATA['tiktok_videos'][cat]
        dates = sorted(cat_data.keys())
        latest = dates[-1]
        prev = dates[-2] if len(dates) > 1 else None

        print(f"\n{'='*70}")
        print(f"TIKTOK - {cat.upper()} (date: {latest} vs {prev})")
        print(f"{'='*70}")

        entries = cat_data[latest]
        items = []
        for tag, info in entries.items():
            pv = cat_data.get(prev, {}).get(tag, {}).get('value', None) if prev else None
            delta = info['value'] - pv if pv is not None else None
            items.append({
                'tag': tag,
                'value': info['value'],
                'wow': info.get('wow', 0),
                'delta': round(delta, 1) if delta is not None else None
            })

        print(f"  Total tags tracked: {len(items)}")

        print("\n  [Top 10 by Total Views (만회)]")
        for i, x in enumerate(sorted(items, key=lambda x: x['value'], reverse=True)[:10], 1):
            wow_str = f"WoW={x['wow']*100:+.2f}%" if x['wow'] else ""
            delta_str = f"순증={x['delta']:+.1f}" if x['delta'] is not None else ""
            print(f"    {i:2}. {x['tag']:<22} {x['value']:>10,.2f}  {wow_str:>12}  {delta_str}")

        print("\n  [Top 5 by 순증 (absolute increase)]")
        top_delta = sorted([x for x in items if x['delta'] is not None], key=lambda x: x['delta'], reverse=True)[:5]
        for i, x in enumerate(top_delta, 1):
            print(f"    {i:2}. {x['tag']:<22} 순증={x['delta']:+.1f}  (total={x['value']:,.2f}, WoW={x['wow']*100:+.2f}%)")

        print("\n  [Top 5 by WoW Growth %]")
        top_wow = sorted([x for x in items if x['wow'] and x['wow'] > 0], key=lambda x: x['wow'], reverse=True)[:5]
        for i, x in enumerate(top_wow, 1):
            print(f"    {i:2}. {x['tag']:<22} WoW={x['wow']*100:+.2f}%  (total={x['value']:,.2f}, 순증={x['delta']:+.1f})")

# ===================== AMAZON =====================
if AMZN:
    print(f"\n{'='*70}")
    print(f"AMAZON (AMZN) - Latest week vs Previous week")
    print(f"{'='*70}")
    print(f"  Brands: {', '.join(AMZN.keys())}")

    for brand, bdata in AMZN.items():
        if not isinstance(bdata, dict):
            continue
        print(f"\n  --- {brand} ---")
        if 'total' in bdata and isinstance(bdata['total'], list) and len(bdata['total']) >= 2:
            arr = bdata['total']
            latest = arr[-1]
            prev = arr[-2]
            wow = (latest - prev) / prev * 100 if prev != 0 else 0
            print(f"    Total Revenue: ${latest:,.0f} (prev: ${prev:,.0f}, WoW: {wow:+.1f}%)")

        if 'qty' in bdata and isinstance(bdata['qty'], dict):
            print(f"    Qty categories: {list(bdata['qty'].keys())}")
        elif 'qty' in bdata and isinstance(bdata['qty'], list) and len(bdata['qty']) >= 2:
            arr = bdata['qty']
            print(f"    Total Qty: {arr[-1]:,.0f} (prev: {arr[-2]:,.0f})")

        if 'products' in bdata and isinstance(bdata['products'], dict):
            print(f"    Products:")
            for prod, pdata in bdata['products'].items():
                if isinstance(pdata, dict) and 'qty' in pdata:
                    q = pdata['qty']
                    p = pdata.get('price', [])
                    if len(q) >= 2:
                        q_l, q_p = q[-1], q[-2]
                        q_wow = (q_l - q_p) / q_p * 100 if q_p != 0 else float('inf')
                        p_l = p[-1] if p else 'N/A'
                        print(f"      {prod}: qty={q_l:,.0f} (prev={q_p:,.0f}, {q_wow:+.1f}%), price=${p_l}")

print(f"\n{'='*70}")
print("END OF SUMMARY")
print(f"{'='*70}")
