from flask import Flask,jsonify,Response,request
from flask_cors import CORS
import pandas as pd
import json
from sqlalchemy import create_engine, text

app = Flask(__name__)
cors = CORS(app, origins='*')
engine = create_engine('sqlite:///vendor.db')

create_table_statement = text('''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    order_date_time DATETIME, 
    product_id TEXT, 
    quantity INTEGER, 
    price REAL,
    total REAL 
) 
''')

with engine.connect() as conn:
    conn.execute(create_table_statement)
# Load the JSON file into a pandas DataFrame
df = pd.read_json('inventory.json') 
df.to_sql('invent_data', engine, if_exists='replace', index=False)

@app.route('/products', methods=['GET']) 
def get_products(): 
    conn = engine.connect()
    query = text('SELECT * FROM invent_data')
    result = conn.execute(query)
    products = [dict(row._mapping) for row in result]
    conn.close()
    return jsonify(products)

@app.route('/orders', methods=['POST'])
def take_order():
    order_data = request.json
    product_id = order_data["product_id"] #need to decide how order information will be communicated
    order_quantity = order_data["order_quantity"] #placeholders
    store_id = order_data["store_id"]
    order_date_time = order_data["order_date_time"]
    with engine.connect() as conn:
        result = conn.execute(text('SELECT onhand_quantity FROM retail_data WHERE product_id = :product_id'), {"product_id": product_id})
        product = result.fetchone()
        if product and product["onhand_quantity"] >= order_quantity:
            conn.execute(text('UPDATE retail_data SET onhand_quantity = onhand_quantity - :order_quantity WHERE product_id = :product_id'), {"order_quantity": order_quantity, "product_id": product_id}) 
            total = order_quantity * product["unit_price"]
            conn.execute(text('INSERT INTO sales (order_date_time, product_id, quantity, price, total) VALUES (:order_date_time, :product_id, :quantity, :price, :total)'), {
                "order_date_time": order_date_time,
                "product_id": product_id,
                "quantity": order_quantity,
                "price": product["unit_price"],
                "total": total
            })
            return jsonify({"message": "Order processed"})
        else:
            return jsonify({"error": "Insufficient inventory"}), 400 #400 status code for hwne server cannot or will not process a request due to client error
        
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
