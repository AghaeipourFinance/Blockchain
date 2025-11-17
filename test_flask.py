from flask import Flask , request
import json
import requests
from bs4 import BeautifulSoup

def get_data_tgju(assets=None):
    url = 'https://www.tgju.org/'
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to retrieve the page. Status code: {response.status_code}"}

    soup = BeautifulSoup(response.text, 'html.parser')

    data_map = {
        "سکه": soup.find(text="سکه").find_next().text.strip(),
        "دلار": soup.find('li', {'id': "l-price_dollar_rl"}).find('span', {'class': 'info-price'}).text,
        "طلا ۱۸": soup.find(text="طلا ۱۸").find_next().text.strip(),
        "تتر": soup.find(text="تتر").find_next().text.strip(),
        "نفت برنت": soup.find('li', {'id': "l-oil_brent"}).find('span', {'class': 'info-price'}).text,
        "بیت کوین": soup.find('li', {'id': 'l-crypto-bitcoin'}).find('span', {'class': 'info-price'}).text,
    }

    if assets:
        # Filter and return only requested assets
        filtered_data = {key: data_map[key] for key in assets if key in data_map}
        return filtered_data if filtered_data else {"error": "No valid assets found"}
    else:
        return data_map

app = Flask(__name__)

@app.route('/',methods=['GET'])
def home():
    return 'Welcome To Damus Page'

@app.route('/live', methods=['GET'])
def get_live():
    data = get_data_tgju()
    return json.dumps(data)

@app.route('/asset', methods=['POST'])
def get_asset():
    """
    how request for this part
    import requests
            url = 'http://127.0.0.1:5000/asset'
            header = {'assets': ["دلار", "سکه"]}
            response = requests.post(url=url , json=header)
            response.json()
    """
    try:
        content = request.get_json()
        assets = content.get('assets')
        return json.dumps(get_data_tgju(assets))
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    app.run(debug=True)
