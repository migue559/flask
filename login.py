import os
import sys
file_item_path= os.path.join(os.path.dirname(__file__),"pythonFlask\Lib\site-packages") # con esta linea de codigo realizamos el import de la libreria
sys.path.append(file_item_path)
print(file_item_path)

from flask import Flask, url_for,request, render_template#, abort
app = Flask(__name__)

##coment for git 
@app.route('/login',methods=['GET','POST'])
def login():
	error=None	
	if request.method=='POST':
		if valid_login(request.form['username'],request.form['password']):
			return "Welcom back %s you are logged in" % request.form['username']
		else:
			error="username and password are incorrect"	
	return render_template('login.html',error=error)

def valid_login(username, password):
	if username== password:
		return True
	else:
		return False



if __name__ == '__main__':
	host=os.getenv('IP','127.0.0.1')
	port=int(os.getenv('PORT',5000))
	app.debug=True
	app.run(host=host, port=port)
	