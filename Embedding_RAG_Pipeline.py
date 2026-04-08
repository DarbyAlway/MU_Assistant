from Embedding_RAG_Chroma import RAGIndexer

OLD_DATA_PATH = "./test.jsonl"
NEW_DATA_PATH = "./test_2.jsonl"
DB_PATH = "./project_db"
def main():
    # Point to a path that DOES NOT exist yet
    print("\n--- 🆕 Creating New Database ---")
    new_db_indexer = RAGIndexer(db_path=DB_PATH, collection_name="NewProject")
    
    # Ingest data into the empty store
    new_db_indexer.run_ingestion(file_path=OLD_DATA_PATH)
    
    # Verify by searching

    # --- Update the OLD Database ---
    # Point to the EXACT folder path where your old data lives
    print("--- 🔄 Updating Old Database ---")
    old_db_path = "./my_old_vector_store"
    old_db_indexer = RAGIndexer(db_path=DB_PATH, collection_name="NewProject")
    
    # Add new data (Appends to existing vectors)
    old_db_indexer.run_ingestion(file_path=NEW_DATA_PATH)
    
    # Verify by searching
    old_db_indexer.search("この学科での主な授業内容はどのようなものですか？", n_results=2)


 

if __name__ == "__main__":
    main()