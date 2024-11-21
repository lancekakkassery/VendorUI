from flask import Flask,jsonify
from flask_cors import CORS
import pandas as pd
import json

app = Flask(__name__)
cors = CORS(app, origins='*')


# Load the JSON file into a pandas DataFrame
@app.route('/') # route is the URL or HTML key, ex. file/ vs file/home
def read_file():
    # Open the JSON file
    with open('retail.json', 'r') as file:
        # Load and parse the JSON data
        list_of_dict = json.load(file)
        output_list=[]
        for dict in list_of_dict:
            for key in dict:
                val=dict[key]
                output_list.append(f'"{key}":"{val}"')
        # output_string=', '.join(output_list)
    return json.dumps(output_list)
    # return json.loads('{"key":"val"}')
# Access the data


#small 

if __name__ == '__main__':
    app.run(debug=True, port=8080)
