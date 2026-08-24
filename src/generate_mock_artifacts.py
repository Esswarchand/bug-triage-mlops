import os
import torch
import torch.nn as nn

os.makedirs("ml_artifacts", exist_ok=True)

# 1. DistilBERT Classification Model Export (Outputs logits for 3 teams)
class MockDistilBERTForSequenceClassification(nn.Module):
    def __init__(self):
        super().__init__()
        self.classifier = nn.Linear(768, 3)

    def forward(self, input_ids, attention_mask):
        batch_size = input_ids.shape[0]
        # Perform computation with attention_mask so ONNX tracer retains it as an input node
        mask_scale = attention_mask.sum(dim=1, keepdim=True).float() / 128.0
        dummy_hidden = torch.ones(batch_size, 768) * mask_scale
        logits = self.classifier(dummy_hidden)
        return logits

# 2. Sentence-Transformer (all-MiniLM-L6-v2) Model Export (Outputs 384-d vector)
class MockMiniLMEmbedder(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(384, 384)

    def forward(self, input_ids, attention_mask):
        batch_size = input_ids.shape[0]
        mask_scale = attention_mask.sum(dim=1, keepdim=True).float() / 128.0
        raw_emb = torch.ones(batch_size, 384) * mask_scale
        out = self.projection(raw_emb)
        norm_emb = torch.nn.functional.normalize(out, p=2, dim=1)
        return norm_emb

# Dummy inputs matching Hugging Face Tokenizer tensor outputs
dummy_input_ids = torch.ones(1, 128, dtype=torch.long)
dummy_attention_mask = torch.ones(1, 128, dtype=torch.long)

# Export DistilBERT Classifier to ONNX
distilbert_model = MockDistilBERTForSequenceClassification()
torch.onnx.export(
    distilbert_model,
    (dummy_input_ids, dummy_attention_mask),
    "ml_artifacts/classifier.onnx",
    input_names=["input_ids", "attention_mask"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "logits": {0: "batch_size"}
    },
    opset_version=14
)

# Export MiniLM Embedder to ONNX
minilm_model = MockMiniLMEmbedder()
torch.onnx.export(
    minilm_model,
    (dummy_input_ids, dummy_attention_mask),
    "ml_artifacts/embeddings.onnx",
    input_names=["input_ids", "attention_mask"],
    output_names=["embeddings"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "embeddings": {0: "batch_size"}
    },
    opset_version=14
)

print("SUCCESS: DistilBERT and MiniLM ONNX Transformer artifacts created in ./ml_artifacts/")