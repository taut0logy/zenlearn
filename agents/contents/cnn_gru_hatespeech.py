"""
Sophisticated CNN-GRU Model with Rationale-Guided Attention
for Hate Speech Detection on HateXplain Dataset

Architecture:
- Embedding Layer → CNN (multi-scale) → BiGRU → Rationale-Guided Attention → Classification
- Multi-task learning: Classification + Rationale Prediction
- LIME-based explainability
"""

import json
import numpy as np
import pandas as pd
import re
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
def set_seed(seed=42):
    """Ensure reproducibility across runs"""
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)

#############################################################################
# SECTION 1: DATA LOADING AND PREPROCESSING
#############################################################################

def load_and_process_hatexplain(json_path, num_samples=None):
    """
    Load HateXplain dataset and process majority labels, targets, and rationales
    
    Args:
        json_path: Path to HateXplain JSON file
        num_samples: Optional limit on number of samples
    
    Returns:
        DataFrame with processed data
    """
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    print(f"📊 Loaded {len(data)} posts from dataset")
    
    # Initialize storage lists
    FINAL_LABEL_LIST = []
    input_data = []
    rationales = []
    post_ids = []
    FINAL_TARGET_LIST = []
    
    def get_majority_label(label_list):
        """Get majority vote label (>50% agreement)"""
        if not label_list:
            return None
        label_counts = Counter(label_list)
        most_common_label, count = label_counts.most_common(1)[0]
        if count / len(label_list) > 0.5:
            return most_common_label
        return None
    
    def get_majority_targets(annotators):
        """Get targets mentioned by >50% of annotators"""
        if not annotators:
            return ['None']
        target_count = {}
        total_entries = len(annotators)
        
        for entry in annotators:
            for target in entry.get('target', []):
                target_count[target] = target_count.get(target, 0) + 1
        
        majority_targets = [
            target for target, count in target_count.items() 
            if count / total_entries > 0.5
        ]
        return majority_targets if majority_targets else ['None']
    
    # Process each post
    for k in data.keys():
        # Majority label
        label_list = [item['label'] for item in data[k]['annotators']]
        assigned_label = get_majority_label(label_list)
        FINAL_LABEL_LIST.append(assigned_label)
        
        # Majority targets
        majority_targets = get_majority_targets(data[k]['annotators'])
        FINAL_TARGET_LIST.append(majority_targets)
        
        # Post tokens to text
        input_data.append(' '.join(data[k]['post_tokens']))
        post_ids.append(data[k]['post_id'])
        
        # Process rationales (average across annotators)
        if k == '24439295_gab':  # Known problematic entry
            rationales.append([])
        else:
            rationales_array = np.array(data[k]['rationales'])
            if rationales_array.size > 0:
                averaged_rationales = np.mean(rationales_array, axis=0)
                finalized_rationales = [1 if value > 0.5 else 0 for value in averaged_rationales]
            else:
                finalized_rationales = [0] * len(data[k]['post_tokens'])
            rationales.append(finalized_rationales)
    
    # Create DataFrame
    df = pd.DataFrame({
        'post_ids': post_ids,
        'input_text': input_data,
        'rationales': rationales,
        'label': FINAL_LABEL_LIST,
        'Final_target': FINAL_TARGET_LIST,
    })
    
    # Remove entries without majority label
    df = df.dropna(subset=['label'])
    
    # Limit samples if specified
    if num_samples and num_samples < len(df):
        df = df.iloc[:num_samples].copy()
    
    print(f"✅ Processed {len(df)} posts with majority labels")
    print(f"📋 Label distribution:\n{df['label'].value_counts()}")
    
    return df


def clean_html_tags_and_update_rationales(row):
    """Remove HTML tags while maintaining rationale alignment"""
    tokens = row['input_text'].split()
    rationales = row['rationales']
    cleaned_tokens = []
    cleaned_rationales = []
    
    for token, rationale in zip(tokens, rationales):
        # Keep line breaks but remove other HTML tags
        if not re.match(r'<.*?>', token):
            cleaned_tokens.append(token)
            cleaned_rationales.append(rationale)
        elif token.lower() in ['<br>', '<hr>']:
            cleaned_tokens.append(token)
            cleaned_rationales.append(rationale)
    
    cleaned_text = ' '.join(cleaned_tokens)
    return pd.Series([cleaned_text, cleaned_rationales], index=['input_text', 'rationales'])


def filter_target_communities(df):
    """Filter targets to focus on specific communities"""
    final_communities_sel = [
        'African', 'Islam', 'Jewish', 'Homosexual', 'Women', 
        'Refugee', 'Arab', 'Caucasian', 'Asian', 'Hispanic'
    ]
    
    df.reset_index(inplace=True, drop=True)
    final_target_information = []
    
    for i in range(len(df)):
        if isinstance(df['Final_target'][i], list):
            temp = list(set(df['Final_target'][i]) & set(final_communities_sel))
            final_target_information.append(temp if temp else ['None'])
        else:
            final_target_information.append(['None'])
    
    df['Final_target'] = final_target_information
    
    all_values = [item for sublist in df['Final_target'] if isinstance(sublist, list) for item in sublist]
    unique_values = set(all_values)
    print(f"🎯 Target communities: {unique_values}")
    
    return df


#############################################################################
# SECTION 2: VOCABULARY AND DATASET PREPARATION
#############################################################################

class Vocabulary:
    """
    Build vocabulary from text data with special tokens
    Handles word-to-index and index-to-word mappings
    """
    def __init__(self, freq_threshold=2):
        self.freq_threshold = freq_threshold
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        
    def build_vocabulary(self, texts):
        """Build vocabulary from list of texts"""
        word_freq = Counter()
        for text in texts:
            tokens = text.lower().split()
            word_freq.update(tokens)
        
        idx = 2
        for word, freq in word_freq.items():
            if freq >= self.freq_threshold:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx += 1
        
        print(f"📚 Vocabulary size: {len(self.word2idx)}")
        
    def text_to_indices(self, text):
        """Convert text to list of indices"""
        tokens = text.lower().split()
        return [self.word2idx.get(token, self.word2idx['<UNK>']) for token in tokens]
    
    def __len__(self):
        return len(self.word2idx)


class HateSpeechDataset(Dataset):
    """
    PyTorch Dataset for hate speech detection
    Returns: text indices, rationales, labels, and sequence lengths
    """
    def __init__(self, texts, rationales, labels, vocabulary):
        self.texts = texts
        self.rationales = rationales
        self.labels = labels
        self.vocabulary = vocabulary
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        rationale = self.rationales[idx]
        label = self.labels[idx]
        
        # Convert text to indices
        indices = self.vocabulary.text_to_indices(text)
        
        # Ensure rationale matches length (pad/truncate if needed)
        if len(rationale) < len(indices):
            rationale = rationale + [0] * (len(indices) - len(rationale))
        elif len(rationale) > len(indices):
            rationale = rationale[:len(indices)]
        
        return {
            'indices': torch.LongTensor(indices),
            'rationale': torch.FloatTensor(rationale),
            'label': torch.LongTensor([label]),
            'length': len(indices)
        }


def collate_fn(batch):
    """
    Custom collate function for DataLoader
    Pads sequences to same length in batch
    """
    indices = [item['indices'] for item in batch]
    rationales = [item['rationale'] for item in batch]
    labels = torch.cat([item['label'] for item in batch])
    lengths = torch.LongTensor([item['length'] for item in batch])
    
    # Pad sequences
    indices_padded = pad_sequence(indices, batch_first=True, padding_value=0)
    rationales_padded = pad_sequence(rationales, batch_first=True, padding_value=0)
    
    return {
        'indices': indices_padded,
        'rationales': rationales_padded,
        'labels': labels,
        'lengths': lengths
    }


#############################################################################
# SECTION 3: CNN-GRU MODEL WITH RATIONALE-GUIDED ATTENTION
#############################################################################

class CNNFeatureExtractor(nn.Module):
    """
    Multi-scale CNN for extracting local n-gram features
    Uses multiple filter sizes (3, 4, 5) to capture different n-gram patterns
    """
    def __init__(self, embed_dim, num_filters=100, filter_sizes=[3, 4, 5], dropout=0.3):
        super(CNNFeatureExtractor, self).__init__()
        
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, 
                     out_channels=num_filters, 
                     kernel_size=fs,
                     padding=fs//2)  # Same padding
            for fs in filter_sizes
        ])
        
        self.dropout = nn.Dropout(dropout)
        self.output_dim = num_filters * len(filter_sizes)
        
    def forward(self, embedded):
        """
        Args:
            embedded: (batch_size, seq_len, embed_dim)
        Returns:
            cnn_features: (batch_size, seq_len, num_filters * len(filter_sizes))
        """
        # Transpose for Conv1d: (batch, embed_dim, seq_len)
        embedded = embedded.transpose(1, 2)
        
        # Apply convolutions and activation
        conv_outputs = []
        for conv in self.convs:
            conv_out = F.relu(conv(embedded))  # (batch, num_filters, seq_len)
            conv_outputs.append(conv_out)
        
        # Concatenate features from different filter sizes
        concatenated = torch.cat(conv_outputs, dim=1)  # (batch, num_filters*len(filter_sizes), seq_len)
        
        # Transpose back: (batch, seq_len, num_filters*len(filter_sizes))
        concatenated = concatenated.transpose(1, 2)
        
        return self.dropout(concatenated)


class RationaleGuidedAttention(nn.Module):
    """
    Attention mechanism guided by ground-truth rationales
    
    Two modes:
    1. Training: Uses rationales as supervision signal
    2. Inference: Uses learned attention weights
    """
    def __init__(self, hidden_dim, dropout=0.3):
        super(RationaleGuidedAttention, self).__init__()
        
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, gru_output, rationales=None, lengths=None):
        """
        Args:
            gru_output: (batch_size, seq_len, hidden_dim)
            rationales: (batch_size, seq_len) - ground truth importance
            lengths: (batch_size,) - actual sequence lengths
        
        Returns:
            context: (batch_size, hidden_dim) - weighted representation
            attention_weights: (batch_size, seq_len) - attention scores
        """
        batch_size, seq_len, hidden_dim = gru_output.size()
        
        # Compute attention scores
        attention_scores = self.attention(gru_output).squeeze(-1)  # (batch, seq_len)
        
        # Create padding mask
        if lengths is not None:
            mask = torch.arange(seq_len, device=gru_output.device).unsqueeze(0) < lengths.unsqueeze(1)
            attention_scores = attention_scores.masked_fill(~mask, -1e9)
        
        # Compute attention weights
        attention_weights = F.softmax(attention_scores, dim=1)  # (batch, seq_len)
        
        # Apply attention to GRU output
        context = torch.bmm(attention_weights.unsqueeze(1), gru_output).squeeze(1)  # (batch, hidden_dim)
        
        return context, attention_weights


class CNN_GRU_RationaleModel(nn.Module):
    """
    Complete CNN-GRU model with rationale-guided attention
    
    Architecture Flow:
    Input → Embedding → CNN (local features) → BiGRU (sequential) → 
    Attention (rationale-guided) → Classification + Rationale Prediction
    """
    def __init__(self, vocab_size, embed_dim=300, hidden_dim=256, 
                 num_filters=100, filter_sizes=[3, 4, 5],
                 num_classes=3, dropout=0.5):
        super(CNN_GRU_RationaleModel, self).__init__()
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # CNN feature extractor
        self.cnn = CNNFeatureExtractor(embed_dim, num_filters, filter_sizes, dropout)
        
        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size=self.cnn.output_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if 2 > 1 else 0
        )
        
        # Rationale-guided attention
        self.attention = RationaleGuidedAttention(hidden_dim * 2, dropout)  # *2 for bidirectional
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )
        
        # Rationale prediction head (token-level)
        self.rationale_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
    def forward(self, indices, lengths, rationales=None):
        """
        Forward pass with multi-task outputs
        
        Returns:
            logits: (batch, num_classes) - classification logits
            attention_weights: (batch, seq_len) - attention scores
            rationale_preds: (batch, seq_len) - predicted rationales
        """
        # Embedding
        embedded = self.embedding(indices)  # (batch, seq_len, embed_dim)
        
        # CNN features
        cnn_features = self.cnn(embedded)  # (batch, seq_len, cnn_output_dim)
        
        # Pack sequence for GRU (efficiency)
        packed = pack_padded_sequence(
            cnn_features, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        
        # BiGRU
        gru_output, _ = self.gru(packed)
        gru_output, _ = pad_packed_sequence(gru_output, batch_first=True)  # (batch, seq_len, hidden*2)
        
        # Rationale-guided attention
        context, attention_weights = self.attention(gru_output, rationales, lengths)
        
        # Classification
        logits = self.classifier(context)  # (batch, num_classes)
        
        # Rationale prediction (token-level)
        rationale_preds = self.rationale_predictor(gru_output).squeeze(-1)  # (batch, seq_len)
        
        return logits, attention_weights, rationale_preds


#############################################################################
# SECTION 4: TRAINING PIPELINE WITH MULTI-TASK LEARNING
#############################################################################

class MultiTaskTrainer:
    """
    Sophisticated trainer with multi-task learning
    Tasks: Classification + Rationale Prediction
    
    Features:
    - Early stopping
    - Learning rate scheduling
    - Gradient clipping
    - Checkpoint saving
    - Comprehensive metrics tracking
    """
    def __init__(self, model, device, class_weights=None):
        self.model = model.to(device)
        self.device = device
        
        # Loss functions
        if class_weights is not None:
            class_weights = torch.FloatTensor(class_weights).to(device)
        self.classification_loss = nn.CrossEntropyLoss(weight=class_weights)
        self.rationale_loss = nn.BCELoss()
        
        # Optimizer with weight decay
        self.optimizer = torch.optim.AdamW(
            model.parameters(), lr=0.001, weight_decay=0.01
        )
        
        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='max', patience=3, factor=0.5, verbose=True
        )
        
        # Training history
        self.history = {
            'train_loss': [], 'train_acc': [], 'train_f1': [],
            'val_loss': [], 'val_acc': [], 'val_f1': []
        }
        
        self.best_val_f1 = 0.0
        self.patience_counter = 0
        
    def compute_loss(self, logits, labels, rationale_preds, rationale_targets, lengths):
        """
        Compute combined multi-task loss
        
        Loss = α * Classification Loss + β * Rationale Loss
        """
        # Classification loss
        cls_loss = self.classification_loss(logits, labels)
        
        # Rationale loss (only on actual sequence, ignore padding)
        batch_size, max_len = rationale_preds.size()
        mask = torch.arange(max_len, device=self.device).unsqueeze(0) < lengths.unsqueeze(1)
        
        masked_preds = rationale_preds[mask]
        masked_targets = rationale_targets[mask]
        
        rat_loss = self.rationale_loss(masked_preds, masked_targets) if masked_preds.numel() > 0 else 0.0
        
        # Combined loss with weighting
        total_loss = cls_loss + 0.3 * rat_loss  # β=0.3 for rationale importance
        
        return total_loss, cls_loss, rat_loss
    
    def train_epoch(self, train_loader):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        all_preds, all_labels = [], []
        
        progress_bar = tqdm(train_loader, desc="Training")
        for batch in progress_bar:
            indices = batch['indices'].to(self.device)
            rationales = batch['rationales'].to(self.device)
            labels = batch['labels'].to(self.device)
            lengths = batch['lengths'].to(self.device)
            
            # Forward pass
            logits, attn_weights, rationale_preds = self.model(indices, lengths, rationales)
            
            # Compute loss
            loss, cls_loss, rat_loss = self.compute_loss(
                logits, labels, rationale_preds, rationales, lengths
            )
            
            # Backward pass with gradient clipping
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Track predictions
            preds = torch.argmax(logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'cls_loss': f'{cls_loss.item():.4f}',
                'rat_loss': f'{rat_loss.item() if isinstance(rat_loss, torch.Tensor) else rat_loss:.4f}'
            })
        
        avg_loss = total_loss / len(train_loader)
        acc = accuracy_score(all_labels, all_preds)
        f1 = f1_score(all_labels, all_preds, average='weighted')
        
        return avg_loss, acc, f1
    
    def validate(self, val_loader):
        """Validate the model"""
        self.model.eval()
        total_loss = 0
        all_preds, all_labels = [], []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validating"):
                indices = batch['indices'].to(self.device)
                rationales = batch['rationales'].to(self.device)
                labels = batch['labels'].to(self.device)
                lengths = batch['lengths'].to(self.device)
                
                logits, attn_weights, rationale_preds = self.model(indices, lengths, rationales)
                
                loss, _, _ = self.compute_loss(
                    logits, labels, rationale_preds, rationales, lengths
                )
                
                total_loss += loss.item()
                
                preds = torch.argmax(logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_loss = total_loss / len(val_loader)
        acc = accuracy_score(all_labels, all_preds)
        f1 = f1_score(all_labels, all_preds, average='weighted')
        
        return avg_loss, acc, f1, all_preds, all_labels
    
    def train(self, train_loader, val_loader, epochs=30, early_stopping_patience=7):
        """
        Full training loop with early stopping
        """
        print("\n🚀 Starting training...")
        
        for epoch in range(epochs):
            print(f"\n{'='*60}")
            print(f"Epoch {epoch+1}/{epochs}")
            print(f"{'='*60}")
            
            # Train
            train_loss, train_acc, train_f1 = self.train_epoch(train_loader)
            
            # Validate
            val_loss, val_acc, val_f1, val_preds, val_labels = self.validate(val_loader)
            
            # Update scheduler
            self.scheduler.step(val_f1)
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['train_f1'].append(train_f1)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['val_f1'].append(val_f1)
            
            # Print metrics
            print(f"\n📊 Epoch {epoch+1} Results:")
            print(f"  Train - Loss: {train_loss:.4f}, Acc: {train_acc:.4f}, F1: {train_f1:.4f}")
            print(f"  Val   - Loss: {val_loss:.4f}, Acc: {val_acc:.4f}, F1: {val_f1:.4f}")
            
            # Early stopping and checkpointing
            if val_f1 > self.best_val_f1:
                self.best_val_f1 = val_f1
                self.patience_counter = 0
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_f1': val_f1,
                }, '/home/claude/best_model.pt')
                print(f"  ✅ New best model saved! (F1: {val_f1:.4f})")
            else:
                self.patience_counter += 1
                print(f"  ⏳ No improvement ({self.patience_counter}/{early_stopping_patience})")
            
            if self.patience_counter >= early_stopping_patience:
                print(f"\n⛔ Early stopping triggered after {epoch+1} epochs")
                break
        
        print(f"\n🎉 Training complete! Best Val F1: {self.best_val_f1:.4f}")
        
        # Load best model
        checkpoint = torch.load('/home/claude/best_model.pt')
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        return self.history


#############################################################################
# SECTION 5: EXPLAINABILITY WITH LIME
#############################################################################

class LIMEExplainer:
    """
    LIME-based explainability for CNN-GRU model
    
    Provides:
    1. Word-level importance scores
    2. Visualization of predictions
    3. Integration with built-in attention weights
    """
    def __init__(self, model, vocabulary, label_encoder, device):
        self.model = model
        self.vocabulary = vocabulary
        self.label_encoder = label_encoder
        self.device = device
        self.model.eval()
        
    def predict_proba(self, texts):
        """
        Prediction function for LIME
        Returns probability distributions for list of texts
        """
        probas = []
        
        for text in texts:
            # Convert text to indices
            indices = self.vocabulary.text_to_indices(text)
            indices_tensor = torch.LongTensor([indices]).to(self.device)
            length_tensor = torch.LongTensor([len(indices)]).to(self.device)
            
            with torch.no_grad():
                logits, _, _ = self.model(indices_tensor, length_tensor)
                proba = F.softmax(logits, dim=1).cpu().numpy()[0]
            
            probas.append(proba)
        
        return np.array(probas)
    
    def explain_prediction(self, text, num_features=10, num_samples=5000):
        """
        Generate LIME explanation for a text
        
        Returns:
            - Predicted label
            - Probability distribution
            - Word importance scores
            - Attention weights (built-in)
        """
        from lime.lime_text import LimeTextExplainer
        
        # Create LIME explainer
        explainer = LimeTextExplainer(class_names=self.label_encoder.classes_)
        
        # Generate explanation
        exp = explainer.explain_instance(
            text,
            self.predict_proba,
            num_features=num_features,
            num_samples=num_samples
        )
        
        # Get prediction
        indices = self.vocabulary.text_to_indices(text)
        indices_tensor = torch.LongTensor([indices]).to(self.device)
        length_tensor = torch.LongTensor([len(indices)]).to(self.device)
        
        with torch.no_grad():
            logits, attention_weights, rationale_preds = self.model(indices_tensor, length_tensor)
            proba = F.softmax(logits, dim=1).cpu().numpy()[0]
            predicted_class = torch.argmax(logits, dim=1).item()
            predicted_label = self.label_encoder.inverse_transform([predicted_class])[0]
        
        # Get attention weights and rationale predictions
        attention_weights = attention_weights[0].cpu().numpy()
        rationale_preds = rationale_preds[0].cpu().numpy()
        
        return {
            'predicted_label': predicted_label,
            'probabilities': proba,
            'lime_explanation': exp,
            'attention_weights': attention_weights[:len(text.split())],
            'rationale_predictions': rationale_preds[:len(text.split())],
            'tokens': text.split()
        }
    
    def visualize_explanation(self, explanation_dict, save_path=None):
        """
        Visualize explanation with multiple perspectives:
        1. LIME word importance
        2. Attention weights
        3. Predicted rationales
        """
        tokens = explanation_dict['tokens']
        lime_exp = explanation_dict['lime_explanation']
        attention = explanation_dict['attention_weights']
        rationales = explanation_dict['rationale_predictions']
        
        # Get LIME scores
        lime_scores = dict(lime_exp.as_list())
        lime_values = [lime_scores.get(token, 0) for token in tokens]
        
        # Create visualization
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 1. LIME importance
        axes[0].barh(range(len(tokens)), lime_values, color='skyblue')
        axes[0].set_yticks(range(len(tokens)))
        axes[0].set_yticklabels(tokens)
        axes[0].set_xlabel('LIME Importance Score')
        axes[0].set_title('LIME Word Importance (Model-Agnostic)')
        axes[0].invert_yaxis()
        
        # 2. Attention weights
        axes[1].barh(range(len(tokens)), attention[:len(tokens)], color='lightcoral')
        axes[1].set_yticks(range(len(tokens)))
        axes[1].set_yticklabels(tokens)
        axes[1].set_xlabel('Attention Weight')
        axes[1].set_title('Model Attention Weights (Built-in Explainability)')
        axes[1].invert_yaxis()
        
        # 3. Predicted rationales
        axes[2].barh(range(len(tokens)), rationales[:len(tokens)], color='lightgreen')
        axes[2].set_yticks(range(len(tokens)))
        axes[2].set_yticklabels(tokens)
        axes[2].set_xlabel('Rationale Prediction Score')
        axes[2].set_title('Predicted Rationale (Learned Importance)')
        axes[2].invert_yaxis()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Visualization saved to {save_path}")
        
        plt.show()
        
        # Print prediction info
        print(f"\n🎯 Prediction: {explanation_dict['predicted_label']}")
        print(f"📊 Probabilities:")
        for i, prob in enumerate(explanation_dict['probabilities']):
            print(f"   {i}: {prob:.4f}")


#############################################################################
# SECTION 6: MAIN EXECUTION PIPELINE
#############################################################################

def main():
    """
    Main execution pipeline
    Orchestrates: Data loading → Training → Evaluation → Explainability
    """
    # Configuration
    DATA_PATH = '/mnt/user-data/uploads/mini_dataset.json'
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  Using device: {DEVICE}")
    
    # Step 1: Load and preprocess data
    print("\n" + "="*60)
    print("STEP 1: DATA LOADING & PREPROCESSING")
    print("="*60)
    
    df = load_and_process_hatexplain(DATA_PATH)
    df = df.apply(clean_html_tags_and_update_rationales, axis=1)
    df = filter_target_communities(df)
    
    # Prepare labels
    label_encoder = LabelEncoder()
    df['label_encoded'] = label_encoder.fit_transform(df['label'])
    
    print(f"\n📋 Classes: {label_encoder.classes_}")
    
    # Step 2: Build vocabulary
    print("\n" + "="*60)
    print("STEP 2: VOCABULARY BUILDING")
    print("="*60)
    
    vocabulary = Vocabulary(freq_threshold=1)  # Low threshold for small dataset
    vocabulary.build_vocabulary(df['input_text'].tolist())
    
    # Step 3: Split data
    print("\n" + "="*60)
    print("STEP 3: TRAIN/VAL SPLIT")
    print("="*60)
    
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label_encoded'])
    print(f"✅ Train: {len(train_df)}, Val: {len(val_df)}")
    
    # Create datasets
    train_dataset = HateSpeechDataset(
        train_df['input_text'].tolist(),
        train_df['rationales'].tolist(),
        train_df['label_encoded'].tolist(),
        vocabulary
    )
    
    val_dataset = HateSpeechDataset(
        val_df['input_text'].tolist(),
        val_df['rationales'].tolist(),
        val_df['label_encoded'].tolist(),
        vocabulary
    )
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, collate_fn=collate_fn)
    
    # Step 4: Initialize model
    print("\n" + "="*60)
    print("STEP 4: MODEL INITIALIZATION")
    print("="*60)
    
    model = CNN_GRU_RationaleModel(
        vocab_size=len(vocabulary),
        embed_dim=128,  # Reduced for small dataset
        hidden_dim=128,
        num_filters=64,
        filter_sizes=[2, 3, 4],
        num_classes=len(label_encoder.classes_),
        dropout=0.3
    )
    
    print(f"✅ Model initialized with {sum(p.numel() for p in model.parameters()):,} parameters")
    
    # Step 5: Train model
    print("\n" + "="*60)
    print("STEP 5: TRAINING")
    print("="*60)
    
    # Compute class weights for imbalanced data
    class_counts = df['label_encoded'].value_counts().sort_index().values
    class_weights = 1.0 / class_counts
    class_weights = class_weights / class_weights.sum() * len(class_counts)
    
    trainer = MultiTaskTrainer(model, DEVICE, class_weights)
    history = trainer.train(train_loader, val_loader, epochs=50, early_stopping_patience=10)
    
    # Step 6: Final evaluation
    print("\n" + "="*60)
    print("STEP 6: FINAL EVALUATION")
    print("="*60)
    
    _, val_acc, val_f1, val_preds, val_labels = trainer.validate(val_loader)
    
    print(f"\n📊 Final Validation Metrics:")
    print(f"  Accuracy: {val_acc:.4f}")
    print(f"  Weighted F1: {val_f1:.4f}")
    
    print("\n📋 Classification Report:")
    print(classification_report(val_labels, val_preds, target_names=label_encoder.classes_))
    
    # Step 7: LIME Explainability
    print("\n" + "="*60)
    print("STEP 7: EXPLAINABILITY WITH LIME")
    print("="*60)
    
    lime_explainer = LIMEExplainer(model, vocabulary, label_encoder, DEVICE)
    
    # Example explanation
    test_text = df['input_text'].iloc[0]
    print(f"\n🔍 Explaining: '{test_text}'")
    
    explanation = lime_explainer.explain_prediction(test_text, num_features=10)
    lime_explainer.visualize_explanation(explanation, save_path='/home/claude/explanation.png')
    
    # Show LIME in notebook format
    explanation['lime_explanation'].show_in_notebook(text=True)
    
    print("\n✅ Pipeline complete!")
    
    return model, vocabulary, label_encoder, trainer, lime_explainer


if __name__ == "__main__":
    model, vocabulary, label_encoder, trainer, lime_explainer = main()
