## Setup Instructions

Follow these steps to run the project.

### 1. Set Your OpenAI API Key

You need an OpenAI API key to run the system.

Create a `.env` file in the project root and add your API key as a variable:

```
OPENAI_API_KEY=your_openai_api_key_here
```

---

### 2. Download the Vector Databases

Download the required vector databases from the following links:

* **SAR Vector Database**
  https://drive.google.com/drive/folders/1mq15KU2ieUmLJK63DdhDb9IzSTH_8e80?usp=sharing
* **RAG Vector Database**
  https://drive.google.com/drive/folders/1WVeW0gmiWsyrdvdMSJB6B-AX49WmahXe?usp=sharing
---

### 3. Place the Databases in the Project

After downloading:


Your folder structure should look like this:

```
project_root/
│
├── chroma_rag_storage/        # Vector database for RAG
├── chroma_sar_storage/        # Vector database for SAR
│
├── frontend/                  # Frontend interface
│
├── Embedding_RAG_Chroma.py    # Create RAG embeddings using Chroma
├── Embedding_RAG.py           # RAG embedding pipeline
├── Embedding_SAR_Chroma.py    # Create SAR embeddings using Chroma
├── Embedding_SAR.py           # SAR embedding pipeline
│
├── main.py                    # Main program entry point
├── QAGenerator.py             # Question generation script
├── RAG.py                     # Retrieval-Augmented Generation system
├── SAR.py                     # Semantic Answer Retrieval system
├── summarizer.py              # Text summarization utility
│
└── README.md
```


## Environment Setup

Create the conda environment:
```
conda env create -f environment.yml
conda activate scraper
```
then start the main.py `python main.py`
