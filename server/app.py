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
    quantities INTEGER, 
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
    conn.execute(create_orders)
    conn.execute(create_sales)
    conn.execute(create_inventory)
    conn.execute(create_shipments)
    conn.execute(create_expenses)
def check_if_table_has_data(table_name):
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"Table {table_name} has data.")
        else:
            print(f"Table {table_name} is empty.")
        
check_if_table_has_data('shipments') 
check_if_table_has_data('orders') 
check_if_table_has_data('sales')
# Check if the desired table has data, e.g., 'inventory'
check_if_table_has_data('inventory')

with engine.connect() as conn:
    result = conn.execute(text(f"SELECT 1 FROM expenses LIMIT 1"))
    row = result.fetchone()
    if row:
        print(f"expenses has data")
    else:
        print(f"expenses is empty")

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
    orders_data = request.json
    with engine.connect() as conn:
        order_sufficient_inventory = True
        orders_processed = []
        order_price_total = 0.0

        all_toppings = {}
        overall_order_quantity = 0
        for order_data in orders_data:
            toppings = order_data["toppings"] + ["bun", "patty"]
            order_quantity = order_data["order_quantity"]
            order_date_time = order_data["order_date_time"]

            with conn.begin():
                total_price_per_burger = 0.0 
                sufficient_inventory = True
                
                for topping in toppings: 
                    if topping not in all_toppings:
                        all_toppings[topping] = 0
                    all_toppings[topping] += order_quantity

                    result = conn.execute(text('SELECT quantity, unit_price FROM inventory WHERE product_name = :product_name'), {"product_name": topping}) 
                    product = result.fetchone() 
                    product = dict(product._mapping)

                    if product:
                        if product["quantity"] < all_toppings[topping]: 
                            sufficient_inventory = False
                            break
                        total_price_per_burger += product["unit_price"]
                    else:
                        sufficient_inventory = False
                        break

                if not sufficient_inventory:
                    order_sufficient_inventory = False
                    break

                if sufficient_inventory:
                    order_price_total += total_price_per_burger * order_quantity
                    overall_order_quantity += order_quantity
                    orders_processed.append({ 
                        "toppings": toppings, 
                        "order_quantity": order_quantity, 
                        "order_date_time": order_date_time, 
                        "total_price_per_burger": total_price_per_burger
                    })

                if order_sufficient_inventory:
                    for topping, quantity_needed in all_toppings.items():
                        conn.execute(text('UPDATE inventory SET quantity = quantity - :quantity_needed WHERE product_name = :product_name'), {
                            "quantity_needed": quantity_needed, 
                            "product_name": topping
                        })
                    
                    components_list = []
                    unit_prices = []
                    quantities = []
                    for order in orders_processed:
                        components_list.append(f'burger with {', '.join(order["toppings"])}')
                        unit_prices.append(f"{order["total_price_per_burger"]:.2f}")
                        quantities.append(str(order["order_quantity"]))
                    conn.execute(text('INSERT INTO orders (order_date_time, product_id, order_quantity) VALUES (:order_date_time, :product_id, :order_quantity)'), { 
                        "order_date_time": order_date_time, 
                        "product_id": f"{len(orders_data)} burger order", 
                        "order_quantity": overall_order_quantity
                    })
                    order_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()
                    conn.execute(text(''' 
                        INSERT INTO sales (order_id, sale_date_time, product_id, quantities, unit_price, total) 
                        VALUES (:order_id, :sale_date_time, :product_id, :quantities, :unit_price, :total) 
                    '''), { 
                            "order_id": order_id, 
                            "sale_date_time": order_date_time, 
                            "product_id": f"{' and '.join(components_list)}", 
                            "quantities": f"{', '.join(quantities)}",
                            "unit_price": ', '.join(unit_prices),
                            "total": order_price_total
                    })
        if order_sufficient_inventory:
            return jsonify({"message": "Order confirmed", "orders": orders_processed, "total price": order_price_total})
        else:
            return jsonify({"error": "Insufficient inventory"}), 400
            
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

@app.route('/profits', methods = ['GET'])
def profit():
    with engine.connect() as conn:
        query = text('SELECT SUM(total) as total_profit FROM sales')
        result = conn.execute(query)
        profit = result.fetchone()
        return jsonify({"total_profit": profit[0]})
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
        with conn.begin():
            # Fetch the product details from the inventory
            result = conn.execute(text('SELECT quantity, restock_price FROM inventory WHERE product_name = :product_name'), {"product_name": product_name})
            product = result.fetchone()

            if product:
                product = dict(product._mapping)

                # Update the inventory by adding the new shipment quantity
                conn.execute(text('UPDATE inventory SET quantity = quantity + :shipment_quantity WHERE product_name = :product_name'),
                            {"shipment_quantity": shipment_quantity, "product_name": product_name})

                # Insert the new shipment record into the shipments table
                conn.execute(text('INSERT INTO shipments (shipment_date_time, product_id, shipment_quantity) VALUES (:shipment_date_time, :product_id, :shipment_quantity)'),
                            {
                                "shipment_date_time": shipment_date_time,
                                "product_id": product_name,
                                "shipment_quantity": shipment_quantity,
                            })

                # After inserting, we use last_insert_rowid() to fetch the auto-incremented shipment_id
                shipment_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()

                if shipment_id:
                    total = shipment_quantity * product["restock_price"]

                    # Insert an expense record related to the shipment
                    conn.execute(text(''' 
                        INSERT INTO expenses (shipment_id, shipment_date_time, product_id, quantity, restock_price, total)
                        VALUES (:shipment_id, :shipment_date_time, :product_id, :quantity, :restock_price, :total)
                    '''), {
                        "shipment_id": shipment_id,
                        "shipment_date_time": shipment_date_time,
                        "product_id": product_name,
                        "quantity": shipment_quantity,
                        "restock_price": product["restock_price"],
                        "total": total
                    })
                    
                    # Return the shipment ID and success message
                    return jsonify({"message": "Shipment processed", "shipment_id": shipment_id}), 200
                else:
                    return jsonify({"error": "Failed to retrieve Shipment ID"}), 500
            else:
                return jsonify({"error": "Product does not exist"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=8080)
