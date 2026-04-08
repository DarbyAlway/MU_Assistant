import json
import os
from dotenv import load_dotenv
import tiktoken
from tqdm import tqdm
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class SARIndexer:
    def __init__(self, db_path: str = "./sar_db", collection_name: str = "SAR"):
        """
        Initializes the Vector DB client and embedding function.
        
        :param db_path: Path where the ChromaDB persistence data is stored.
        :param collection_name: The name of the collection in the vector database.
        """
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")

        # Initialize Chroma Client
        self.client_db = chromadb.PersistentClient(path=db_path)
        
        # Initialize Embedding Function
        self.embedding_fn = OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-large"
        )

        # Get or Create Collection
        self.collection = self.client_db.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # Tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _chunk_with_overlap(self, text, size=800, overlap=150):
        """Internal helper for token-based chunking."""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= size:
            return [self.tokenizer.decode(tokens)]
        
        chunks = []
        step = size - overlap
        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i : i + size]
            chunks.append(self.tokenizer.decode(chunk_tokens))
            if i + size >= len(tokens):
                break
        return chunks

    def run_ingestion(self, file_path: str):
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return

        # FIX: Create a unique prefix based on filename to prevent overwriting IDs
        file_prefix = os.path.basename(file_path).replace(".", "_")

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(tqdm(lines, desc=f"Indexing {os.path.basename(file_path)}")):
            item = json.loads(line)
            summary = item.get('summarize_content', '')
            questions = " ".join(item.get('related_questions', []))
            url = item.get("url", "N/A")
            content_chunks = self._chunk_with_overlap(item.get('content', ''))

            for c_idx, chunk in enumerate(content_chunks):
                combined_text = f"SUMMARY: {summary}\nQUESTIONS: {questions}\nCONTENT: {chunk}"
                
                # Use file_prefix in the ID
                self.collection.add(
                    ids=[f"{file_prefix}_{idx}_{c_idx}"],
                    documents=[combined_text],
                    metadatas=[{"url": url, "summary": summary, "chunk_index": c_idx}]
                )
        print(f"Success! Collection '{self.collection.name}' now has {self.collection.count()} items.")
        
    def search(self, query: str, n_results: int = 3):
        """
        Queries the collection and prints formatted results.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        print(f"\n" + "="*60)
        print(f"🔎 SEARCHING FOR: {query}")
        print("="*60)

        if not results['documents'] or len(results['documents'][0]) == 0:
            print("No matches found.")
            return results

        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            # Convert cosine distance to a similarity score
            score = 1 - results['distances'][0][i]

            print(f"\n[RANK {i+1}] | Relevance Score: {score:.4f}")
            print(f"🔗 URL: {meta.get('url')}")
            print(f"📝 SUMMARY: {meta.get('summary')[:100]}...")
            # Print a snippet of the actual combined text stored
            print(f"📄 EXCERPT: {doc[:300].replace(chr(10), ' ')}...") 
            print("-" * 40)

        return results

# --- How to use it ---
if __name__ == "__main__":
    # You can specify the DB path and Collection Name here
    indexer = SARIndexer(db_path="./my_vector_store", collection_name="SAR_Collection")
    indexer.run_ingestion(file_path='test.jsonl')
    indexer.search("池田眞朗教授はどのような研究をしているのですか？", n_results=3)
