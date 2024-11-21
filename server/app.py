from flask import Flask,jsonify,Response
from flask_cors import CORS
import pandas as pd
import json
from sqlalchemy import create_engine, text

app = Flask(__name__)
cors = CORS(app, origins='*')
engine = create_engine('sqlite:///vendor.db')

# Load the JSON file into a pandas DataFrame
df = pd.read_json('retail.json') 
df.to_sql('invent_data', engine, if_exists='replace', index=False)
@app.route('/products', methods=['GET']) 
def get_products(): 
    conn = engine.connect() 
    query = text('SELECT * FROM invent_data')
    result = conn.execute(query) 
    products = [dict(row._mapping) for row in result] 
    conn.close()
    return jsonify(products)
@app.route('/preliminary')
def read_file():
    # Open the JSON file
    with open('retail.json', 'r') as file:
        # Load data as pandas dataframe
        df = pd.read_json(file)
        df['order_date_time'] = df['order_date_time'].astype(str)
    data = df.to_dict(orient='records')
    formatted_json = json.dumps(data, indent=2)
    return Response(formatted_json, mimetype='application/json')
# Access the data


#small 

if __name__ == '__main__':
    app.run(debug=True, port=8080)
