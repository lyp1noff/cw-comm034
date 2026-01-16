import os
from flask import Flask, render_template_string
from google.cloud import bigquery

app = Flask(__name__)
client = bigquery.Client()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>B5 Data Viewer</title></head>
<body>
    <h1>BigQuery Data Portal</h1>
    <p>Select a report to generate:</p>
    <a href="/report1"><button>Top 5 Categories (Revenue)</button></a>
    <a href="/report2"><button>Orders Status Summary</button></a>
    <hr>
    {% if table %}
        <h2>Report Results:</h2>
        {{ table | safe }}
    {% endif %}
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/report1')
def report1():
    query = f"""
        SELECT 
            p.category, 
            SUM(oi.sale_price) as revenue 
        FROM `{os.getenv('PROJECT_ID')}.thelook.order_items` AS oi
        JOIN `{os.getenv('PROJECT_ID')}.thelook.products` AS p 
          ON oi.product_id = p.id 
        GROUP BY 1 
        ORDER BY 2 DESC 
        LIMIT 5
    """
    df = client.query(query).to_dataframe()
    return render_template_string(HTML_TEMPLATE, table=df.to_html(classes='data', header="true"))


@app.route('/report2')
def report2():
    query = f"SELECT status, COUNT(*) as count FROM `{os.getenv('PROJECT_ID')}.thelook.orders` GROUP BY 1 ORDER BY 2 DESC"
    df = client.query(query).to_dataframe()
    return render_template_string(HTML_TEMPLATE, table=df.to_html(classes='data', header="true"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
