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
def print_sales_data(): 
    with engine.connect() as conn: 
        result = conn.execute(text('SELECT * FROM sales')) 
        sales = [dict(row._mapping) for row in result] 
        print("Sales Data:", sales)
@app.route('/orders', methods=['POST'])
def take_order():
    order_data = request.json
    product_name = order_data["product_name"]
    order_quantity = order_data["order_quantity"]
    order_date_time = order_data["order_date_time"]
    
    with engine.connect() as conn:
        # Start a transaction explicitly
        with conn.begin():
            # Fetch the product details from the inventory
            result = conn.execute(text('SELECT quantity, unit_price FROM inventory WHERE product_name = :product_name'), {"product_name": product_name})
            product = result.fetchone()
            if product:
                product = dict(product._mapping)
                # Check if sufficient inventory exists
                if product["quantity"] >= order_quantity:
                    # Update the inventory
                    conn.execute(text('UPDATE inventory SET quantity = quantity - :order_quantity WHERE product_name = :product_name'),
                                 {"order_quantity": order_quantity, "product_name": product_name})
                    # Insert new order
                    conn.execute(text('INSERT INTO orders (order_date_time, product_id, order_quantity) VALUES (:order_date_time, :product_id, :order_quantity)'),
                                 {
                                     "order_date_time": order_date_time,
                                     "product_id": product_name,
                                     "order_quantity": order_quantity,
                                 })
                    # Get the last inserted order ID
                    order_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()
                    print(f"Order ID: {order_id}")  # Debugging: Print the order ID to confirm it's being inserted

                    if order_id:
                        total = order_quantity * product["unit_price"]
                        conn.execute(text('''
                            INSERT INTO sales (order_id, sale_date_time, product_id, quantity, unit_price, total)
                            VALUES (:order_id, :sale_date_time, :product_id, :quantity, :unit_price, :total)
                        '''),
                                     {
                                         "order_id": order_id,
                                         "sale_date_time": order_date_time,
                                         "product_id": product_name,
                                         "quantity": order_quantity,
                                         "unit_price": product["unit_price"],
                                         "total": total
                                     })


                        return jsonify({"message": "Order processed"})
                    else:
                        return jsonify({"error": "Failed to retrieve order ID"}), 500
                else:
                    return jsonify({"error": "Insufficient inventory"}), 400
            else:
                return jsonify({"error": "Product does not exist"}), 400    

@app.route('/sales', methods=['GET'])
def sales_data():
    with engine.connect() as conn:
        query = text('SELECT * FROM sales')
        result = conn.execute(query)
        sales = [dict(row._mapping) for row in result]
    return jsonify(sales)

@app.route('/order_history', methods=['GET'])
def order_history():
    # Create a connection to the database
    with engine.connect() as conn:
        # You can now execute queries
        query = text("SELECT * FROM orders")  # Adjust with your actual table name
        result = conn.execute(query)
        # Fetch all rows from the result
        rows = result.fetchall()
        # Convert the result into a list of dictionaries
        order_history = []
        for row in rows:
            # For each row, create a dictionary of the columns and their values
            order_history.append({column: value for column, value in row.items()})
    # Return the data as a JSON response
    return jsonify(order_history)


#small 

if __name__ == '__main__':
    app.run(debug=True, port=8080)
