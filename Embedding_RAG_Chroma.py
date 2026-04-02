import json
import os
from dotenv import load_dotenv
import tiktoken
from tqdm import tqdm
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# 1. Setup & Config
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

chroma_client = chromadb.PersistentClient(path="./rag_db")
embedding_function = OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-large"
)

collection = chroma_client.get_or_create_collection(
    name="RAG", 
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}

)

tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_text_with_overlap(text, max_tokens=800, overlap=100):
    """Splits text into overlapping chunks."""
    tokens = tokenizer.encode(text)
    chunks = []
    
    if len(tokens) <= max_tokens:
        return [tokenizer.decode(tokens)]

    step = max_tokens - overlap
    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i : i + max_tokens]
        chunks.append(tokenizer.decode(chunk_tokens))
        # Stop if we've reached the end of the text
        if i + max_tokens >= len(tokens):
            break
    return chunks

# 2. Processing Data
file_path = 'merged.jsonl'
with open(file_path, 'r', encoding='utf-8') as f:
    total_lines = sum(1 for _ in f)

with open(file_path, 'r', encoding='utf-8') as f:
    for line_idx, line in enumerate(tqdm(f, total=total_lines, desc="Indexing with Overlap")):
        item = json.loads(line)
        full_text = item['content']
        url = item.get("url", "No URL")
        
        # Create overlapping chunks
        chunks = chunk_text_with_overlap(full_text, max_tokens=800, overlap=150)
        
        ids = [f"id_{line_idx}_{c_idx}" for c_idx in range(len(chunks))]
        metadatas = [{"url": url, "chunk_index": i} for i in range(len(chunks))]
        
        # ChromaDB handles the API calls for embeddings automatically
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

print(f"\nSuccess! Indexed {collection.count()} overlapping chunks.")