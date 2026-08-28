import random

# Read the original file
with open("data/private_comps.py", "r") as f:
    content = f.read()

# Generate the 500 rows array as a string
from generate_500_comps import output

array_str = "COMP_UNIVERSE: List[PublicComp] = [\n"
for row in output:
    array_str += f'    PublicComp("{row[0]}", "{row[1]}", "{row[2]}", "{row[3]}", {row[4]}, {row[5]}, {row[6]}, {row[7]}, {row[8]}),\n'
array_str += "]\n"

parts = content.split("def find_comparable_companies")
header = parts[0][:parts[0].find("COMP_UNIVERSE: List[PublicComp] = [")]
footer = "\ndef find_comparable_companies" + parts[1]

with open("data/private_comps.py", "w") as f:
    f.write(header)
    f.write(array_str)
    f.write(footer)

print("Updated private_comps.py successfully with footer included.")
