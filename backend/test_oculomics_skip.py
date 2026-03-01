import os
from backend.oculomics.inference import get_ocular_api, Config

print("Testing Inference Skip on Missing Models...")

# Look for an image in the artifacts folder as a tester, or create a dummy black image
test_img_path = "dummy_test.jpg"
from PIL import Image
Image.new('RGB', (224, 224), color = 'black').save(test_img_path)

api = get_ocular_api()
results = api.run_full_profile(test_img_path)

print("INFERENCE RESULTS:")
print(results)
os.remove(test_img_path)
