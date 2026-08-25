import re

with open('api/app.py', 'r') as f:
    content = f.read()

# Add import
import_statement = "from api.routes import portfolio, retail, multi_asset"
new_import = "from api.routes import portfolio, retail, multi_asset, nlp"
content = content.replace(import_statement, new_import)

# Add router
router_statement = "app.include_router(multi_asset.router, prefix=\"/api/v1/risk/multi-asset\", tags=[\"Multi-Asset Risk\"])"
new_router = router_statement + "\napp.include_router(nlp.router, prefix=\"/api/v1/nlp/sentiment\", tags=[\"NLP Sentiment\"])"
content = content.replace(router_statement, new_router)

with open('api/app.py', 'w') as f:
    f.write(content)
