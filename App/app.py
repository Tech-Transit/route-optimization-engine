from flask import Flask
import pandas as pd
from RouteEngine import engine as eng


app = Flask(__name__)
df = pd.read_csv('./assets/transport_facilities_full.csv')

@app.route('/')
def home():
    source = "Mundra Port"
    target = "Port of Piraeus"

    # Find optimal routes with mode preference
    G, paths, pos, node_colors, node_sizes, nodes_list = eng.find_optimal_routes(
        df, source, target, preferred_mode='Airport', k=10
    )
    
    print(pos)
    if pos=={}:
        print('None')
        return "<p>Try another mode, No optimal routes in preffered mode.</p>"
    
    return f"<p>{pos}</p>"



if __name__ == '__main__':
    app.run(debug=True)