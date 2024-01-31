from flask import Flask, request, render_template, jsonify
import os
from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain_openai import OpenAI   
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# OpenAI API Anahtarını ayarlayın
os.environ['OPENAI_API_KEY'] = "API-KEY-HERE"

# SQLite veritabanı için URI ayarlayın
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# SQLAlchemy nesnesini oluşturun
db = SQLAlchemy(app)

# QueryHistory modelini tanımlayın
class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_ = db.Column(db.String(500), nullable=False)
    response = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QueryHistory {self.id}>'

# MSSQL veritabanı bağlantısını oluşturun
mssql_connection_string = "mssql+pyodbc://<USERNAME>:<PASSWORD>@<SERVER_ADDRESS>/<DATABASE_NAME>?driver=ODBC+Driver+17+for+SQL+Server"
mssql_db = SQLDatabase.from_uri(mssql_connection_string)

llm = OpenAI(temperature=0,max_tokens=60)  # OpenAI LLM'yi oluşturun
toolkit = SQLDatabaseToolkit(db=mssql_db, llm=llm)  # LLM parametresini ekleyin
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/get_response', methods=['POST'])
def get_response():
    #translator = Translator()
    query_ = request.form['query']
    #translated_result = translator.translate(agent_executor.run(query_),src='en',dest='tr').text
    translated_result = agent_executor.run(query_)
    max_length = 200  # Maksimum çıktı uzunluğunu belirleyin
    if len(translated_result) > max_length:
        result = translated_result[:max_length] + '...'
    new_record = QueryHistory(query_=query_, response=translated_result)
    db.session.add(new_record)
    db.session.commit()

    return jsonify({'response': translated_result})

@app.route("/view_records")
def view_records():
    with app.app_context():
        all_records = QueryHistory.query.all()
    return render_template("view_records.html", all_records=all_records)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   
    app.run(debug=True)
