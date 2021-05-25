import sqlite3

from flask import Blueprint, redirect, render_template, request, session

import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_inventory as helper_inventory

inventory_blueprint = Blueprint(
    "inventory", __name__, static_folder="static", template_folder="templates"
)

@inventory_blueprint.route("/inventory")
def inventory():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM user_inventory WHERE username=?;",
            (session["username"],),
        )
        # gets a list of IDs from my inventory
        my_item_ids = cur.fetchall()

        # get item data from database
        cur.execute("SELECT * FROM inventory_items")
        all_item_data = cur.fetchall()

        # create a dictionary to increase performance
        item_data_lookup = {}
        # put item data into a dictionary
        for item in all_item_data:
            item_id = item[0]
            item_data_lookup[item_id] = item

        items_out = []
        # make a list using item data using my inventory
        for item in my_item_ids:
            item_id = item[0]
            item_data = item_data_lookup[item_id]
            items_out.append(item_data)

        # sort by rarity, rarest = first
        items_out.sort(key=lambda x: x[3], reverse=True)

    return render_template("inventory.html", 
        requestCount=helper_connections.get_connection_request_count(),
        notifications=helper_general.get_notifications(),
        items=items_out
    )