with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

import re
import numpy as np

def clean_dict(d):
    return {k: float(v) if isinstance(v, (np.float64, np.float32, np.int64, np.int32)) else v for k, v in d.items()}

# Let's completely rewrite the endpoint file to be sure
