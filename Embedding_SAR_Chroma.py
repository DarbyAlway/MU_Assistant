import json
import os
from dotenv import load_dotenv
import tiktoken
from tqdm import tqdm
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# 1. Configuration
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_db = chromadb.PersistentClient(path="./sar_db")

embedding_fn = OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-large"
)

collection = client_db.get_or_create_collection(
    name="SAR",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_with_overlap(text, size=800, overlap=150):
    tokens = tokenizer.encode(text)
    if len(tokens) <= size:
        return [tokenizer.decode(tokens)]
    
    chunks = []
    step = size - overlap
    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i : i + size]
        chunks.append(tokenizer.decode(chunk_tokens))
        if i + size >= len(tokens):
            break
    return chunks

# 2. Ingestion Loop
file_path = 'merged.jsonl'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(tqdm(lines, desc="SAR Indexing")):
    item = json.loads(line)
    
    # Extract specific SAR fields
    summary = item.get('summarize_content', '')
    questions = " ".join(item.get('related_questions', []))
    url = item.get("url", "N/A")
    
    # We chunk the MAIN content
    content_chunks = chunk_with_overlap(item['content'], size=800, overlap=150)

    for c_idx, chunk in enumerate(content_chunks):
        # CHANGE: We combine Summary + Questions + Content Chunk into the searchable 'document'
        # This makes the chunk highly relevant to the summary/questions during search.
        combined_search_text = (
            f"SUMMARY: {summary}\n"
            f"QUESTIONS: {questions}\n"
            f"CONTENT: {chunk}"
        )
        
        collection.add(
            ids=[f"sar_{idx}_{c_idx}"],
            documents=[combined_search_text],
            metadatas=[{
                "url": url,
                "summary": summary,
                "chunk_index": c_idx,
                # Optionally keep the clean chunk here for pure display
                "clean_content": chunk 
            }]
        )

print(f"\nSuccess! Total records in SAR collection: {collection.count()}")