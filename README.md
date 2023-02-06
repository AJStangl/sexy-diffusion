# Template


```env
VISION_DECODER_MODEL="/models/image-caption-generator"
GPT2_FAST_TOKENIZER="/models/image-caption-generator/tokenizer"
AZURE_STORAGE_CONNECTION_STRING=""
OUT_PATH="/workspaces/General/scripts/images"
IMAGE_TRAINING_TABLE="training"
LOCAL_TRAINING_IMAGES="/workspaces/General/scripts/training"
```

Local Build:
```
python setup.py build
pip install --editable .
```

Git Build:
```
pip install
```