try:
    import torch
    import transformers
    import pytorch_grad_cam
    import sklearn
    import tqdm
    import seaborn
    import cv2
    import timm
    print("ALL_MODULES_OK")
except ImportError as e:
    print(f"MISSING_MODULE: {e}")
