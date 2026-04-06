import re, json, sys

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

# For Amazon, get the brand-level totals (last vs second-to-last array element)
if AMZN:
    print("=" * 70)
    print("AMAZON (AMZN) - Latest week vs Previous week (last 2 array elements)")
    print("=" * 70)
    for brand, bdata in AMZN.items():
        if not isinstance(bdata, dict):
            continue
        if 'total' in bdata and isinstance(bdata['total'], list) and len(bdata['total']) >= 2:
            arr = bdata['total']
            latest = arr[-1]
            prev = arr[-2]
            wow = (latest - prev) / prev * 100 if prev != 0 else 0
            print(f"  {brand}: latest=${latest:,.0f}  prev=${prev:,.0f}  WoW={wow:+.1f}%")

    # Also show product-level for brands that have 'products'
    for brand, bdata in AMZN.items():
        if not isinstance(bdata, dict):
            continue
        if 'products' in bdata and isinstance(bdata['products'], dict):
            print(f"\n  [{brand}] Product breakdown (latest week):")
            for prod, pdata in bdata['products'].items():
                if isinstance(pdata, dict) and 'qty' in pdata:
                    qty_arr = pdata['qty']
                    price_arr = pdata.get('price', [])
                    if len(qty_arr) >= 2:
                        q_latest = qty_arr[-1]
                        q_prev = qty_arr[-2]
                        p_latest = price_arr[-1] if price_arr else 'N/A'
                        print(f"    {prod}: qty={q_latest} (prev={q_prev}), price=${p_latest}")

print()
