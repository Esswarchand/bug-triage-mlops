import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, make_asgi_app
from opensearchpy import OpenSearch, exceptions as OpenSearchExceptions

from app.config import settings
from src.inference import BugInferenceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bug_triage_api")

# Global Inference Engine Instance
inference_engine = None
opensearch_client = None

# ---------------------------------------------------------
# PROMETHEUS METRICS INSTRUMENTATION
# ---------------------------------------------------------
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total HTTP Requests", 
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP Request Latency in Seconds", 
    ["endpoint"]
)
MODEL_PREDICTION_COUNTER = Counter(
    "model_predictions_total", 
    "Total Predictions grouped by Target Team", 
    ["predicted_team"]
)
OPENSEARCH_LATENCY = Histogram(
    "opensearch_search_duration_seconds", 
    "Vector Search Latency in OpenSearch"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to initialize models and connections on startup"""
    global inference_engine, opensearch_client
    logger.info("Initializing DistilBERT & MiniLM ONNX Inference Engine...")
    
    inference_engine = BugInferenceEngine(
        classifier_path=settings.classifier_onnx_path,
        embeddings_path=settings.embeddings_onnx_path
    )
    
    # Initialize OpenSearch Vector DB Connection
    opensearch_client = OpenSearch(
        hosts=[{'host': settings.opensearch_host, 'port': settings.opensearch_port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False
    )
    logger.info("Service Startup Complete.")
    yield
    logger.info("Shutting down service...")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Expose /metrics endpoint for Prometheus scraping
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ---------------------------------------------------------
# PYDANTIC SCHEMAS (Data Validation Contracts)
# ---------------------------------------------------------
class BugPayload(BaseModel):
    bug_id: str = Field(..., json_schema_extra={"example": "BUG-8921"})
    summary: str = Field(..., json_schema_extra={"example": "Null Pointer Exception in Auth Middleware"})
    description: str = Field(..., json_schema_extra={"example": "Token parser fails on missing Bearer prefix in header"})
    stacktrace: str = Field(default="", json_schema_extra={"example": "java.lang.NullPointerException at auth.v2.TokenFilter..."})

class HistoricBugMatch(BaseModel):
    historic_bug_id: str
    similarity_score: float
    rca: str
    resolution: str

class TriageResponse(BaseModel):
    bug_id: str
    predicted_team: str
    confidence_score: float
    top_similar_historic_bugs: list[HistoricBugMatch]

# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Liveness probe endpoint for Kubernetes pods"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Inference engine not ready")
    return {"status": "healthy", "service": settings.app_name}

@app.post("/api/v1/triage", response_model=TriageResponse)
async def triage_bug(payload: BugPayload):
    start_time = time.time()
    
    try:
        # 1. Concatenate fields as expected by ML models
        combined_text = f"{payload.summary} \n {payload.description} \n {payload.stacktrace}"
        
        # 2. Run DistilBERT ONNX Team Classifier
        predicted_team, confidence = inference_engine.predict_team(combined_text)
        MODEL_PREDICTION_COUNTER.labels(predicted_team=predicted_team).inc()
        
        # 3. Run MiniLM ONNX Model to generate 384-d dense embedding
        embedding_vector = inference_engine.generate_embeddings(combined_text)
        
        # 4. Perform Vector KNN Search against OpenSearch
        similar_bugs = []
        os_start = time.time()
        
        try:
            query = {
                "size": 5,
                "query": {
                    "knn": {
                        "bug_vector": {
                            "vector": embedding_vector,
                            "k": 5
                        }
                    }
                }
            }
            response = opensearch_client.search(body=query, index=settings.opensearch_index)
            OPENSEARCH_LATENCY.observe(time.time() - os_start)
            
            for hit in response['hits']['hits']:
                source = hit['_source']
                similar_bugs.append(HistoricBugMatch(
                    historic_bug_id=source.get('historic_bug_id', 'BUG-UNKNOWN'),
                    similarity_score=round(hit['_score'], 2),
                    rca=source.get('rca', 'No RCA available'),
                    resolution=source.get('resolution', 'No resolution logged')
                ))
        except Exception as os_err:
            logger.warning(f"OpenSearch query failed or unavailable (fallback mode activated): {os_err}")
            # Fallback mock response for local testing when OpenSearch cluster is offline
            similar_bugs = [
                HistoricBugMatch(
                    historic_bug_id="BUG-4102",
                    similarity_score=0.89,
                    rca="Expired token header handling missing check",
                    resolution="Updated token parsing logic in auth middleware v2.1"
                )
            ]

        # Record API Latency and Request metrics
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint="/api/v1/triage").observe(duration)
        REQUEST_COUNT.labels(method="POST", endpoint="/api/v1/triage", http_status="200").inc()

        return TriageResponse(
            bug_id=payload.bug_id,
            predicted_team=predicted_team,
            confidence_score=confidence,
            top_similar_historic_bugs=similar_bugs
        )

    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/api/v1/triage", http_status="500").inc()
        logger.error(f"Inference Failure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")