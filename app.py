import os
import logging
from flask import Flask, render_template, request, jsonify
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize RAG service
rag_service = RAGService()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat queries"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        logger.info(f"Processing query: {query}")
        
        # Process query through RAG pipeline
        response = rag_service.process_query(query)
        
        return jsonify({
            'response': response['answer'],
            'sources': response.get('sources', []),
            'metadata': response.get('metadata', {})
        })
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({'error': 'An error occurred processing your query. Please try again.'}), 500

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize the RAG system by processing Firebase data"""
    try:
        logger.info("Initializing RAG system...")
        
        # Initialize the RAG service (fetch data, generate embeddings, etc.)
        result = rag_service.initialize()
        
        return jsonify({
            'status': 'success',
            'message': f"RAG system initialized successfully. Processed {result.get('total_chunks', 0)} chunks.",
            'details': result
        })
        
    except Exception as e:
        logger.error(f"Error initializing RAG system: {str(e)}")
        return jsonify({'error': 'Failed to initialize RAG system. Please check logs.'}), 500

@app.route('/api/status')
def status():
    """Get system status"""
    try:
        status_info = rag_service.get_status()
        return jsonify(status_info)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': 'Failed to get system status'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)