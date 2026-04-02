import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

class MusashinoAssistant_RAG:
    def __init__(self):
        # 1. Setup OpenAI Client
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        
        # 2. Setup ChromaDB
        # Point this to the directory where you saved your SAR/RAG data
        self.chroma_client = chromadb.PersistentClient(path="./rag_db")
        
        # Define the embedding function so Chroma can vectorize your queries automatically
        self.embedding_fn = OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-large"
        )
        
        # Get the existing collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="RAG",
            embedding_function=self.embedding_fn
        )

    def get_answer(self, user_query, language='japanese'):
        # 1. RETRIEVAL (Search ChromaDB)
        results = self.collection.query(
            query_texts=[user_query],
            n_results=4,
            include=["documents", "metadatas"]
        )
        print('query: ',user_query)

        # 2. AUGMENTATION
        reference_text = ""
        source_urls = [] # List to store clean URLs for the frontend

        for i in range(len(results['documents'][0])):
            doc_text = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            print(f"DEBUG: Metadata keys found: {meta.keys()}")
            # Get URL and add to our source list if it's not a duplicate
            url = meta.get('url', 'N/A')
            if url != 'N/A' and url not in source_urls:
                source_urls.append(url)

            reference_text += f"\n[Source URL]: {url}\n"
            
            content = meta.get('clean_content', doc_text)
            reference_text += f"[Content Chunk]: {content}\n"
            reference_text += "---------------------------\n"

        # 3. GENERATION
        system_prompt = f"""
        あなたは武蔵野大学（Musashino University）の公式アシスタントです。
        学生や利用者からの質問に対して、丁寧かつ分かりやすく回答してください。
        回答は提供されたコンテキストに基づいて行ってください。
        もし答えが分からない場合は、分からないと正直に伝えてください。
        また、毎回の回答の最後に、追加の質問を歓迎する一文を添えてください。
        以下の取得されたコンテキストを使用して質問に答えてください。
        回答は簡潔に{language}で行ってください。
        """

        user_prompt = f"[Reference Materials]:\n{reference_text}\n\nUser Question: {user_query}"

        response = self.client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        
        # Return both the text answer and the clean list of URLs
        return response.choices[0].message.content, source_urls

# Test execution
if __name__ == "__main__":
        assistant = MusashinoAssistant_RAG()
        # Example question: "What is the founding spirit of Musashino University?"
        answer,source_urls = assistant.get_answer("what is the email of this university")
        print(answer)
        print(source_urls)