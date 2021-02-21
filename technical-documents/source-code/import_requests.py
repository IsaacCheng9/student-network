from flask import Flask, render_template, request, redirect
from passlib.hash import sha256_crypt

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index_page():
    return redirect("/login")

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')
    
@app.route('/login', methods=['POST'])
def login_submit():
    username = request.form['username_input']
    psw = request.form['psw_input']
    #Get user from database using username
    #Compare password with hashed password 
    #Compare using sha256_crypt.verify(psw, hashed_password)
    return redirect("/postpage")

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')      

@app.route('/register', methods=['POST'])
def register_submit():
    username = request.form['username_input']
    email = request.form['email_input']
    psw = request.form['psw_input']
    psw_check = request.form['psw_input_check']
    if password_check(psw, psw_check):
        print('Password Matches')
        hash_psw = sha256_crypt.hash(psw)
        #store username and email in db
        #store hashed psw in db
    else:
        print('Passwords do not match')
        #set a variable = to false which returns an error message on redirect
    return redirect("/postpage")
    


@app.route('/postpage', methods=['GET'])
def post_page():
    return render_template('postpage.html')


def password_check(psw, psw_check):
    if psw == psw_check:
        return True
    else:
        return False     

if __name__ == '__main__':
    app.run(debug=True) 


#print("password1 -> " + password)
#print("password2 -> " + password2)

#print(sha256_crypt.verify("myPassword123", password))
#print(sha256_crypt.verify("myPassword1234", password))