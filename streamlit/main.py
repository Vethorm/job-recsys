import streamlit as st
from job_recsys.scraper.greenhouse import JobScraper
from job_recsys.resume.extractor import extract_text_from_pdf
from job_recsys.embeddings.simple_embedder import get_embeddings
from job_recsys.search.simple_vector_similarity import search_jobs
from job_recsys.summarization.simple_summarizer import summarize_recursive

job_board = (
    "https://boards-api.greenhouse.io/v1/boards/andurilindustries/jobs?content=true"
)

st.title("Job Recommender")

# Resume PDF uploader
uploaded_file = st.file_uploader("Upload your resume PDF", type=["pdf"])

if uploaded_file is not None:
    resume_text = extract_text_from_pdf(uploaded_file)
else:
    # Fallback to a local resume file
    resume = "data/Software_Engineering_2.pdf"
    resume_text = extract_text_from_pdf(resume)

with st.expander("Resume text"):
    st.write(resume_text)

# Initialize the scraper
scraper = JobScraper(job_board)

# Get unique department prefixes and allow the user to select one
dept_prefixes = sorted(list(scraper.get_unique_department_prefixes()))
selected_prefix = st.selectbox(
    "Select department prefix to search for jobs:", dept_prefixes, index=0
)

# Add a button to trigger the job search
if st.button("Search Jobs"):
    # Get jobs with the selected department prefix
    jobs = scraper.get_jobs_by_department(selected_prefix)[:50]
    if not jobs:
        st.warning("No jobs found for the selected department prefix.")
        st.stop()

    # For each job, scrape its description and keep track of the URL
    job_descriptions = []
    job_urls = []
    for job in jobs:
        url = job.get("absolute_url")
        try:
            description = scraper.scrape_job_description(url)
            job_descriptions.append(description)
            job_urls.append(url)
        except Exception as e:
            st.error(f"Error processing job {job.get('title')}: {e}")

    if not job_descriptions:
        st.warning("No job descriptions could be fetched.")
        st.stop()

    # Compute embeddings for the resume and the job descriptions
    resume_embedding = get_embeddings(resume_text)[0]
    job_embeddings = get_embeddings(job_descriptions)

    # Perform vector search to rank jobs by similarity to the resume
    ranked_jobs = search_jobs(resume_embedding, job_embeddings)
    top_5 = ranked_jobs[:5]

    st.subheader("Top 5 Relevant Jobs")
    for idx, similarity in top_5:
        # Summarize the job description text
        summary = summarize_recursive(job_descriptions[idx], target_length=350)
        job_url = job_urls[idx]
        st.markdown(f"**Job {idx + 1} (Similarity: {similarity:.2f})**")
        st.write(summary)
        st.write(f"[Job Link]({job_url})")
        st.markdown("---")
