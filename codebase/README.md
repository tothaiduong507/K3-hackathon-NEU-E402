# Paper2Venue backend

Backend prototype for a research assistant that:

1. searches and transparently ranks scholarly papers;
2. creates an abstract-grounded comparison and research-gap brief for a topic;
3. extracts text from an arXiv PDF for a single-paper deep dive;
4. produces structured, evidence-linked summaries with real model calls;
5. recommends a shortlist of conferences from a source-controlled catalog.

The backend deliberately does not predict acceptance probability and does not
invent conference deadlines. Conference URLs and scope metadata always come
from `data/conferences.json`, never from model output.

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill one model key in `.env`. `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are
currently supported. A Semantic Scholar key is optional but recommended. If
Semantic Scholar is throttled or unavailable, search falls back to arXiv.
Exact `ARXIV:<id>` lookups use the same fallback for 403/429 responses.

## Streamlit demo

The demo UI follows the submitted four-frame wireframe: search and filter,
pipeline progress, ranked paper summaries, then conference recommendations.

```powershell
streamlit run streamlit_app.py
```

Open `http://localhost:8501`, select a sample topic or enter a research query,
then choose **Thực thi AI Pipeline**. Keep minimum citations at `0` when the
app is using arXiv fallback because arXiv does not return citation counts.

Each result with an arXiv ID also includes **Đọc và tóm tắt toàn bài**. This
opens the Deep Paper Summary screen, downloads up to 80 PDF pages, summarizes
section-sized chunks, and performs a second synthesis pass. The result includes
methodology, datasets, experiments, findings, limitations, section summaries,
key takeaways, glossary entries, and validated page references. Results are
cached by PDF content, language, model, and prompt version.

The UI intentionally does not show fabricated deadlines or acceptance
probabilities. Every completed run can be downloaded as Markdown or JSON and is
also saved under `runs/`.

## Commands

Search for papers:

```powershell
python -m paper2venue.cli search "retrieval augmented generation" --limit 5
```

Search and show the transparent relevance ranking without spending a model call:

```powershell
python -m paper2venue.cli rank "retrieval augmented generation" --limit 10
```

Create a Smart Literature Review from the top results:

```powershell
python -m paper2venue.cli review "retrieval augmented generation" --search-limit 10 --analyze-top 3
```

The batch review intentionally uses abstracts and labels that evidence level in
the output. Use `brief --paper-id` for a deeper arXiv PDF-based summary.

Build a brief from the first search result:

```powershell
python -m paper2venue.cli brief --query "retrieval augmented generation" --select 1
```

Build a brief directly from an abstract:

```powershell
python -m paper2venue.cli brief --title "My paper" --abstract-file sample-abstract.txt
```

Build a brief from an exact DOI or arXiv ID:

```powershell
python -m paper2venue.cli brief --paper-id "ARXIV:2005.11401"
python -m paper2venue.cli brief --paper-id "DOI:10.xxxx/example"
```

Choose another model provider:

```powershell
python -m paper2venue.cli --provider openrouter brief --query "vision transformer"
```

Every successful brief is saved as JSON and Markdown under `runs/`.

## Tests

Tests do not call external APIs:

```powershell
python -m unittest discover -s tests -v
```

Run the deterministic catalog/golden-set evaluation:

```powershell
python ..\eval\run_catalog_eval.py
python ..\eval\run_ranking_eval.py
```

## Source and confidence boundaries

- Paper metadata is returned with the Semantic Scholar URL and external IDs.
- A summary is marked `abstract_only` unless arXiv full text was extracted.
- Evidence references are restricted to labels actually supplied to the model,
  such as `[abstract]` and `[p.3]`.
- Conference IDs and URLs in the final output are resolved from the local
  catalog. Model-provided URLs are ignored.
- Deadlines are intentionally absent until a separately verified deadline
  source is implemented.
- The recommendation is a scope-fit shortlist, not an acceptance forecast.
