from sqlalchemy import create_engine, text 
# Connect to the database 
create_inventory = text('''
CREATE TABLE IF NOT EXISTS inventory (
    product_name TEXT PRIMARY KEY,
    quantity INTEGER
) 
''')

engine = create_engine('sqlite:///vendor.db')
with engine.connect() as conn:
    conn.execute(create_inventory)
    conn.execute(text(''' INSERT INTO inventory (product_name, quantity) VALUES (:product_name, :quantity) '''), 
        { "product_name": "bun", "quantity": 100})
    conn.commit()
with engine.connect() as conn: # Execute the query to check the inventory for 'bun' 
    result = conn.execute(text("SELECT * FROM inventory WHERE product_name = 'bun'")) 
    products = result.fetchall() # Print the results 
if products: 
    for product in products: 
        print(dict(product._mapping)) 
else: 
    print("No products found with product_name 'bun'")