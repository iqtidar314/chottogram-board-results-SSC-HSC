from curl_cffi import requests

def fetch_html(roll):
    url = "https://hscresult.bise-ctg.gov.bd/h_x_y_ctg25/individual/result_mark_details.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "roll": str(roll),
        "button2": "Submit"
    }
    
    print(f"Fetching HTML for roll: {roll}")
    try:
        response = requests.post(url, data=data, headers=headers, impersonate="chrome120", timeout=30)
        if response.status_code == 200:
            with open(f"roll_{roll}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved to roll_{roll}.html")
        else:
            print(f"Failed with status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_html(100500) # User provided example
