from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import traceback

# Import our database functions
from db import get_database, save_translation_history, get_user_history

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Test database connection on startup
def initialize():
    try:
        db = get_database()
        print("✅ Successfully connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")

# Initialize database connection when app starts
initialize()

@app.route('/')
def home():
    return jsonify({"message": "Voice Translation API Server", "status": "running"})

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db = get_database()
        # Test database connectivity
        db.command('ping')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/save-translation', methods=['POST'])
def save_translation():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['uid', 'translation_type', 'source_text', 'translated_text', 'source_lang', 'target_lang']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create translation record
        translation_record = {
            'uid': data['uid'],
            'translation_type': data['translation_type'],  # 'text_to_text', 'speech_to_text', 'text_to_speech'
            'source_text': data['source_text'],
            'translated_text': data['translated_text'],
            'source_lang': data['source_lang'],
            'target_lang': data['target_lang'],
            'timestamp': datetime.utcnow(),
            'audio_duration': data.get('audio_duration'),  # Optional for speech features
            'confidence_score': data.get('confidence_score')  # Optional for speech recognition
        }
        
        # Save to MongoDB
        result = save_translation_history(translation_record)
        
        if result:
            return jsonify({
                "message": "Translation saved successfully", 
                "translation_id": str(result)
            }), 201
        else:
            return jsonify({"error": "Failed to save translation"}), 500
            
    except Exception as e:
        print(f"Error saving translation: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/history/<uid>', methods=['GET'])
def get_history(uid):
    try:
        # Get query parameters for filtering
        translation_type = request.args.get('type')  # Optional filter
        limit = int(request.args.get('limit', 50))  # Default 50 records
        
        history = get_user_history(uid, translation_type, limit)
        
        return jsonify({
            "history": history,
            "count": len(history)
        }), 200
        
    except Exception as e:
        print(f"Error fetching history: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/history/<uid>/<translation_type>', methods=['GET'])
def get_history_by_type(uid, translation_type):
    try:
        limit = int(request.args.get('limit', 50))
        history = get_user_history(uid, translation_type, limit)
        
        return jsonify({
            "history": history,
            "count": len(history),
            "type": translation_type
        }), 200
        
    except Exception as e:
        print(f"Error fetching history by type: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/delete-history/<uid>', methods=['DELETE'])
def delete_user_history(uid):
    try:
        db = get_database()
        collection = db['translation_history']
        
        # Delete all history for this user
        result = collection.delete_many({'uid': uid})
        
        return jsonify({
            "message": f"Deleted {result.deleted_count} translation records",
            "deleted_count": result.deleted_count
        }), 200
        
    except Exception as e:
        print(f"Error deleting history: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/delete-translation/<translation_id>', methods=['DELETE'])
def delete_single_translation(translation_id):
    try:
        from bson import ObjectId
        db = get_database()
        collection = db['translation_history']
        
        # Delete specific translation
        result = collection.delete_one({'_id': ObjectId(translation_id)})
        
        if result.deleted_count > 0:
            return jsonify({"message": "Translation deleted successfully"}), 200
        else:
            return jsonify({"error": "Translation not found"}), 404
            
    except Exception as e:
        print(f"Error deleting translation: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=True)