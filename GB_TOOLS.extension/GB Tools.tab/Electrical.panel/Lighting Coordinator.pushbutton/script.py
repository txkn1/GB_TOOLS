from pyrevit import revit, DB, forms, script

doc = revit.doc
output = script.get_output()

# Find loaded Revit links
links = list(
    DB.FilteredElementCollector(doc)
    .OfClass(DB.RevitLinkInstance)
)

loaded_links = []

for link in links:
    link_doc = link.GetLinkDocument()
    if link_doc:
        loaded_links.append((link.Name, link, link_doc))

if not loaded_links:
    forms.alert(
        "No loaded Revit links were found.",
        title="Lighting Coordinator"
    )
    script.exit()

# Let user choose the linked model
link_names = sorted([item[0] for item in loaded_links])

selected_name = forms.SelectFromList.show(
    link_names,
    title="Select Architectural Link",
    button_name="Scan Lighting Fixtures",
    multiselect=False
)

if not selected_name:
    script.exit()

selected_link = None
selected_link_doc = None

for name, link, link_doc in loaded_links:
    if name == selected_name:
        selected_link = link
        selected_link_doc = link_doc
        break

# Collect lighting fixture instances from the linked model
fixtures = list(
    DB.FilteredElementCollector(selected_link_doc)
    .OfCategory(DB.BuiltInCategory.OST_LightingFixtures)
    .WhereElementIsNotElementType()
)

if not fixtures:
    forms.alert(
        "No Lighting Fixture instances were found in the selected link.",
        title="Lighting Coordinator"
    )
    script.exit()

# Group by Family + Type
fixture_groups = {}

for fixture in fixtures:
    try:
        symbol = fixture.Symbol
        family_name = symbol.Family.Name
        type_name = symbol.Name
    except:
        family_name = "<Unknown Family>"
        type_name = "<Unknown Type>"

    key = (family_name, type_name)

    if key not in fixture_groups:
        fixture_groups[key] = 0

    fixture_groups[key] += 1

# Build table
rows = []

for key, count in fixture_groups.items():
    family_name, type_name = key
    rows.append([
        family_name,
        type_name,
        count
    ])

rows.sort(key=lambda x: (x[0].lower(), x[1].lower()))

output.print_md("# Lighting Coordinator")
output.print_md("**Linked Model:** {}".format(selected_name))
output.print_md("**Total Lighting Fixtures:** {}".format(len(fixtures)))
output.print_md("**Family / Type Combinations:** {}".format(len(rows)))

output.print_table(
    table_data=rows,
    columns=[
        "Architect Family",
        "Architect Type",
        "Quantity"
    ],
    title="Linked Lighting Fixtures"
)
