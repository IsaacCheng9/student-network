from flask import Flask

from .views.achievements import achievements_blueprint
from .views.connections import connections_blueprint
from .views.login import login_blueprint
from .views.posts import posts_blueprint
from .views.profile import profile_blueprint
from .views.quizzes import quizzes_blueprint
from .views.staff import staff_blueprint

app = Flask(__name__)
app.register_blueprint(achievements_blueprint, url_prefix="")
app.register_blueprint(connections_blueprint, url_prefix="")
app.register_blueprint(login_blueprint, url_prefix="")
app.register_blueprint(posts_blueprint, url_prefix="")
app.register_blueprint(profile_blueprint, url_prefix="")
app.register_blueprint(quizzes_blueprint, url_prefix="")
app.register_blueprint(staff_blueprint, url_prefix="")
app.secret_key = ("\xfd{H\xe5 <\x95\xf9\xe3\x96.5\xd1\x01O <!\xd5\""
                  "xa2\xa0\x9fR\xa1\xa8")
app.url_map.strict_slashes = False

if __name__ == "__main__":
    app.run(debug=True)
