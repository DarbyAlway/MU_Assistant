import json
import os
from dotenv import load_dotenv
import tiktoken
from tqdm import tqdm
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class RAGIndexer:
    def __init__(self, db_path: str = "./rag_db", collection_name: str = "RAG"):
        """
        Initializes the RAG Indexer with database and collection configurations.
        
        :param db_path: Local directory for the Persistent Chroma client.
        :param collection_name: The name of the collection to get or create.
        """
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API Key not found. Please check your .env file.")

        # 1. Setup & Config
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-large"
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _chunk_text_with_overlap(self, text, max_tokens=800, overlap=100):
        """Internal helper: Splits text into overlapping chunks based on tokens."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        if len(tokens) <= max_tokens:
            return [self.tokenizer.decode(tokens)]

        step = max_tokens - overlap
        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i : i + max_tokens]
            chunks.append(self.tokenizer.decode(chunk_tokens))
            if i + max_tokens >= len(tokens):
                break
        return chunks

    def run_ingestion(self, file_path: str, max_tokens: int = 800, overlap: int = 150):
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return

        # --- FIX: Create a unique tag based on the filename ---
        # e.g., 'test_2.jsonl' becomes 'test_2_jsonl'
        file_tag = os.path.basename(file_path).replace(".", "_")

        with open(file_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(tqdm(f, total=total_lines, desc=f"Indexing {file_path}")):
                item = json.loads(line)
                full_text = item.get('content', '')
                url = item.get("url", "No URL")
                
                chunks = self._chunk_text_with_overlap(full_text, max_tokens=max_tokens, overlap=overlap)
                
                # --- FIX: Use the file_tag in the ID ---
                ids = [f"{file_tag}_{line_idx}_{c_idx}" for c_idx in range(len(chunks))]
                
                metadatas = [{"url": url, "chunk_index": i} for i in range(len(chunks))]
                
                self.collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )

        print(f"\nSuccess! Total entries in '{self.collection.name}': {self.collection.count()}")
        
    def search(self, query: str, n_results: int = 3):
        """
        Queries the vector database and prints the results in a readable format.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        print(f"\n" + "="*50)
        print(f"🔍 SEARCH QUERY: {query}")
        print("="*50)

        # Check if we actually got results
        if not results['documents'] or len(results['documents'][0]) == 0:
            print("No relevant documents found.")
            return results

        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            
            # Converting distance to a similarity score (higher is better)
            score = 1 - dist

            print(f"\n[RESULT #{i+1}] | Score: {score:.4f}")
            print(f"🔗 URL: {meta.get('url', 'N/A')}")
            print(f"📄 CONTENT: {doc[:300]}...") # Printing first 300 chars for brevity
            print("-" * 30)

        return results
# --- Execution Example ---
if __name__ == "__main__":
    # Initialize the class with your preferred DB path and Collection name
    indexer = RAGIndexer(db_path="./my_vector_store", collection_name="Test_RAG")
    indexer.search("グローバル学部の入試結果についてもう少し詳しく教えてください", n_results=2)    
    # Execute the ingestion by passing the file path
    # indexer.run_ingestion(file_path='test_2.jsonl')