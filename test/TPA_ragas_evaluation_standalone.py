import os

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness, context_precision, context_recall
from datasets import Dataset
from dotenv import load_dotenv

# Load API key
load_dotenv()

# -----------------------------
# Setup RAG Chain with Chroma
# -----------------------------
def setup_rag_with_chroma():
    embedding_model = OpenAIEmbeddings()
    
    vector_store = Chroma(persist_directory="../chroma_db", embedding_function=embedding_model)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

qa_chain = setup_rag_with_chroma()

# -----------------------------
# Define Evaluation Examples
# -----------------------------
examples = [
    {
        "question": "I need unlimited data with the best 5G coverage",
        "ground_truth": "Verizon’s Unlimited Ultimate plan offers truly unlimited data and supports 5G Ultra Wideband, providing the best coverage and speed."
    },
    {
        "question": "What's the cheapest Verizon plan with hotspot?",
        "ground_truth": "The cheapest Verizon plan with hotspot is the Unlimited Plus plan, which includes 30GB of hotspot data."
    },
    {
        "question": "Compare plans for a family of 4 with heavy streaming",
        "ground_truth": "Unlimited Plus and Unlimited Ultimate are suitable. Plus offers 30GB hotspot and 5G UW, Ultimate adds 60GB hotspot and more features. Multi-line discounts apply."
    },
    {
        "question": "Which plan includes Disney+ or Netflix?",
        "ground_truth": "Most Verizon plans no longer include Disney+ or Netflix by default. Unlimited Ultimate offers Apple One and streaming via +play credits, but bundles may change with promotions."
    },
    {
        "question": "Best plan for gaming and streaming under $85/month",
        "ground_truth": "Unlimited Plus is under $85/month, includes 30GB hotspot, premium data, and 5G Ultra Wideband — good for streaming and gaming."
    },
    {
        "question": "I travel internationally - which plan has the best roaming?",
        "ground_truth": "Unlimited Ultimate includes international calling, texting, and roaming in 210+ countries with high-speed access in select regions."
    }
]

# -----------------------------
# Run Evaluation
# -----------------------------
def evaluate_rag_pipeline():
    test_results = []
    for ex in examples:
        print(f"\nEvaluating: {ex['question']}")
        response = qa_chain(ex['question'])
        answer = response['result']
        source_chunks = [doc.page_content for doc in response['source_documents']]

        test_results.append({
            "question": ex["question"],
            "answer": answer,
            "contexts": source_chunks,
            "ground_truth": ex["ground_truth"]
        })

    dataset = Dataset.from_list(test_results)

    scored = evaluate(
        dataset,
        metrics=[answer_relevancy, faithfulness, context_precision, context_recall]
    )

    print("\nEvaluation Scores:")
    print(scored.to_pandas())
    scored.to_pandas().to_csv("./reports/TPA_ragas_evaluation_standalone_report.csv", index=False)

if __name__ == "__main__":
    evaluate_rag_pipeline()
