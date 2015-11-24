This a Python library for using https://datamarket.azure.com/dataset/amla/recommendations more conveniently.

# How to Install: 
	pip install git+git://github.com/crwilcox/CortanaAnalytics.git

# Samples

## Recommendations

```python

from cortanaanalytics.recommendations import Recommendations

email = 'email@outlook.com'
key = '1abCdEFGh/ijKlmN/opq234r56st/UvWXYZabCD7EF8='
rs = Recommendations(email, key)

# create model
model_id = rs.create_model('groceries' + datetime.now().strftime('%Y%m%d%H%M%S'))

# import item catalog
catalog_path = os.path.join('app', 'management', 'commands', 'catalog.csv')
rs.import_file(model_id, catalog_path, Uris.import_catalog)

# import usage information
transactions_path = os.path.join('app', 'management', 'commands', 'transactions.csv')
rs.import_file(model_id, transactions_path, Uris.import_usage)

# build model
build_id = rs.build_fbt_model(model_id)
status = rs.wait_for_build(model_id, build_id)

if status != BuildStatus.success:
    print('Unsuccessful in building the model, failing now.')
    return

# update model active build (not needed unless you are rebuilding)
rs.update_model(model_id, None, build_id)

print('Built a model. Model ID:{} Build ID:{}'.format(model_id, build_id))
```
