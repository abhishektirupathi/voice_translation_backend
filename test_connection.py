from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_connection():
    try:
        # Get the MongoDB URI from environment variables
        uri = os.getenv('MONGODB_URI')
        print(f"Testing connection with URI: {uri}")
        
        # Create MongoDB client
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test basic connection
        client.admin.command('ping')
        print("✅ Basic connection successful!")
        
        # Test database access
        db = client[os.getenv('DB_NAME', 'voice_translation')]
        print(f"✅ Successfully connected to database: {db.name}")
        
        # Test write operation
        collection = db['test_collection']
        result = collection.insert_one({"test": "data", "timestamp": "2025-08-29"})
        print(f"✅ Write test successful: {result.inserted_id}")
        
        # Test read operation
        found_doc = collection.find_one({"_id": result.inserted_id})
        print(f"✅ Read test successful: {found_doc}")
        
        # Clean up test data
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Test cleanup successful")
        
        # Test collection creation for your app
        history_collection = db['translation_history']
        print(f"✅ History collection ready: {history_collection.name}")
        
        client.close()
        print("✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False
    

if __name__ == "__main__":
    print("=" * 50)
    print("MongoDB Atlas Connection Test")
    print("=" * 50)
    test_connection()
