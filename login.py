import os
import sys
file_item_path= os.path.join(os.path.dirname(__file__),"pythonFlask\Lib\site-packages") # con esta linea de codigo realizamos el import de la libreria
sys.path.append(file_item_path)
print(file_item_path)

from flask import Flask, url_for,request, render_template,redirect,flash,make_response,session#, abort
								# session permite que la cookie de usr sea encriptada
app = Flask(__name__)

##coment for git 2
@app.route('/login',methods=['GET','POST'])
def login():
	error=None	
	if request.method=='POST':
		usr=request.form['username']
		pwd=request.form['password']
		if (not usr or not pwd):
			error="Datos vacios, intenta nuevamente "
			#flash("Datos vacios, intenta nuevamente ")
		else:
			if valid_login(usr,pwd):
				flash("Aqui esta mi mensaje flash: Chupame esta!")
				session['usr']=request.form.get('username')
				return redirect(url_for('welcome'))
				#response=make_response(redirect(url_for('welcome')))  eliminado por agregar session
				#response.set_cookie('usr',usr)
				#return response
				
				#return redirect(url_for('welcome',username=usr))
				#return "Welcom back %s you are logged in" % request.form['username']
			else:
				error="username and password are incorrect"	
	return render_template('login.html',error=error)

@app.route('/logout')
def logout():
	session.pop('usr',None)
	return redirect(url_for('login'))
	#response=make_response(redirect(url_for('login')))  eliminado por agregar session
	#response.set_cookie('usr','',expires=0)
	#return response

def valid_login(username, password):
	if username== password:
		return True
	else:
		return False

@app.route('/')
def welcome():
	#usr=request.cookies.get('usr')
	if 'usr' in  session:
		#return render_template('welcome.html',username=usr)
		return render_template('welcome.html',username=session['usr'])
	else:
		redirect(url_for('login'))

if __name__ == '__main__':
	host=os.getenv('IP','127.0.0.1')
	port=int(os.getenv('PORT',5000))
	app.debug=True
	app.secret_key='CadenaSecreta'
	app.run(host=host, port=port)
	