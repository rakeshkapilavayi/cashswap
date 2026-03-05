import pandas as pd
from pathlib import Path
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

faqs_path = Path(__file__).parent/"resources"/"cashswap_chatbot_faq.csv"
chroma_client = chromadb.EphemeralClient()
collection_name_faq = "faqs"

ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()

def ingest_faq_data(path):
    if collection_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print('Ingesting data into collection...')
        collection = chroma_client.get_or_create_collection(name=collection_name_faq,
        embedding_function=ef
        )
        df = pd.read_csv(path)
        docs = df["question"].tolist()
        metadatas = [{'answer': ans} for ans in df['answer'].tolist()]
        ids = [f'id_{i}' for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingested {len(docs)} FAQ entries into collection {collection_name_faq}.")
    else:
        print(f"Collection {collection_name_faq} already exists. Skipping ingestion.")

def get_relevant_faqs(query):
    collection = chroma_client.get_collection(name=collection_name_faq)
    results = collection.query(
        query_texts=[query],
        n_results=2
    )
    return results

def faq_chain(query):
    result = get_relevant_faqs(query)
    context = ''.join([r.get('answer') for r in result['metadatas'][0]])
    answer = generate_answer(query, context)
    return answer

def generate_answer(query, context):

    prompt = f'''
    Given the question and context below, generate the answer based on the context only.If you don't find the answer inside the context then say "I don't know".
    Do not make things up.

    QUESTION: {query}
    CONTEXT: {context}
    '''
    groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = groq.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model=os.getenv("GROQ_MODEL")
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    ingest_faq_data(faqs_path)
    query = "what is cash swap?"
    results = get_relevant_faqs(query)
    
    answer = faq_chain(query)
    print(answer)
