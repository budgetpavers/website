from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Product
import json
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def new_product_range(request):
    # Get category from query params
    category_filter = request.GET.get("category", "").strip()

    # Path to your CSV
    csv_path = os.path.join(settings.BASE_DIR, "Mapped_Product_Data.csv")

    # Read CSV instead of Excel
    df = pd.read_csv(csv_path)

    # Debug: see the columns we actually have
    print("CSV Columns:", df.columns.tolist())

    # Filter by category if given
    if category_filter:
        if "category" in df.columns:
            df = df[df["category"].str.strip().str.lower() == category_filter.lower()]
        else:
            print("⚠ No 'category' column found in CSV — skipping filter")

    # Convert to list of dicts for the template
    products = df.to_dict(orient="records")

    context = {
        "products": products,
        "current_category": category_filter,
    }

    return render(request, "our_range.html", context)


import pandas as pd
import os
from collections import defaultdict


def build_working_groups():
    """Dynamically builds product groups by reading directly from the Excel price lists in D:\Desktop\wall_quote"""

    base_dir = r"D:\Desktop\wall_quote"

    files = {
        "Concrete Sleepers - Silvercrete": "SC Sleepers Pricelist.xlsx",
        "Concrete Sleepers - Outback": "OS Sleepers Pricelist.xlsx",
        "Under Fence Plinths - Silvercrete": "SC UFP+Cribs Pricelist.xlsx",
        "Under Fence Plinths - Outback": "OS UFP+Cribs Pricelist.xlsx",
        "Accessories": "OS Accessories Pricelist.xlsx",
        "Steel Posts & Hardware": "Steel Pricelist.xlsx"
    }

    groups = {}

    def read_file(file_name):
        path = os.path.join(base_dir, file_name)
        if not os.path.exists(path):
            return pd.DataFrame()
        return pd.read_excel(path)

    # ---------- GALVANISED STEEL ----------
    steel_df = read_file(files["Steel Posts & Hardware"])
    if not steel_df.empty:
        steel_types = ["120UB65 I Beam", "125x65 C Channel", "150UB14 I Beam", "150x75 C Channel"]
        for stype in steel_types:
            matches = steel_df[steel_df["Item (50 Characters) (searchable)"].str.contains(stype, case=False, na=False)]
            if not matches.empty:
                lengths = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'(\d+\.?\d*)m')[0].dropna()))
                groups[stype] = {
                    "name": stype,
                    "category": "galvanised_steel",
                    "config_type": "steel_length_only",
                    "products": matches.to_dict("records"),
                    "available_lengths": lengths,
                    "min_price": float(matches["Sale Price (Excluding GST)"].min())
                }

    # ---------- CONCRETE SLEEPERS ----------
    sleepers_dfs = {
        "Silvercrete": read_file(files["Concrete Sleepers - Silvercrete"]),
        "Outback Sleepers": read_file(files["Concrete Sleepers - Outback"])
    }
    sleeper_colours = ["Plain Grey", "Plain Sandstone", "Plain Charcoal", "Charcoal Stackstone", "Charcoal Rockface",
                       "Sandstone Rockface", "Woodgrain"]

    for colour in sleeper_colours:
        for brand, df in sleepers_dfs.items():
            matches = df[df["Item (50 Characters) (searchable)"].str.contains(colour, case=False, na=False)]
            if not matches.empty:
                lengths = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'(\d+\.\d+|\d+)m')[0].dropna()))
                heights = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'x(\d{2,3})x')[1].dropna()))
                thicknesses = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'x\d{2,3}x(\d{2,3})')[0].dropna()))
                groups[f"{colour} ({brand})"] = {
                    "name": f"{colour} ({brand})",
                    "category": "concrete_sleepers",
                    "config_type": "sleeper_hierarchical",
                    "products": matches.to_dict("records"),
                    "available_lengths": lengths,
                    "available_heights": heights,
                    "available_thicknesses": thicknesses,
                    "min_price": float(matches["Sale Price (Excluding GST)"].min())
                }

    # ---------- CONCRETE UFPs & CRIBS ----------
    ufps_dfs = {
        "Silvercrete": read_file(files["Under Fence Plinths - Silvercrete"]),
        "Outback Sleepers": read_file(files["Under Fence Plinths - Outback"])
    }
    ufp_colours = ["Plain Grey", "Plain Sandstone", "Plain Charcoal", "Charcoal Stackstone"]

    for colour in ufp_colours:
        for brand, df in ufps_dfs.items():
            matches = df[df["Item (50 Characters) (searchable)"].str.contains(colour, case=False, na=False)]
            if not matches.empty:
                lengths = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'(\d+\.\d+|\d+)m')[0].dropna()))
                heights = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'x(\d{2,3})x')[1].dropna()))
                thicknesses = sorted(
                    set(matches["Item (50 Characters) (searchable)"].str.extract(r'x\d{2,3}x(\d{2,3})')[0].dropna()))
                groups[f"{colour} UFP ({brand})"] = {
                    "name": f"{colour} UFP ({brand})",
                    "category": "concrete_ufp_cribs",
                    "config_type": "ufp_hierarchical",
                    "products": matches.to_dict("records"),
                    "available_lengths": lengths,
                    "available_heights": heights,
                    "available_thicknesses": thicknesses,
                    "min_price": float(matches["Sale Price (Excluding GST)"].min())
                }

    # ---------- STEP KITS ----------
    accessories_df = read_file(files["Accessories"])
    stepkit_types = ["Step Kits Wide Opening", "Step Kit Tread"]
    for stype in stepkit_types:
        matches = accessories_df[
            accessories_df["Item (50 Characters) (searchable)"].str.contains(stype, case=False, na=False)]
        if not matches.empty:
            colours = sorted(set(matches["Item (50 Characters) (searchable)"].str.extract(
                r'(\bPlain Grey|\bPlain Charcoal|\bPlain Sandstone|\bCharcoal Stackstone|\bCharcoal Rockface|\bSandstone Rockface|\bWoodgrain)')[
                                     0].dropna()))
            sizes = sorted(
                set(matches["Item (50 Characters) (searchable)"].str.extract(r'(\d+\.\d+|\d+)m')[0].dropna()))
            groups[stype] = {
                "name": stype,
                "category": "step_kits",
                "config_type": "stepkit_dropdown",
                "products": matches.to_dict("records"),
                "available_colours": colours,
                "available_sizes": sizes,
                "min_price": float(matches["Sale Price (Excluding GST)"].min())
            }

    # ---------- ACCESSORIES ----------
    for _, row in accessories_df.iterrows():
        pname = row["Item (50 Characters) (searchable)"]
        groups[pname] = {
            "name": pname,
            "category": "accessories",
            "config_type": "simple_accessory",
            "products": [row.to_dict()],
            "min_price": float(row["Sale Price (Excluding GST)"])
        }

    return groups


def get_brands_from_products(products):
    """Extract brands from products"""
    brands = set()
    for product in products:
        if 'silvercrete' in product.category.lower():
            brands.add('Silvercrete')
        elif 'outback' in product.category.lower():
            brands.add('Outback Sleepers')
    return sorted(list(brands))


def extract_lengths_from_products(products):
    """Extract lengths from steel product names"""
    import re
    lengths = set()
    for product in products:
        name = product.name.lower()
        match = re.search(r'(\d+)mm', name)
        if match:
            mm = int(match.group(1))
            if mm >= 1000:
                lengths.add(f"{mm / 1000:.1f}m")
            else:
                lengths.add(f"{mm}mm")
    return sorted(list(lengths))


@require_POST
def get_ufp_options(request):
    """Get UFP dropdown options based on brand selection"""
    try:
        data = json.loads(request.body)
        group_name = data.get('group_name')
        brand = data.get('brand')

        print(f"🔍 Getting UFP options for {group_name}, brand: {brand}")

        plinth_products = Product.objects.filter(category__icontains='Plinth', is_active=True)

        if 'Plain Grey' in group_name:
            products = plinth_products.filter(name__icontains='[GREY]')
        elif 'Plain Charcoal' in group_name:
            products = plinth_products.filter(name__icontains='[CHAR]').exclude(name__icontains='stackstone')
        elif 'Plain Sandstone' in group_name:
            products = plinth_products.filter(name__icontains='[SAND]')
        elif 'Charcoal Stackstone' in group_name:
            products = plinth_products.filter(Q(name__icontains='stackstone') & Q(name__icontains='[CHAR]'))
        else:
            products = plinth_products.none()

        if brand == 'Silvercrete':
            products = products.filter(category__icontains='Silvercrete')
        elif brand == 'Outback Sleepers':
            products = products.filter(category__icontains='Outback')

        options = extract_ufp_options(products, brand)

        return JsonResponse({
            'success': True,
            'options': options,
            'products_found': products.count()
        })

    except Exception as e:
        print(f"❌ Error getting UFP options: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def find_ufp_product(request):
    """Find exact UFP product based on selections"""
    try:
        data = json.loads(request.body)
        group_name = data.get('group_name')
        brand = data.get('brand')
        length = data.get('length')
        height = data.get('height')
        thickness = data.get('thickness')

        print(f"🔍 Finding UFP: {group_name}, {brand}, {length}x{height}x{thickness}")

        products = Product.objects.filter(category__icontains='Plinth', is_active=True)

        if brand == 'Silvercrete':
            products = products.filter(category__icontains='Silvercrete')
        elif brand == 'Outback Sleepers':
            products = products.filter(category__icontains='Outback')

        if 'Plain Grey' in group_name:
            products = products.filter(name__icontains='[GREY]')
        elif 'Plain Charcoal' in group_name:
            products = products.filter(name__icontains='[CHAR]').exclude(name__icontains='stackstone')
        elif 'Plain Sandstone' in group_name:
            products = products.filter(name__icontains='[SAND]')
        elif 'Charcoal Stackstone' in group_name:
            products = products.filter(Q(name__icontains='stackstone') & Q(name__icontains='[CHAR]'))

        length_mm = str(int(float(length.replace('m', '')) * 1000))
        height_num = height.replace('mm', '')
        thickness_num = thickness.replace('mm', '')

        dimension_pattern = f"{length_mm}x{height_num}x{thickness_num}"
        matching = products.filter(name__icontains=dimension_pattern)

        if matching.exists():
            product = matching.first()
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': f"{float(product.price):.2f}",
                    'sku': product.sku or '',
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'No UFP found for {dimension_pattern}'
            })

    except Exception as e:
        print(f"❌ Error finding UFP: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def extract_ufp_options(products, brand):
    """Extract available UFP options from products"""
    import re
    options = {
        'lengths': set(),
        'heights': set(),
        'thicknesses': set()
    }

    for product in products:
        name = product.name
        match = re.search(r'(\d{4})x(\d{2,3})x(\d{2,3})', name)
        if match:
            length_mm = int(match.group(1))
            height_mm = int(match.group(2))
            thickness_mm = int(match.group(3))
            options['lengths'].add(f"{length_mm / 1000:.3f}m".rstrip('0').rstrip('.') + 'm')
            options['heights'].add(f"{height_mm}mm")
            options['thicknesses'].add(f"{thickness_mm}mm")

    for key in options:
        options[key] = sorted(list(options[key]))

    if brand == 'Outback Sleepers':
        options['rebated_options'] = ['Yes', 'No']
    elif brand == 'Silvercrete':
        options['finish_options'] = ['One-sided', 'Double-sided']

    return options


def determine_accessory_group_name(product):
    """Determine accessory group name"""
    name_lower = product.name.lower()

    if 'chemical anchor glue' in name_lower:
        return "Step Kit Chemical Anchor Glue"
    elif 'wheel stops' in name_lower and '1650' in name_lower:
        return "Wheel Stops"
    elif 'ag pipe' in name_lower:
        return "Ag Pipe - Slotted Sock"
    elif 'step kit brackets' in name_lower:
        return "Step Kit Brackets"
    elif 'fence bracket' in name_lower:
        return "Fence Brackets"
    elif 'wheel stop fixings' in name_lower:
        return "Wheel Stop Fixings"

    return None


def get_accessory_config_type(group_name):
    """Get config type for accessories"""
    if "Fence Brackets" in group_name:
        return "fence_bracket_dropdown"
    elif "Wheel Stop Fixings" in group_name:
        return "wheel_stop_fixings_dropdown"
    else:
        return "simple_accessory"
