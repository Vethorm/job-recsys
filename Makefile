ui:
	uv run streamlit run streamlit/main.py

list-companies:
	uv run run-job-spiders --list-companies --registry configs/job_sites.yml

run-scraper:
	uv run run-job-spiders --registry configs/job_sites.yml