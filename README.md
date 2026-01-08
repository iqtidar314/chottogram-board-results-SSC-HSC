# HSC Result Scraper - High Volume

A highly efficient, asynchronous Python scraper designed to fetch ~900,000 HSC results using GitHub Actions Matrix Strategy.

## Features
- **High Concurrency**: Uses `asyncio` and `curl_cffi` for fast, non-blocking requests.
- **Stealth**: Impersonates Chrome browser TLS fingerprints to avoid detection.
- **Scalable**: GitHub Actions workflow splits the load into 20 parallel workers, reducing total time from days to ~1.5 hours.
- **Robust**: Automatic retries and error handling.
- **Smart Output**: Skips "No Result Found" entries to save space.

## Project Structure
- `scraper.py`: Main script.
- `.github/workflows/scrape.yml`: Automation configuration.
- `requirements.txt`: Dependencies.

## How to Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Scraper**:
   ```bash
   # Example: Scrape rolls 100000 to 100050
   python scraper.py --start 100000 --end 100050 --output my_results.csv
   ```

## Output Format
The `results.csv` contains detailed information:
- **Personal Info**: Roll, Name, Board, Father/Mother Name, Group, Session, Reg No, Type, Institute, Result, GPA.
- **Subjects**: A JSON string column `subjects_json` containing all subject marks (e.g., `{"BANGLA(101)": "A (156)"}`).

## deploying to GitHub Actions (Free)

1. **Push to GitHub**:
   - Initialize a git repo and push all files.
   
2. **Trigger Workflow**:
   - Go to **Actions** tab in your repository.
   - Select **Bulk Scraper Matrix**.
   - Click **Run workflow**.

3. **Download Results**:
   - Once completed, go to the run summary.
   - Download the `results-chunk-x` artifacts at the bottom.

## Configuration
- **Concurrency**: Adjust `MAX_CONCURRENT_REQUESTS` in `scraper.py`.
- **Matrix Size**: Adjust `chunk` list in `.github/workflows/scrape.yml`.
