from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Bug Triage & RCA Engine API"
    environment: str = "production"
    classifier_onnx_path: str = "ml_artifacts/classifier.onnx"
    embeddings_onnx_path: str = "ml_artifacts/embeddings.onnx"
    
    # AWS OpenSearch Vector DB configuration
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_index: str = "historic-bugs"
    
    class Config:
        env_file = ".env"

settings = Settings()