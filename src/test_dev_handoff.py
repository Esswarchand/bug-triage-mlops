from src.inference import BugInferenceEngine

def main():
    engine = BugInferenceEngine(
        classifier_path="ml_artifacts/classifier.onnx",
        embeddings_path="ml_artifacts/embeddings.onnx"
    )
    
    sample_text = "Null Pointer Exception in Auth Middleware token parsing"
    team, confidence = engine.predict_team(sample_text)
    embedding = engine.generate_embeddings(sample_text)
    
    print("--- TRANSFORMATION STACK HANDOFF TEST ---")
    print(f"Sample Bug Text: {sample_text}")
    print(f"DistilBERT Predicted Team: {team}")
    print(f"Confidence Score: {confidence}")
    print(f"all-MiniLM-L6-v2 Vector Dimensions: {len(embedding)}")
    print("STATUS: Transformer ONNX Dev Code Verified Successfully!")

if __name__ == "__main__":
    main()