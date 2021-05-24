import sqlite3

from flask import Blueprint, redirect, render_template, request, session

import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general

inventory_blueprint = Blueprint(
    "inventory", __name__, static_folder="static", template_folder="templates"
)

@inventory_blueprint.route("/inventory")
def inventory():
    return render_template("inventory.html", 
        requestCount=helper_connections.get_connection_request_count(),
        notifications=helper_general.get_notifications()
    )