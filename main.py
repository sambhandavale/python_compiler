from flask import Flask,request
import io
import sys

app = Flask(__name__)

@app.route('/python',methods=['POST'])
def run_python_code():
    if request.method == 'POST':
        code_json = request.json
        code = code_json['code']
        stout = io.StringIO() # instead of putting output in terminal now in this variable
        sys.stdout = stout
        exec(code)

        result = stout.getvalue()
        sys.stdout = sys.__stdout__ # to reset 
        return {"result":result.replace('\n',' ')}

if __name__ == '__main__':
    app.run()