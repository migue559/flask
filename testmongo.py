import os
import sys
file_item_path= os.path.join(os.path.dirname(__file__),"pythonFlask\Lib\site-packages") 
sys.path.append(file_item_path)
print(file_item_path)

from flask import Flask, url_for,request, render_template,redirect,flash,make_response,session
from flask_pymongo import PyMongo
								
app = Flask(__name__)

app.config['MONGO_DBNAME']='flaskPython'
app.config['MONGO_URI']='mongodb://127.0.0.1:27017/flaskPython'

mongo = PyMongo(app)	#contiene la conexion a mongo

@app.route('/add')
def add():
    collection = mongo.db.user  # genera la conexion a la colleccion
    name='Luis'
    pwd='Luis786'
    a=[]
    new_user= collection.find({'name':name})
    for i in new_user:
    	print(i['name'])
    	a.append(i['name'])

    #new_user= collection.insert({'name':name,'password':pwd})
    return 'add user !!:::: %s' %a[0]

if __name__ == '__main__':
	app.run(debug=True)
 