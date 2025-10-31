import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# MongoDB connection globals
client = None
database = None

def get_database():
    """Get MongoDB database connection with improved error handling"""
    global client, database
    
    if database is not None:
        try:
            # Test existing connection
            database.command('ping')
            return database
        except:
            # Reset if connection is stale
            client = None
            database = None
    
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('DB_NAME', 'voice_translation')
        
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        print(f"🔗 Attempting to connect to MongoDB Atlas...")
        print(f"🏷️  Database: {db_name}")
        
        # Create MongoDB client with optimized settings
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            maxPoolSize=50,
            retryWrites=True,
            w='majority'
        )
        
        # Test the connection
        client.admin.command('ping')
        
        # Get database
        database = client[db_name]
        
        # Test database access
        database.command('ping')
        
        # Create indexes for better performance
        _create_indexes()
        
        print(f"✅ Successfully connected to MongoDB Atlas - Database: {db_name}")
        return database
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Database connection error: {e}")
        raise e
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e

def _create_indexes():
    """Create database indexes for better performance"""
    try:
        if database is None:
            return
            
        # Translation history collection indexes
        history_collection = database['translation_history']
        
        # Index on uid for faster user queries
        history_collection.create_index("uid")
        
        # Compound index for uid + translation_type
        history_collection.create_index([("uid", 1), ("translation_type", 1)])
        
        # Index on timestamp for sorting
        history_collection.create_index([("timestamp", -1)])
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"⚠️  Warning - Error creating indexes: {e}")

def save_translation_history(translation_data):
    """Save translation history to MongoDB"""
    try:
        db = get_database()
        collection = db['translation_history']
        
        # Add server timestamps
        current_time = datetime.utcnow()
        translation_data['created_at'] = current_time
        translation_data['updated_at'] = current_time
        
        # Ensure timestamp exists
        if 'timestamp' not in translation_data:
            translation_data['timestamp'] = current_time
        
        print(f"💾 Saving translation for user: {translation_data.get('uid')}")
        
        # Insert the document
        result = collection.insert_one(translation_data)
        
        print(f"✅ Translation saved with ID: {result.inserted_id}")
        return result.inserted_id
        
    except Exception as e:
        print(f"❌ Error saving translation: {traceback.format_exc()}")
        return None

def get_user_history(uid, translation_type=None, limit=50):
    """Get user's translation history from MongoDB"""
    try:
        db = get_database()
        collection = db['translation_history']
        
        # Build query
        query = {'uid': uid}
        if translation_type:
            query['translation_type'] = translation_type
        
        print(f"📊 Fetching history for user: {uid}, type: {translation_type}, limit: {limit}")
        
        # Get documents sorted by timestamp (newest first)
        cursor = collection.find(query).sort('timestamp', -1).limit(limit)
        
        # Convert to list and handle ObjectId serialization
        history = []
        for doc in cursor:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            
            # Convert datetime to ISO string for JSON serialization
            for field in ['timestamp', 'created_at', 'updated_at']:
                if field in doc and doc[field]:
                    doc[field] = doc[field].isoformat()
            
            history.append(doc)
        
        print(f"✅ Retrieved {len(history)} history records for user {uid}")
        return history
        
    except Exception as e:
        print(f"❌ Error fetching history: {traceback.format_exc()}")
        return []

def close_connection():
    """Close MongoDB connection"""
    global client, database
    if client:
        client.close()
        client = None
        database = None
        print("✅ MongoDB connection closed")

# Test connection on import
if __name__ != "__main__":
    try:
        get_database()
    except Exception as e:
        print(f"❌ Initial database connection failed: {e}")
