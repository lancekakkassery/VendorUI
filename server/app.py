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

create_shipments = text('''
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_date_time DATETIME,
    product_id TEXT,
    shipment_quantity INTEGER
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

create_expenses = text('''
CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    shipment_id  INTEGER,
    shipment_date_time DATETIME, 
    product_id TEXT, 
    quantity INTEGER, 
    restock_price REAL,
    total REAL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
) 
''')

create_inventory = text('''
CREATE TABLE IF NOT EXISTS inventory (
    product_name TEXT PRIMARY KEY,
    quantity INTEGER,
    unit_price REAL,
    restock_price REAL
) 
''')
with engine.connect() as conn:
    result = conn.execute(text(f"SELECT 1 FROM expenses LIMIT 1"))
    row = result.fetchone()
    if row:
        print(f"expenses has data")
    else:
        print(f"expenses is empty")

with engine.connect() as conn:
    conn.execute(create_orders)
    conn.execute(create_sales)
    conn.execute(create_inventory)
    conn.execute(create_shipments)
    conn.execute(create_expenses)

# Load the JSON file into a pandas DataFrame
df = pd.read_json('inventory.json') 
df.to_sql('inventory', engine, if_exists='replace', index=False)

@app.route('/inventory', methods=['GET']) 
def get_inventory(): 
    conn = engine.connect()
    query = text('SELECT * FROM inventory')
    result = conn.execute(query)
    products = [dict(row._mapping) for row in result]
    conn.close()
    return jsonify(products)

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
        rows = result.fetchall()
        sales = []
        for row in rows:
            sales.insert(0,dict(row._mapping))
    return jsonify(sales)

@app.route('/clear_sales', methods=['POST'])
def clear_sales():
    # Create a connection to the database
    with engine.connect() as conn:
        # Execute the DELETE query to remove all records from the orders table
        try:
            conn.execute(text("DELETE FROM sales"))
            conn.commit()  # Commit the changes to the database

            # Respond with a success message
            return jsonify({"message": "Sales history cleared successfully!"}), 200
        
        except Exception as e:
            # If there's an error, return an error message
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

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
            order_history.insert(0,dict(row._mapping))
    # Return the data as a JSON response
    return jsonify(order_history)

@app.route('/clear_order_history', methods=['POST'])
def clear_order_history():
    # Create a connection to the database
    with engine.connect() as conn:
        # Execute the DELETE query to remove all records from the orders table
        try:
            conn.execute(text("DELETE FROM orders"))
            conn.commit()  # Commit the changes to the database

            # Respond with a success message
            return jsonify({"message": "Order history cleared successfully!"}), 200
        
        except Exception as e:
            # If there's an error, return an error message
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/shipment_history', methods=['GET'])
def shipment_history():
    # Create a connection to the database
    with engine.connect() as conn:
        # You can now execute queries
        query = text("SELECT * FROM shipments")  # Adjust with your actual table name
        result = conn.execute(query)
        # Fetch all rows from the result
        rows = result.fetchall()
        # Convert the result into a list of dictionaries
        shipment_history = []
        for row in rows:
            # For each row, create a dictionary of the columns and their values
            shipment_history.insert(0,dict(row._mapping))
    # Return the data as a JSON response
    return jsonify(shipment_history)

@app.route('/clear_shipment_history', methods=['POST'])
def clear_shipment_history():
    # Create a connection to the database
    with engine.connect() as conn:
        # Execute the DELETE query to remove all records from the orders table
        try:
            conn.execute(text("DELETE FROM shipments"))
            conn.commit()  # Commit the changes to the database

            # Respond with a success message
            return jsonify({"message": "Shipment history cleared successfully!"}), 200
        
        except Exception as e:
            # If there's an error, return an error message
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/restock_inventory', methods=['POST'])
def restock():
    shipment_data = request.json
    product_name = shipment_data["product_name"]
    shipment_quantity = shipment_data["shipment_quantity"]
    shipment_date_time = shipment_data["shipment_date_time"]
    with engine.connect() as conn:
        # Fetch the product details from the inventory
        result = conn.execute(text('SELECT quantity, restock_price FROM inventory WHERE product_name = :product_name'), {"product_name": product_name})
        product = result.fetchone()
        if product:
            product = dict(product._mapping)
            # Update the inventory
            conn.execute(text('UPDATE inventory SET quantity = quantity + :shipment_quantity WHERE product_name = :product_name'),
                            {"shipment_quantity": shipment_quantity, "product_name": product_name})
            # Insert new shipment
            conn.execute(text('INSERT INTO shipments (shipment_date_time, product_id, shipment_quantity) VALUES (:shipment_date_time, :product_id, :shipment_quantity)'),
                            {
                                "shipment_date_time": shipment_date_time,
                                "product_id": product_name,
                                "shipment_quantity": shipment_quantity,
                            })
            # Get the last inserted shipment ID
            shipment_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()
            print(f"Shipment ID: {shipment_id}")  # Debugging: Print the order ID to confirm it's being inserted

            if shipment_id:
                total = shipment_quantity * product["restock_price"]
                conn.execute(text('''
                    INSERT INTO expenses (shipment_id, shipment_date_time, product_id, quantity, restock_price, total)
                    VALUES (:shipment_id, :shipment_date_time, :product_id, :quantity, :restock_price, :total)
                '''),
                                {
                                    "shipment_id": shipment_id,
                                    "shipment_date_time": shipment_date_time,
                                    "product_id": product_name,
                                    "quantity": shipment_quantity,
                                    "restock_price": product["restock_price"],
                                    "total": total
                                })
                
                return jsonify({"message": "Shipment processed"})
            else:
                return jsonify({"error": "Failed to retrieve Shipment ID"}), 500
        else:
            return jsonify({"error": "Product does not exist"}), 400    



if __name__ == '__main__':
    app.run(debug=True, port=8080)
