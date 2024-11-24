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
                    conn.execute(text('INSERT INTO orders (order_date_time, product_id, order_quantity) VALUES (:order_date_time, :product_id, :order_quantity)'), { 
                        "order_date_time": order_date_time, 
                        "product_id": f"{len(orders_data)} burger order", 
                        "order_quantity": overall_order_quantity
                    })
                    order_id = conn.execute(text('SELECT last_insert_rowid()')).scalar()

                    total = total_price_per_burger * order_quantity
                    conn.execute(text('''
                        INSERT INTO sales (order_id, sale_date_time, product_id, quantity, unit_price, total) 
                        VALUES (:order_id, :sale_date_time, :product_id, :quantity, :unit_price, :total)
                    '''), {
                        "order_id": order_id,
                        "sale_date_time": order_date_time,
                        "product_id": f"burger with {', '.join(toppings)}",
                        "quantity": order_quantity,
                        "unit_price": total_price_per_burger,
                        "total": total
                    })
                    #    orders_processed.append({
                    #        "order_id": order_id,
                     #       "total_price_per_burger": total,
                    #        "toppings": toppings
                     #   })
                    components_list = []
                    unit_prices = []
                    for order in orders_processed:
                        components_list.append(f'burger with {', '.join(order["toppings"])}')
                        unit_prices.append(f"{order["total_price_per_burger"]:.2f}")
                    conn.execute(text(''' 
                        INSERT INTO sales (order_id, sale_date_time, product_id, quantity, unit_price, total) 
                        VALUES (:order_id, :sale_date_time, :product_id, :quantity, :unit_price, :total) 
                    '''), { 
                            "order_id": order_id, 
                            "sale_date_time": order_date_time, 
                            "product_id": f"{' and '.join(components_list)}", 
                            "quantity": overall_order_quantity, 
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


#small 

if __name__ == '__main__':
    app.run(debug=True, port=8080)
