from flask import Flask,jsonify,Response,request
from flask_cors import CORS
import pandas as pd
import json
from sqlalchemy import create_engine, text

app = Flask(__name__)
cors = CORS(app, origins='*')
engine = create_engine('sqlite:///vendor.db')

create_orders = text('''
CREATE TABLE IF NOT EXISTS orders (
    order_id  INTEGER PRIMARY KEY AUTOINCREMENT, 
    order_date_time DATETIME, 
    product_id TEXT, 
    order_quantity INTEGER
) 
''')

create_sales = text('''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    order_id  INTEGER,
    sale_date_time DATETIME, 
    product_id TEXT, 
    quantity INTEGER, 
    unit_price REAL,
    total REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
) 
''')

create_inventory = text('''
CREATE TABLE IF NOT EXISTS inventory (
    product_name TEXT PRIMARY KEY,
    quantity INTEGER,
    unit_price REAL
) 
''')

with engine.connect() as conn:
    conn.execute(create_orders)
    conn.execute(create_sales)
    conn.execute(create_inventory)

# Load the JSON file into a pandas DataFrame
df = pd.read_json('inventory.json') 
df.to_sql('inventory', engine, if_exists='replace', index=False)

@app.route('/products', methods=['GET']) 
def get_products(): 
    conn = engine.connect()
    query = text('SELECT * FROM inventory')
    result = conn.execute(query)
    products = [dict(row._mapping) for row in result]
    conn.close()
    return jsonify(products)

@app.route('/orders', methods=['POST'])
def take_order():
    order_data = request.json
    product_name = order_data["product_name"] #need to decide how order information will be communicated
    order_quantity = order_data["order_quantity"] #placeholders
    order_date_time = order_data["order_date_time"]
    with engine.connect() as conn:
        result = conn.execute(text('SELECT quantity, unit_price FROM inventory WHERE product_name = :product_name'), {"product_name": product_name})
        product = result.fetchone()
        if product:
            product = dict(product._mapping)
            if product["quantity"] >= order_quantity:
                conn.execute(text('UPDATE inventory SET quantity = quantity - :order_quantity WHERE product_name = :product_name'), {"order_quantity": order_quantity, "product_name": product_name}) 
                conn.execute(text('INSERT INTO orders (order_date_time, product_id, order_quantity) VALUES (:order_date_time, :product_id, :order_quantity)'), {
                    "order_date_time": order_date_time,
                    "product_id": product_name,
                    "order_quantity": order_quantity,
                })
                total = order_quantity * product["unit_price"]
                order_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()
                conn.execute(text('INSERT INTO sales (order_id, sale_date_time, product_id, quantity, unit_price, total) VALUES (:order_id, :sale_date_time, :product_id, :quantity, :unit_price, :total)'), {
                    "order_id": order_id,
                    "sale_date_time": order_date_time,
                    "product_id": product_name,
                    "quantity": order_quantity,
                    "unit_price": product["unit_price"],
                    "total": total
                })
                return jsonify({"message": "Order processed"})
            else:
                return jsonify({"error": "Insufficient inventory"}), 400 #400 status code for hwne server cannot or will not process a request due to client error
        else:
            return jsonify({"error": "Does not exist"}), 400    
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
