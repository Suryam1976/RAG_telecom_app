import streamlit as st
import pandas as pd
import os
import io

from datasets import Dataset
from ragas.metrics import answer_relevancy, faithfulness, context_precision, context_recall
from ragas import evaluate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TAP Reliability Evaluation Dashboard", layout="wide")

st.title("📊 TAP Reliability Evaluation Dashboard")

@st.cache_resource
def load_qa_chain():
    embedding = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory="../chroma_db", embedding_function=embedding)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

qa_chain = load_qa_chain()

uploaded_file = st.file_uploader("📂 Upload JSONL test file", type=["jsonl"])
if uploaded_file:
    uploaded_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    df = pd.read_json(io.BytesIO(uploaded_bytes), lines=True)
    dataset = df.to_dict(orient="records")

    results = []
    with st.spinner("Running evaluation..."):
        for row in dataset:
            query = row["question"]
            ground = row["ground_truth"]
            rag_output = qa_chain(query)
            answer = rag_output["result"]
            sources = [doc.page_content for doc in rag_output["source_documents"]]
            results.append({
                "question": query,
                "answer": answer,
                "contexts": sources,
                "ground_truth": ground
            })

        test_dataset = pd.DataFrame(results)
        ragas_dataset = Dataset.from_list(results)

        evaluated = evaluate(
            ragas_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )
        df = evaluated.to_pandas()

        st.subheader("📈 Evaluation Results")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", data=csv, file_name="./reports/TPA_streamlit_rag_dashboard_report.csv", mime="text/csv")
