import streamlit as st
from pathlib import Path
import json
from job_recsys.scraper.greenhouse import JobScraper
from job_recsys.embeddings.simple_embedder import get_embeddings
from job_recsys.search.simple_vector_similarity import search_jobs
from job_recsys.summarization.simple_summarizer import summarize_recursive
from job_recsys.resume.extractor import extract_text_from_pdf
from job_recsys.embeddings.embedding_loaders import (
    ResumeEmbeddingLoader,
    JobEmbeddingLoader,
)
from job_recsys.resume.resume_processor import ResumeEmbeddingProcessor

# Directories for saved data
RESUME_EMBEDDINGS_DIR = "./embeddings/resumes"
JOB_EMBEDDINGS_DIR = "./embeddings"

# Initialize loaders and processors
resume_loader = ResumeEmbeddingLoader(RESUME_EMBEDDINGS_DIR)
resume_processor = ResumeEmbeddingProcessor(output_dir=RESUME_EMBEDDINGS_DIR)

st.title("Enhanced Job Recommender")

# Upload and save resume
st.header("Upload Your Resume")
uploaded_file = st.file_uploader("Upload your resume PDF", type=["pdf"])
if uploaded_file is not None:
    file_path = Path(RESUME_EMBEDDINGS_DIR) / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Resume '{uploaded_file.name}' uploaded successfully!")

    # Process and save embeddings
    resume_processor.process_resume(str(file_path))
    st.success("Resume processed and embeddings generated!")

# Select from existing resumes
st.header("Select a Resume")
available_resumes = resume_loader.list_embeddings()
if available_resumes:
    selected_resume = st.selectbox("Choose from uploaded resumes", available_resumes)
    selected_resume_path = Path(RESUME_EMBEDDINGS_DIR) / f"{selected_resume}.json"
else:
    st.warning("No uploaded resumes found!")
    selected_resume = None

# Select companies
st.header("Select Companies")
job_loader = JobEmbeddingLoader(JOB_EMBEDDINGS_DIR)
companies = [
    folder.name for folder in Path(JOB_EMBEDDINGS_DIR).iterdir() if folder.is_dir()
]
selected_companies = st.multiselect("Choose companies", companies)

# Perform vector search and get top 5 job descriptions
if st.button("Find Top Jobs"):
    if not selected_resume:
        st.error("Please select a resume.")
        st.stop()

    if not selected_companies:
        st.error("Please select at least one company.")
        st.stop()

    # Load selected resume embedding
    resume_embedding = resume_loader.load_embedding(selected_resume)
    if not resume_embedding:
        st.error(f"Failed to load embedding for resume: {selected_resume}")
        st.stop()
    resume_embedding_vector = list(resume_embedding["embeddings"].values())[
        0
    ]  # Extract embedding vector

    # Load job embeddings for selected companies
    job_embeddings = job_loader.load_embeddings_for_companies(selected_companies)
    if not job_embeddings:
        st.error("No job embeddings found for the selected companies.")
        st.stop()

    # Extract job descriptions and embeddings
    job_descriptions = [job["description"] for job in job_embeddings]
    job_urls = [job["url"] for job in job_embeddings]
    job_vectors = [job["embedding"] for job in job_embeddings]

    # Perform vector similarity search
    ranked_jobs = search_jobs(resume_embedding_vector, job_vectors)
    top_5 = ranked_jobs[:5]

    # Display top 5 job descriptions
    st.subheader("Top 5 Relevant Jobs")
    for idx, similarity in top_5:
        summary = summarize_recursive(job_descriptions[idx], target_length=350)
        job_url = job_urls[idx]
        st.markdown(f"**Job {idx + 1} (Similarity: {similarity:.2f})**")
        st.write(summary)
        st.write(f"[Job Link]({job_url})")
        st.markdown("---")
