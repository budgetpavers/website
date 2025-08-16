import pandas as pd

# Dictionary to hold mapping of postcode → zone
POSTCODE_TO_ZONE = {}


def load_postcode_zones():
    """
    Loads the Excel file into POSTCODE_TO_ZONE dictionary.
    Expects columns: 'Postcode', 'Zone' (case insensitive).
    """
    global POSTCODE_TO_ZONE
    df = pd.read_excel("SA Postcode Zone List - Latif.xlsx")

    for _, row in df.iterrows():
        postcode = str(row['Postcode']).strip()
        zone = str(row['Zone']).strip().lower()
        POSTCODE_TO_ZONE[postcode] = zone


# Call it once at import time
load_postcode_zones()


def get_zone_for_postcode(postcode):
    """
    Returns the zone for the given postcode.
    Possible values: 'metro', 'outer metro', or None if unknown.
    """
    return POSTCODE_TO_ZONE.get(str(postcode).strip())