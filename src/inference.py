import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

class BugInferenceEngine:
    def __init__(self, classifier_path: str, embeddings_path: str):
        if not os.path.exists(classifier_path) or not os.path.exists(embeddings_path):
            raise FileNotFoundError("ONNX transformer artifacts missing from specified path.")
            
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        
        self.clf_session = ort.InferenceSession(classifier_path)
        self.emb_session = ort.InferenceSession(embeddings_path)
        
        self.team_mapping = {
            0: "Core-Platform-Team",
            1: "Billing-And-Payments",
            2: "Network-Infrastructure"
        }

    def _tokenize(self, text: str) -> dict[str, np.ndarray]:
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="np"
        )
        return {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }

    def _get_model_inputs(self, session: ort.InferenceSession, tokenized_dict: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Filters input dictionary to match strictly what the ONNX graph expects"""
        valid_inputs = [i.name for i in session.get_inputs()]
        return {k: v for k, v in tokenized_dict.items() if k in valid_inputs}

    def predict_team(self, text: str) -> tuple[str, float]:
        tokenized = self._tokenize(text)
        onnx_inputs = self._get_model_inputs(self.clf_session, tokenized)
        
        raw_outputs = self.clf_session.run(None, onnx_inputs)
        logits = raw_outputs[0][0]
        
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / exp_logits.sum()
        
        predicted_class = int(np.argmax(probabilities))
        predicted_team = self.team_mapping.get(predicted_class, "Unassigned")
        confidence = float(probabilities[predicted_class])
        
        return predicted_team, round(confidence, 2)

    def generate_embeddings(self, text: str) -> list[float]:
        tokenized = self._tokenize(text)
        onnx_inputs = self._get_model_inputs(self.emb_session, tokenized)
        
        raw_outputs = self.emb_session.run(None, onnx_inputs)
        embedding_vector = raw_outputs[0][0].tolist()
        
        return embedding_vector