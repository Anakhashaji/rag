import os

class Config:
    # Firebase configuration
    FIREBASE_CONFIG = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": f"{os.getenv('FIREBASE_PROJECT_ID', 'testing-2c10f')}.firebaseapp.com",
        "databaseURL": f"https://{os.getenv('FIREBASE_PROJECT_ID', 'testing-2c10f')}-default-rtdb.firebaseio.com",
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": f"{os.getenv('FIREBASE_PROJECT_ID', 'testing-2c10f')}.firebasestorage.app",
        "messagingSenderId": "438113286123",
        "appId": os.getenv("FIREBASE_APP_ID"),
        "measurementId": "G-CKLSSSBQTT"
    }
    
    # Hugging Face configuration
    HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN', 'hf_xxxxxxxxxxxxxxxxxxx')
    EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'BAAI/bge-small-en-v1.5')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'meta-llama/Llama-3.1-8B-Instruct')
    
    # API endpoints
    EMBEDDING_API_URL = f"https://api-inference.huggingface.co/models/{EMBEDDING_MODEL_NAME}"
    LLM_API_URL = "https://router.huggingface.co/v1/chat/completions"
    
    # ChromaDB configuration
    CHROMA_PERSIST_DIRECTORY = "chroma_db"
    CHROMA_COLLECTION_NAME = "trainer_feedback"
    
    # Text processing configuration
    MAX_CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Retrieval configuration
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.7