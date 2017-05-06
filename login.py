import os
import sys
file_item_path= os.path.join(os.path.dirname(__file__),"pythonFlask\Lib\site-packages") 
sys.path.append(file_item_path)
print(file_item_path)

from flask         import Flask, url_for,request, render_template,redirect,flash,make_response,session
from flask_pymongo import PyMongo
								
app = Flask(__name__)

app.config['MONGO_DBNAME']='flaskPython'
app.config['MONGO_URI']='mongodb://127.0.0.1:27017/flaskPython'

mongo = PyMongo(app)	#contiene la conexion a mongo


@app.route('/login',methods=['GET','POST'])
def login():
	error=None	
	if request.method=='POST':
		usr=request.form['username']
		pwd=request.form['password']
		if (not usr or not pwd):
			error="Datos vacios, intenta nuevamente "
		else:
			if valid_login(usr,pwd):
				flash("Aqui esta mi mensaje flash: Chupame esta!")
				session['usr']=request.form.get('username')
				return redirect(url_for('welcome'))
			else:
				error="username and password are incorrect"	
	return render_template('login.html',error=error)

@app.route('/logout')
def logout():
	session.pop('usr',None)
	return redirect(url_for('login'))

def valid_login(username, paswd):
	collection = mongo.db.user	
	get_user_mongo = collection.find({'username':username})
	for user in get_user_mongo:
		if user['username'] == username and user['password'] == paswd:
			return True
		else:
			return False


@app.route('/')
def welcome():
	if 'usr' in  session:
		return render_template('welcome.html',username=session['usr'])
	else:
		redirect(url_for('login'))

if __name__ == '__main__':
	host=os.getenv('IP','127.0.0.1')
	port=int(os.getenv('PORT',5000))
	app.debug=True
	app.secret_key='xe1VV\x9c\xe1D\x9b\xc1i\x134\x992)\x00\xf4\x14\xfd\xb10\x02%N\xdc'
	app.run(host=host, port=port)
	