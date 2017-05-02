import os
import sys
file_item_path= os.path.join(os.path.dirname(__file__),"myflaskApp\Lib\site-packages") # con esta linea de codigo realizamos el import de la libreria
sys.path.append(file_item_path)
print(file_item_path)

from flask import Flask#, render_template, abort
app = Flask(__name__)



@app.route('/')
def hello_world():
    return 'Hello, World!'
"""
@app.route('/')
def helloWorld():
	return print("Putos")

if __name__ == '__main__':
	host=os.getenv('IP','0.0.0.0')
	port=int(os.getenv('PORT',5000))
	app.run(host=host, port=port)
	"""