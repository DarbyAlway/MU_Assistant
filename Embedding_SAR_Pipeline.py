from Embedding_SAR_Chroma import SARIndexer

# Configuration
FRESH_DATA = "./test.jsonl"
UPDATE_DATA = "./test_2.jsonl"
DB_PATH = "./new_sar_system"

def main():
    # --- SCENARIO 1: Create a brand NEW SAR Database ---
    print("\n--- 🆕 Creating New SAR Database ---")
    new_indexer = SARIndexer(db_path=DB_PATH, collection_name="SAR_Collection")
    new_indexer.run_ingestion(file_path=FRESH_DATA)

    # --- SCENARIO 2: Update an OLD SAR Database ---
    print("\n--- 🔄 Updating Existing SAR Database ---")
    # Point to the same path and collection name as before
    existing_indexer = SARIndexer(db_path=DB_PATH, collection_name="SAR_Collection")
    
    # This appends data to the existing vector store
    existing_indexer.run_ingestion(file_path=UPDATE_DATA)
    
    # Search across both old and new data
    existing_indexer.search("池田眞朗教授の研究について教えて", n_results=2)

if __name__ == "__main__":
    main()