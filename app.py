from flask import Flask, request, render_template
from essentials import rank

app = Flask(__name__)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/search")
def search():
	query = request.args["query"]
	# TODO Sanitize query
	# 
	urls = rank(query)
	return render_template("results.html", urls=urls)