import asyncio
import argparse
import csv
import os
import random
from curl_cffi import requests as crequests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import time

# Constants
BASE_URL = "https://hscresult.bise-ctg.gov.bd/h_x_y_ctg25/individual/result_mark_details.php"
MAX_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 5
RETRY_DELAY = 1

# Pre-defined known subjects for clean columns (Science/Arts/Commerce)
KNOWN_SUBJECTS = [
    # Compulsory
    "BANGLA(101)", "BANGLA(102)",
    "ENGLISH(107)", "ENGLISH(108)",
    "INFORMATION & COMMUNICATION TECHNOLOGY(275)",
    
    # Science
    "PHYSICS(174)", "PHYSICS(175)",
    "CHEMISTRY(176)", "CHEMISTRY(177)",
    "BIOLOGY(178)", "BIOLOGY(179)",
    "HIGHER MATHEMATICS(265)", "HIGHER MATHEMATICS(266)",
    "STATISTICS(129)", "STATISTICS(130)",
    "PSYCHOLOGY(123)", "PSYCHOLOGY(124)",
    
    # Commerce
    "ACCOUNTING(253)", "ACCOUNTING(254)", 
    "BUSINESS ORGANIZATION & MANAGEMENT(277)", "BUSINESS ORGANIZATION & MANAGEMENT(278)",
    "FINANCE, BANKING & INSURANCE(292)", "FINANCE, BANKING & INSURANCE(293)",
    "PRODUCTION MANAGEMENT & MARKETING(286)", "PRODUCTION MANAGEMENT & MARKETING(287)",
    
    # Arts/Humanities
    "ECONOMICS(109)", "ECONOMICS(110)",
    "CIVICS & GOOD GOVERNANCE(269)", "CIVICS & GOOD GOVERNANCE(270)",
    "LOGIC(121)", "LOGIC(122)",
    "SOCIOLOGY(117)", "SOCIOLOGY(118)",
    "SOCIAL WORK(271)", "SOCIAL WORK(272)",
    "GEOGRAPHY(125)", "GEOGRAPHY(126)",
    "HISTORY(304)", "HISTORY(305)",
    "ISLAMIC HISTORY & CULTURE(267)", "ISLAMIC HISTORY & CULTURE(268)",
    "ISLAMIC STUDIES(249)", "ISLAMIC STUDIES(250)",
    "HOME SCIENCE(273)", "HOME SCIENCE(274)",
    "AGRICULTURAL STUDIES(239)", "AGRICULTURAL STUDIES(240)",
    
    # Others/Optionals potentially appearing (just in case)
    "ARTS & CRAFTS(225)",
]

# Build a lookup map: Code -> Standard Column Name
# e.g., "101" -> "BANGLA(101)"
import re
SUBJECT_CODE_MAP = {}
for subj in KNOWN_SUBJECTS:
    match = re.search(r"\((\d+)\)", subj)
    if match:
        code = match.group(1)
        SUBJECT_CODE_MAP[code] = subj

async def fetch_result(session, roll, semaphore, writer, file_handle):
    async with semaphore:
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Random small delay
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Payload
                data = {
                    "roll": str(roll),
                    "button2": "Submit"
                }
                
                # Extended timeout
                response = await session.post(
                    BASE_URL, 
                    data=data, 
                    impersonate="chrome120", 
                    timeout=30 
                )
                
                if response.status_code == 200:
                    text = response.text
                    
                    if "Sorry! No Result Found" in text:
                        return

                    soup = BeautifulSoup(text, 'html.parser')
                    
                    try:
                        # Extract Personal Info Table
                        info_table = soup.select_one("table.tftable")
                        if not info_table:
                            print(f"[WARN] {roll} - Info table not found.")
                            return

                        def get_text(row_idx, col_idx):
                            el = info_table.select_one(f"tr:nth-child({row_idx}) > td:nth-child({col_idx})")
                            return el.get_text(strip=True) if el else ""

                        # Row 1-6
                        val_roll = get_text(1, 2)
                        val_name = get_text(1, 4)
                        val_board = get_text(2, 2)
                        val_father = get_text(2, 4)
                        val_group = get_text(3, 2)
                        val_mother = get_text(3, 4)
                        val_session = get_text(4, 2)
                        val_reg = get_text(4, 4)
                        val_type = get_text(5, 2)
                        val_institute = get_text(5, 4)
                        val_result = get_text(6, 2)
                        val_gpa = get_text(6, 4)

                        # Extract Subjects
                        subjects_data = {}
                        other_subjects = []
                        
                        subject_table = soup.select_one("table.tftable2")
                        if subject_table:
                            rows = subject_table.find_all("tr")[1:] 
                            for row in rows:
                                cols = row.find_all("td")
                                if len(cols) >= 2:
                                    sub_name_raw = cols[0].get_text(strip=True) # e.g. "BANGLA 1ST(101)"
                                    sub_marks = cols[1].get_text(strip=True)
                                    
                                    # Normalize Logic: Match by Code first
                                    # Extract code from raw string "Foo(101)" -> "101"
                                    code_match = re.search(r"\((\d+)\)", sub_name_raw)
                                    target_col = None
                                    
                                    if code_match:
                                        found_code = code_match.group(1)
                                        if found_code in SUBJECT_CODE_MAP:
                                            target_col = SUBJECT_CODE_MAP[found_code]
                                    
                                    # Fallback to exact match (rarely needed if code works) in case format differs
                                    if not target_col and sub_name_raw in KNOWN_SUBJECTS:
                                         target_col = sub_name_raw

                                    if target_col:
                                        subjects_data[target_col] = sub_marks
                                    else:
                                        # Unknown code/subject -> Add to others
                                        other_subjects.append(f"{sub_name_raw}:{sub_marks}")
                        
                        record = {
                            "roll": roll,
                            "name": val_name,
                            "board": val_board,
                            "father_name": val_father,
                            "mother_name": val_mother,
                            "group": val_group,
                            "session": val_session,
                            "reg_no": val_reg,
                            "type": val_type,
                            "institute": val_institute,
                            "result": val_result,
                            "gpa": val_gpa,
                        }
                        
                        # Merge known subjects
                        for subj in KNOWN_SUBJECTS:
                            record[subj] = subjects_data.get(subj, "")
                            
                        # Add overflow
                        record["others"] = " | ".join(other_subjects)

                        if val_name:
                            print(f"[SUCCESS] {roll} - {val_name} - GPA: {val_gpa}")
                            writer.writerow(record)
                            file_handle.flush()
                            return
                            
                    except Exception as e:
                        print(f"[PARSE ERROR] {roll}: {e}")
                    
                    return

                elif response.status_code in [500, 502, 503, 504]:
                    print(f"[RETRY] {roll} - Status {response.status_code}")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                else:
                    print(f"[FAIL] {roll} - Status {response.status_code}")
                    return

            except Exception as e:
                # Handle timeout specifically
                if "timed out" in str(e).lower():
                     print(f"[TIMEOUT] {roll} - Attempt {attempt}")
                else:
                    print(f"[ERR] {roll} - Attempt {attempt}: {e}")
                
                await asyncio.sleep(RETRY_DELAY)
        
        print(f"[GIVEUP] {roll} - Max retries reached.")

async def main():
    parser = argparse.ArgumentParser(description="HSC Results Scraper")
    parser.add_argument("--start", type=int, required=True, help="Start Roll Number")
    parser.add_argument("--end", type=int, required=True, help="End Roll Number")
    parser.add_argument("--output", type=str, default="results.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    start_roll = args.start
    end_roll = args.end
    output_file = args.output
    
    print(f"Starting Scraper: {start_roll} to {end_roll} -> {output_file}")
    
    # Setup CSV
    file_exists = os.path.isfile(output_file)
    with open(output_file, mode='a', newline='', encoding='utf-8') as f:
        # Full field list
        fieldnames = [
            'roll', 'name', 'board', 'father_name', 'mother_name', 
            'group', 'session', 'reg_no', 'type', 'institute', 
            'result', 'gpa'
        ] + KNOWN_SUBJECTS + ['others']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        
        if not file_exists:
            writer.writeheader()
            
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with AsyncSession() as session:
            tasks = []
            for roll in range(start_roll, end_roll + 1):
                task = asyncio.create_task(fetch_result(session, roll, semaphore, writer, f))
                tasks.append(task)
            
            await asyncio.gather(*tasks)

    print("Scraping Completed.")

if __name__ == "__main__":
    asyncio.run(main())
