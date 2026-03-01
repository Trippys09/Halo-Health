import os
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms

# HuggingFace & GradCAM imports
from transformers import ViTModel
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

class Config:
    # Use absolute local artifacts directory for checkpoints and CAM output
    ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
    OUTPUT_DIR = ARTIFACTS_DIR
    CHECKPOINT_DIR = ARTIFACTS_DIR
    # Local path for heatmap generation to avoid read-only restrictions
    CAM_DIR = ARTIFACTS_DIR / "gradcam_inference"
    
    IMG_SIZE = 224
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Task Definitions: {TaskName: (Type, Num_Classes/Output_Dim, Column_Name)}
    TASKS = {
        'Age': ('regression', 1, 'age'),
        'Gender': ('binary', 2, 'sex'),
        'Diabetes': ('binary', 2, 'diabetes'), 
        'ICDR': ('multiclass', 5, 'final_icdr'),
        'Edema': ('binary', 2, 'final_edema'),
        'Hypertension': ('binary', 2, 'systemic_hypertension'),
        'Cardiovascular_Risk': ('binary', 2, 'vascular_disease'),
        'AMI': ('binary', 2, 'acute_myocardial_infarction'),
        'Neuropathy': ('binary', 2, 'neuropathy'),
        'Nephropathy': ('binary', 2, 'nephropathy')
    }

Config.CAM_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. MODEL ARCHITECTURE (Required for loading weights)
# ==============================================================================

class FoundationalCVModel(nn.Module):
    def __init__(self, backbone='vit_base', mode='eval', weights=None):
        super(FoundationalCVModel, self).__init__()
        self.backbone_name = backbone
        
        if backbone == 'vit_base':
            self.backbone = ViTModel.from_pretrained("google/vit-base-patch16-224-in21k")
        else:
            raise ValueError(f"This inference script is configured for 'vit_base'. Got {backbone}")
            
        self.mode = mode
        self.eval()

    def forward(self, x):
        features = self.backbone(x)
        return features['pooler_output']

class FoundationalCVModelWithClassifier(nn.Module):
    def __init__(self, backbone, hidden, num_classes):
        super(FoundationalCVModelWithClassifier, self).__init__()
        self.backbone = backbone
        self.hidden = hidden
        
        # Calculate backbone output dim
        sample_input = torch.randn(1, 3, 224, 224)
        self.backbone.eval()
        with torch.no_grad():
            output_dim = self.backbone(sample_input).shape[1]
        
        layers = []
        if isinstance(hidden, int):
            layers.append(nn.Linear(output_dim, hidden))
            output_dim = hidden
        elif isinstance(hidden, list):
            for h in hidden:
                layers.append(nn.Linear(output_dim, h))
                output_dim = h
        
        if hidden:
            self.hidden_layers = nn.Sequential(*layers)
        else:
            self.norm = nn.BatchNorm1d(output_dim)

        self.classifier = nn.Linear(output_dim, num_classes)
        self.eval()

    def forward(self, x):
        features = self.backbone(x)
        if self.hidden: features = self.hidden_layers(features)
        else: features = self.norm(features)
        return self.classifier(features)

# ==============================================================================
# 3. GRADCAM UTIL FOR ViT
# ==============================================================================

def reshape_transform_vit(tensor, height=14, width=14):
    """Reshapes the ViT output [B, 197, 768] -> [B, 768, 14, 14] excluding CLS token."""
    result = tensor[:, 1:, :].reshape(tensor.size(0), height, width, tensor.size(2))
    result = result.transpose(2, 3).transpose(1, 2)
    return result

# ==============================================================================
# 4. INFERENCE API CLASS
# ==============================================================================

class OcularInferenceAPI:
    def __init__(self, checkpoint_dir=Config.CHECKPOINT_DIR):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.device = Config.DEVICE
        self.tfms = transforms.Compose([
            transforms.Resize((Config.IMG_SIZE, Config.IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Model Cache Dictionary
        self.models_cache = {}
        print(f"✅ OcularInferenceAPI initialized. Using device: {self.device.upper()}")

    def load_model(self, task_name):
        """
        Lazy load models into memory. If it's already in the cache, return it immediately.
        """
        if task_name in self.models_cache:
            return self.models_cache[task_name]
            
        task_info = Config.TASKS.get(task_name)
        if not task_info:
            raise ValueError(f"Unknown task: {task_name}")
            
        _, num_classes, _ = task_info
        
        print(f"[*] ⏳ Cache miss for '{task_name}'. Loading model into memory...")
        base_vit = FoundationalCVModel(backbone='vit_base', mode='eval')
        model = FoundationalCVModelWithClassifier(
            backbone=base_vit, hidden=256, num_classes=num_classes
        ).to(self.device)
        
        ckpt_path = self.checkpoint_dir / f"best_model_{task_name}.pth"
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Model checkpoint missing for {task_name} at {ckpt_path}. Have you trained it yet?")
            
        model.load_state_dict(torch.load(ckpt_path, map_location=self.device))
        model.eval()
        
        # Cache it
        self.models_cache[task_name] = model
        print(f"[*] ✅ Successfully loaded and cached weights for '{task_name}'.")
        return model

    def preload_all_models(self):
        """Optional: Load all models into RAM/VRAM at once."""
        print(f"\n🚀 Pre-loading all {len(Config.TASKS)} models into memory...")
        for task in Config.TASKS.keys():
            try:
                self.load_model(task)
            except Exception as e:
                print(f"⚠️ Failed to preload {task}: {e}")
        print("🚀 Pre-loading complete.\n")

    def predict_and_explain(self, img_path, task_name):
        """
        Runs inference and generates a GradCAM++ attention map for a single task.
        """
        model = self.load_model(task_name)
        task_type, num_classes, _ = Config.TASKS[task_name]

        # 1. Load Image
        orig_img = Image.open(img_path).convert('RGB')
        orig_img_resized = np.array(orig_img.resize((Config.IMG_SIZE, Config.IMG_SIZE))) / 255.0
        input_tensor = self.tfms(orig_img).unsqueeze(0).to(self.device)

        # 2. Inference
        with torch.no_grad():
            preds = model(input_tensor)
            
        if task_type == 'regression':
            pred_val = preds.item()
            prediction_text = f"Predicted {task_name}: {pred_val:.2f}"
            target_class_idx = 0
            final_result = pred_val
        else:
            probs = F.softmax(preds, dim=1).cpu().numpy()[0]
            pred_cls = int(np.argmax(probs))
            pred_prob = float(probs[pred_cls])
            prediction_text = f"Predicted {task_name}: Class {pred_cls} (Prob: {pred_prob:.2f})"
            target_class_idx = pred_cls
            final_result = {'class': pred_cls, 'probability': pred_prob}

        print(f"  -> 🔍 {prediction_text}")

        # 3. GradCAM++ for ViT
        target_layers = [model.backbone.backbone.encoder.layer[-1].layernorm_before]
        
        cam = GradCAMPlusPlus(
            model=model, 
            target_layers=target_layers, 
            reshape_transform=reshape_transform_vit
        )
        
        targets = [ClassifierOutputTarget(target_class_idx)] if task_type != 'regression' else None
        
        grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
        grayscale_cam = grayscale_cam[0, :]
        
        # 4. Overlay & Display
        visualization = show_cam_on_image(orig_img_resized, grayscale_cam, use_rgb=True)
        
        plt.figure(figsize=(6, 6))
        plt.imshow(visualization)
        plt.title(f"GradCAM++ ({prediction_text})")
        plt.axis('off')
        
        img_filename = Path(img_path).stem
        save_path = Config.CAM_DIR / f"{img_filename}_{task_name}_cam.png"
        plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1)
        plt.close()
        
        print(f"  -> 📸 GradCAM++ Heatmap saved at: {save_path}")
        return final_result, str(save_path)

    def run_full_profile(self, img_path):
        """
        Runs all available tasks on a single image.
        Returns a dictionary of predictions and paths to their attention maps.
        """
        print(f"\n{'='*60}")
        print(f"🩺 RUNNING FULL PATIENT PROFILE FOR: {Path(img_path).name}")
        print(f"{'='*60}")
        
        results = {}
        for task in Config.TASKS.keys():
            try:
                pred, map_path = self.predict_and_explain(img_path, task)
                results[task] = {
                    'prediction': pred,
                    'attention_map': map_path
                }
            except FileNotFoundError:
                print(f"  -> ⚠️ Skipping {task} (Model weights not found).")
            except Exception as e:
                print(f"  -> ❌ Error running {task}: {e}")
                
        print(f"\n✅ Full profile complete for {Path(img_path).name}.")
        return results

# ==============================================================================
# 5. EXECUTION EXAMPLE
# ==============================================================================

_api_instance = None

def get_ocular_api():
    global _api_instance
    if _api_instance is None:
        try:
            _api_instance = OcularInferenceAPI()
        except Exception as e:
            print(f"Failed to initialize OcularInferenceAPI: {e}")
            return None
    return _api_instance

if __name__ == "__main__":
    # Initialize the API
    api = OcularInferenceAPI()
    
    # Define a test image path (Replace this with a real image path from your dataset)
    TEST_IMAGE_PATH = "/data/users4/nshaik3/Datasets/mBRSET/physionet.org/files/mbrset/1.0/images/000000.jpg"
    
    # Check if image exists before running
    if Path(TEST_IMAGE_PATH).exists():
        # Option 1: Run a single task
        print("\n--- Testing Single Task ---")
        api.predict_and_explain(TEST_IMAGE_PATH, task_name="ICDR")
        
        # Option 2: Run all tasks (Generates a full diagnostic profile)
        print("\n--- Testing Full Profile ---")
        full_results = api.run_full_profile(TEST_IMAGE_PATH)
        
        print("\n📊 Summary of Results:")
        for task, data in full_results.items():
            print(f" - {task}: {data['prediction']}")
    else:
        print(f"\n⚠️ Test image not found at {TEST_IMAGE_PATH}.")
        print("Please update 'TEST_IMAGE_PATH' in the script to a valid image path to test the API.")
