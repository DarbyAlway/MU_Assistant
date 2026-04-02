import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
load_dotenv()

class MusashinoAssistant_SAR:
    def __init__(self):
        # 1. Setup OpenAI Client
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        
        # 2. Setup ChromaDB
        # Point this to the directory where you saved your SAR/RAG data
        self.chroma_client = chromadb.PersistentClient(path="./sar_db")
        
        # Define the embedding function so Chroma can vectorize your queries automatically
        self.embedding_fn = OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-large"
        )
        
        # Get the existing collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="SAR",
            embedding_function=self.embedding_fn
        )

    def get_answer(self, user_query, language='japanese'):
        # 1. RETRIEVAL (Search ChromaDB)
        results = self.collection.query(
            query_texts=[user_query],
            n_results=4,
            include=["documents", "metadatas"]
        )

        # 2. AUGMENTATION
        reference_text = ""
        source_urls = [] # List to store clean URLs for the frontend

        for i in range(len(results['documents'][0])):
            doc_text = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            
            # Get URL and add to our source list if it's not a duplicate
            url = meta.get('url', 'N/A')
            if url != 'N/A' and url not in source_urls:
                source_urls.append(url)

            reference_text += f"\n[Source URL]: {url}\n"
            
            if 'summary' in meta:
                reference_text += f"[Document Summary]: {meta['summary']}\n"
            
            content = meta.get('clean_content', doc_text)
            reference_text += f"[Content Chunk]: {content}\n"
            reference_text += "---------------------------\n"

        # 3. GENERATION
        system_prompt = f"""
        ### 役割 (Role)
        あなたは武蔵野大学（Musashino University）の親切で正確な事務助手です。
        学生、保護者、または入学希望者からの質問に対し、提供された資料に基づいてサポートを提供することが任務です。

        ### 制限事項 (Constraints)
        1. **資料の厳守**: 回答は、以下の「参考資料」にある情報のみに基づき作成してください。資料にない情報は「申し訳ありませんが、その件に関する正確な情報が見当たりませんでした」と丁寧に伝えてください。
        2. **推測の禁止**: 自分の知識や外部の情報を使って回答を捏造しないでください。
        3. **言語指定**: 回答は必ず {language} で行ってください。
        4. **トーン**: 丁寧で公式な大学窓口のような口調（敬語）を保ってください。

        ### 回答の構成 (Structure)
        - 質問に対する直接的な回答を最初に述べます。
        - 詳細な説明が必要な場合は、箇条書きを活用して読みやすくしてください。
        - 関連する窓口や部署名が資料にある場合は、それを案内してください。
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
    assistant = MusashinoAssistant_SAR()
    # Example question: "What is the founding spirit of Musashino University?"
    answer,url = assistant.get_answer("what is the email of this university")
    print(answer)
    print(url)

    