with open('data/edgar.py', 'r') as f:
    content = f.read()

if "import pandas as pd" not in content:
    content = "import pandas as pd\n" + content

with open('data/edgar.py', 'w') as f:
    f.write(content)
