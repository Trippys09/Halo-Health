import os
import cv2
import random
import logging
import numpy as np
import pandas as pd
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
import subprocess

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, mean_absolute_error

# HuggingFace & GradCAM imports
from transformers import ViTModel, CLIPModel, ConvNextV2ForImageClassification
from pytorch_grad_cam import GradCAMPlusPlus
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

# ==============================================================================
# 1. CONFIGURATION & LOGGER SETUP
# ==============================================================================

class Config:
    DATA_DIR = Path("/data/users4/nshaik3/Datasets/mBRSET/physionet.org/files/mbrset/1.0")
    IMG_DIR = DATA_DIR / "images"
    CSV_FILE = DATA_DIR / "labels_mbrset.csv"
    
    OUTPUT_DIR = Path("/data/users3/nshaik3/Projects/CVPR-2026/mBRSET/Experiments/Hacklytics/mBRSET_Individual_Models")
    CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
    RESULTS_DIR = OUTPUT_DIR / "results"
    CAM_DIR = OUTPUT_DIR / "gradcam"
    LOG_FILE = OUTPUT_DIR / "pipeline.log"
    
    IMG_SIZE = 224
    BATCH_SIZE = 32
    EPOCHS = 15  # Adjust as needed per task
    LR = 1e-4
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

# Create output directories
for p in [Config.OUTPUT_DIR, Config.CHECKPOINT_DIR, Config.RESULTS_DIR, Config.CAM_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Set up Logger
def setup_logger(log_file):
    logger = logging.getLogger("mBRSET_Pipeline")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

LOGGER = setup_logger(Config.LOG_FILE)

# ==============================================================================
# 2. PROVIDED BASE MODELS (With ViT Implementation)
# ==============================================================================

class CLIPImageEmbeddings(nn.Module):
    def __init__(self, vision_model, visual_projection):
        super(CLIPImageEmbeddings, self).__init__()
        self.vision_model = vision_model
        self.visual_projection = visual_projection
    def forward(self, images):
        vision_output = self.vision_model(images)['pooler_output']
        return self.visual_projection(vision_output)

class FoundationalCVModel(nn.Module):
    def __init__(self, backbone, mode='eval', weights=None):
        super(FoundationalCVModel, self).__init__()
        self.backbone_name = backbone
        
        if backbone in ['vit_base', 'vit_large']:
            backbone_path = {
                'vit_base': "google/vit-base-patch16-224-in21k",
                'vit_large': 'google/vit-large-patch16-224-in21k',
            }
            self.backbone = ViTModel.from_pretrained(backbone_path[backbone])
        else:
            LOGGER.error(f"Unsupported backbone '{backbone}' requested.")
            raise ValueError(f"This script is configured for 'vit_base'. Got {backbone}")
            
        self.mode = mode
        if mode == 'eval': self.eval()
        elif mode == 'fine_tune': self.train()

    def forward(self, x):
        features = self.backbone(x)
        if self.backbone_name in ['vit_base', 'vit_large']:
            features = features['pooler_output']
        return features

class FoundationalCVModelWithClassifier(nn.Module):
    def __init__(self, backbone, hidden, num_classes, mode='eval', backbone_mode='eval'):
        super(FoundationalCVModelWithClassifier, self).__init__()
        self.backbone = backbone
        self.hidden = hidden
        output_dim = self.calculate_backbone_out()
        
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
        
        self.mode = mode
        if backbone_mode == 'eval': self.backbone.eval()
        elif backbone_mode == 'fine_tune': self.backbone.train()
            
        if mode == 'eval': self.eval()
        elif mode == 'fine_tune': self.train()
            
    def calculate_backbone_out(self):
        sample_input = torch.randn(1, 3, 224, 224)
        self.backbone.eval()
        with torch.no_grad():
            output = self.backbone(sample_input)
        return output.shape[1]

    def forward(self, x):
        features = self.backbone(x)
        if self.hidden: features = self.hidden_layers(features)
        else: features = self.norm(features)
        logits = self.classifier(features)
        return logits

# ==============================================================================
# 3. DATA PREPARATION
# ==============================================================================

class IndividualTaskDataset(Dataset):
    def __init__(self, df, img_dir, task_col, task_type, transform=None):
        self.df = df.reset_index(drop=True)
        self.img_dir = img_dir
        self.task_col = task_col
        self.task_type = task_type
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = row['file']
        img_path = Path(self.img_dir) / img_name
        
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            # Silently handle corrupt images by returning a blank image to avoid breaking dataloader
            image = Image.new('RGB', (Config.IMG_SIZE, Config.IMG_SIZE))

        if self.transform:
            image = self.transform(image)

        label_val = row[self.task_col]
        if self.task_type == 'regression':
            target = torch.tensor([float(label_val)], dtype=torch.float32)
        else:
            target = torch.tensor(int(label_val), dtype=torch.long)

        return image, target

def prepare_data():
    LOGGER.info(f"Loading dataset from {Config.CSV_FILE}")
    print(f"[*] Loading dataset from {Config.CSV_FILE}")
    df = pd.read_csv(Config.CSV_FILE)
    
    # Clean standard columns
    df['age'] = pd.to_numeric(df['age'].astype(str).replace('>= 90', '90'), errors='coerce').fillna(df['age'].mode()[0])
    
    # Create "Diabetes" proxy
    df['dm_time'] = pd.to_numeric(df['dm_time'], errors='coerce').fillna(0)
    df['diabetes'] = (df['dm_time'] > 0).astype(int) 
    
    # Binary cleaning mapping
    def clean_bin(val):
        return 1 if str(val).lower().strip() in ['yes', '1', '1.0', 'true'] else 0

    for col in ['sex', 'final_edema', 'systemic_hypertension', 'vascular_disease', 
                'acute_myocardial_infarction', 'neuropathy', 'nephropathy']:
        if col in df.columns:
            df[col] = df[col].apply(clean_bin)

    df.dropna(subset=['final_icdr'], inplace=True)
    df['final_icdr'] = pd.to_numeric(df['final_icdr'], errors='coerce').fillna(0).astype(int)

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    LOGGER.info(f"Data split completed. Train size: {len(train_df)}, Val size: {len(val_df)}")
    print(f"[*] Data split completed! Train size: {len(train_df)} | Val size: {len(val_df)}\n")
    return train_df, val_df

# ==============================================================================
# 4. TRAINING ENGINE
# ==============================================================================

def train_individual_model(task_name, task_type, num_classes, task_col, train_df, val_df):
    LOGGER.info(f"{'='*50}")
    LOGGER.info(f"Starting Training Pipeline for Task: {task_name.upper()} ({task_type})")
    LOGGER.info(f"{'='*50}")
    
    print(f"\n{'='*60}")
    print(f"🚀 STARTING TRAINING: Task -> {task_name.upper()} | Type -> {task_type}")
    print(f"{'='*60}")
    
    tfms = transforms.Compose([
        transforms.Resize((Config.IMG_SIZE, Config.IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    train_ds = IndividualTaskDataset(train_df, Config.IMG_DIR, task_col, task_type, tfms)
    val_ds = IndividualTaskDataset(val_df, Config.IMG_DIR, task_col, task_type, tfms)
    
    train_loader = DataLoader(train_ds, batch_size=Config.BATCH_SIZE, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=Config.BATCH_SIZE, shuffle=False, num_workers=4)

    LOGGER.info("Initializing ViT backbone and Classifier...")
    print(f"[*] Initializing ViT backbone and Classifier on {Config.DEVICE.upper()}...")
    
    base_vit = FoundationalCVModel(backbone='vit_base', mode='fine_tune')
    model = FoundationalCVModelWithClassifier(
        backbone=base_vit, hidden=256, num_classes=num_classes, mode='fine_tune', backbone_mode='fine_tune'
    ).to(Config.DEVICE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=Config.LR)
    criterion = nn.MSELoss() if task_type == 'regression' else nn.CrossEntropyLoss()
    
    best_val_loss = float('inf')
    best_model_path = Config.CHECKPOINT_DIR / f"best_model_{task_name}.pth"

    for epoch in range(Config.EPOCHS):
        # TRAIN
        model.train()
        train_loss = 0
        for imgs, targets in tqdm(train_loader, desc=f"[{task_name}] Epoch {epoch+1}/{Config.EPOCHS} Train", leave=False):
            imgs, targets = imgs.to(Config.DEVICE), targets.to(Config.DEVICE)
            optimizer.zero_grad()
            preds = model(imgs)
            loss = criterion(preds, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        # VAL
        model.eval()
        val_loss = 0
        all_preds, all_targets = [], []
        
        with torch.no_grad():
            for imgs, targets in tqdm(val_loader, desc=f"[{task_name}] Epoch {epoch+1}/{Config.EPOCHS} Val", leave=False):
                imgs, targets = imgs.to(Config.DEVICE), targets.to(Config.DEVICE)
                preds = model(imgs)
                loss = criterion(preds, targets)
                val_loss += loss.item()
                
                if task_type == 'regression':
                    all_preds.extend(preds.cpu().numpy())
                    all_targets.extend(targets.cpu().numpy())
                else:
                    probs = F.softmax(preds, dim=1)
                    all_preds.extend(probs.cpu().numpy())
                    all_targets.extend(targets.cpu().numpy())

        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        
        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)

        # Calculate Metrics and Log/Print
        if task_type == 'regression':
            mae = mean_absolute_error(all_targets, all_preds)
            metrics_str = f"MAE: {mae:.4f}"
        else:
            pred_cls = np.argmax(all_preds, axis=1)
            acc = accuracy_score(all_targets, pred_cls)
            f1 = f1_score(all_targets, pred_cls, average='macro')
            metrics_str = f"Acc: {acc:.4f} | F1 (Macro): {f1:.4f}"

        epoch_result = f"Epoch {epoch+1:02d}/{Config.EPOCHS} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | {metrics_str}"
        LOGGER.info(epoch_result)
        print(f"  -> {epoch_result}")

        # Save Best Model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_model_path)
            LOGGER.info(f"[*] New best model saved for {task_name} (Val Loss: {best_val_loss:.4f})")
            print(f"     ✅ Saved New Best Model! (Val Loss: {best_val_loss:.4f})")
            
    LOGGER.info(f"Finished training for {task_name}.\n")
    print(f"🎉 Finished training for task: {task_name}.\n")

# ==============================================================================
# 5. INFERENCE API & GRADCAM++ FOR ViT
# ==============================================================================

def reshape_transform_vit(tensor, height=14, width=14):
    """Reshapes the ViT output [B, 197, 768] -> [B, 768, 14, 14] excluding CLS token."""
    result = tensor[:, 1:, :].reshape(tensor.size(0), height, width, tensor.size(2))
    result = result.transpose(2, 3).transpose(1, 2)
    return result

class OcularInferenceAPI:
    def __init__(self, checkpoint_dir=Config.CHECKPOINT_DIR):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.device = Config.DEVICE
        self.tfms = transforms.Compose([
            transforms.Resize((Config.IMG_SIZE, Config.IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.models = {}
        LOGGER.info(f"OcularInferenceAPI initialized. Using device: {self.device}")
        print(f"\n[API] OcularInferenceAPI Initialized successfully on {self.device.upper()}.")

    def load_model(self, task_name):
        """Lazy load models into memory only when requested to save VRAM."""
        if task_name in self.models:
            return self.models[task_name]
            
        task_info = Config.TASKS.get(task_name)
        if not task_info:
            LOGGER.error(f"Attempted to load unknown task: {task_name}")
            raise ValueError(f"Unknown task: {task_name}")
            
        _, num_classes, _ = task_info
        
        LOGGER.info(f"Lazy-loading model for task: {task_name}...")
        print(f"[API] ⏳ Lazy-loading model for task: {task_name}...")
        
        base_vit = FoundationalCVModel(backbone='vit_base', mode='eval')
        model = FoundationalCVModelWithClassifier(
            backbone=base_vit, hidden=256, num_classes=num_classes, mode='eval', backbone_mode='eval'
        ).to(self.device)
        
        ckpt_path = self.checkpoint_dir / f"best_model_{task_name}.pth"
        if not ckpt_path.exists():
            LOGGER.error(f"Checkpoint missing for {task_name} at {ckpt_path}")
            raise FileNotFoundError(f"Model checkpoint not found for {task_name} at {ckpt_path}")
            
        model.load_state_dict(torch.load(ckpt_path, map_location=self.device))
        model.eval()
        self.models[task_name] = model
        
        LOGGER.info(f"Successfully loaded model for {task_name}.")
        print(f"[API] ✅ Successfully loaded weights for {task_name}.")
        return model

    def predict_and_explain(self, img_path, task_name, target_class=None):
        """
        Runs inference and generates a GradCAM++ attention map.
        """
        LOGGER.info(f"Running inference for {task_name} on image: {Path(img_path).name}")
        print(f"\n[INFERENCE] Task: {task_name} | Target Image: {Path(img_path).name}")
        
        model = self.load_model(task_name)
        task_type, num_classes, _ = Config.TASKS[task_name]

        # 1. Load Image
        try:
            orig_img = Image.open(img_path).convert('RGB')
        except Exception as e:
            LOGGER.error(f"Failed to load image at {img_path}. Error: {e}")
            raise

        orig_img_resized = np.array(orig_img.resize((Config.IMG_SIZE, Config.IMG_SIZE))) / 255.0
        input_tensor = self.tfms(orig_img).unsqueeze(0).to(self.device)

        # 2. Inference
        with torch.no_grad():
            preds = model(input_tensor)
            
        if task_type == 'regression':
            pred_val = preds.item()
            prediction_text = f"Predicted {task_name}: {pred_val:.2f}"
            target_class_idx = 0
        else:
            probs = F.softmax(preds, dim=1).cpu().numpy()[0]
            pred_cls = np.argmax(probs)
            pred_val = probs[pred_cls]
            prediction_text = f"Predicted {task_name}: Class {pred_cls} (Prob: {pred_val:.2f})"
            target_class_idx = pred_cls if target_class is None else target_class
            
        LOGGER.info(prediction_text)
        print(f"  -> Result: {prediction_text}")

        # 3. GradCAM++ for ViT
        LOGGER.info(f"Generating GradCAM++ for {task_name}...")
        try:
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
            
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.imshow(orig_img_resized)
            plt.title("Original Image")
            plt.axis('off')
            
            plt.subplot(1, 2, 2)
            plt.imshow(visualization)
            plt.title(f"GradCAM++ ({prediction_text})")
            plt.axis('off')
            
            save_path = Config.CAM_DIR / f"{Path(img_path).stem}_{task_name}_cam.png"
            plt.savefig(save_path)
            plt.close()
            
            LOGGER.info(f"GradCAM++ successfully saved to {save_path}")
            print(f"  -> 📸 GradCAM++ Heatmap saved at: {save_path}")
            return prediction_text, save_path
            
        except Exception as e:
            LOGGER.error(f"Error during GradCAM++ generation for {task_name}: {e}", exc_info=True)
            print(f"  -> ❌ Error generating GradCAM++: {e}")
            raise

# ==============================================================================
# 6. MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    LOGGER.info("===" * 20)
    LOGGER.info("Starting Multi-Task Ocular Individual Modeling Pipeline")
    LOGGER.info("===" * 20)
    
    print("\n" + "="*80)
    print("🔥 Starting Multi-Task Ocular Individual Modeling Pipeline 🔥")
    print("="*80 + "\n")
    
    # Set to False if you only want to run inference with existing weights
    TRAIN_MODELS = True  
    
    if TRAIN_MODELS:
        try:
            train_df, val_df = prepare_data()
            for task_name, (task_type, num_classes, task_col) in Config.TASKS.items():
                try:
                    train_individual_model(task_name, task_type, num_classes, task_col, train_df, val_df)
                except Exception as e:
                    LOGGER.error(f"Training failed for task {task_name}. Skipping to next task.", exc_info=True)
                    print(f"❌ Training failed for {task_name}: {e}")
        except Exception as e:
            LOGGER.critical("Critical error during data preparation or main training loop.", exc_info=True)
            print(f"❌ Critical error: {e}")

    # Inference & GradCAM++ Generation Testing
    LOGGER.info("===" * 20)
    LOGGER.info("Starting API & GradCAM++ testing phase")
    LOGGER.info("===" * 20)
    
    api = OcularInferenceAPI()
    
    # Grab a random image from the dataset folder for testing
    sample_images = list(Config.IMG_DIR.glob("*.jpg")) + list(Config.IMG_DIR.glob("*.png"))
    if sample_images:
        test_img = sample_images[0]
        LOGGER.info(f"Selected test image: {test_img}")
        print(f"\n[*] Found test image: {test_img.name}")
        
        # Test on a subset of models
        tasks_to_test = ['ICDR', 'Age', 'Edema', 'Gender', 'Diabetes'] 
        
        for t in tasks_to_test:
            try:
                result_text, map_path = api.predict_and_explain(test_img, task_name=t)
            except Exception as e:
                LOGGER.error(f"Inference pipeline failed for task: {t}", exc_info=True)
                print(f"❌ Inference failed for {t}: {e}")
    else:
        LOGGER.warning(f"No test images found in {Config.IMG_DIR}. Skipping inference phase.")
        print(f"\n⚠️ No test images found in {Config.IMG_DIR}. Skipping inference test phase.")
        
    LOGGER.info("Pipeline execution completed successfully.")
    print("\n✅ Pipeline execution completed successfully.\n")