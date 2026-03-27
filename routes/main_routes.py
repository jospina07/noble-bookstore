from flask import Blueprint, redirect, url_for, jsonify

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return redirect(url_for("books.login"))

@main.route("/api/status")
def status():
    return jsonify({
        "status": "running",
        "project": "team-project"
    })

@main.route("/api/greeting")
def greeting():
    return jsonify({
        "message": "Hello from the Flask team project API"
    })

@main.route("/api/team")
def team():
    return jsonify({
        "team_members": [
            "Member 1",
            "Member 2",
            "Member 3"
        ]
    })