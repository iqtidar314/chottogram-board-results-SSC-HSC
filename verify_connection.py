from curl_cffi import requests
from bs4 import BeautifulSoup

def test_scrape(roll):
    url = "https://hscresult.bise-ctg.gov.bd/h_x_y_ctg25/individual/result_mark_details.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "roll": str(roll),
        "button2": "Submit"
    }
    
    print(f"Testing roll: {roll}")
    try:
        response = requests.post(url, data=data, headers=headers, impersonate="chrome120", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for "No Result Found"
            if "Sorry! No Result Found" in response.text:
                print("Result: No Result Found")
                return

            # Try to find name (based on previous user context)
            # User said: td.cap_lt:nth-child(4)
            # Let's just print the title or something unique to verify
            title = soup.title.string if soup.title else "No Title"
            print(f"Page Title: {title}")
            
            # Dump a bit of text to see if we got data
            text_preview = soup.get_text()[:200].replace('\n', ' ')
            print(f"Text Preview: {text_preview}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_roll = 100050
    for i in range(5):
        test_scrape(start_roll + i)
