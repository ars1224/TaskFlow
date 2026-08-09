import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.engine import URL

load_dotenv()

app = Flask(__name__)
CORS(app)

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.get("/api/health")
def health():
    return jsonify(
        status="success",
        message="Flask API is running",
    )


@app.get("/api/database-health")
def database_health():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify(
            status="success",
            message="Flask successfully connected to PostgreSQL",
        )
    except Exception as error:
        return jsonify(
            status="error",
            message=str(error),
        ), 500


if __name__ == "__main__":
    app.run(debug=True)