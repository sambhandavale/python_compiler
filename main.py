from flask import Flask,request,render_template
import io
import sys
from flask import Flask, request, jsonify
from io import StringIO

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

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
    
# Security configurations
BLACKLISTED_MODULES = {"os", "subprocess", "shutil", "sys", "ctypes", "socket"}
BLACKLISTED_BUILTINS = {"eval", "exec", "open", "__import__", "exit", "quit"}

def create_safe_globals():
    return {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "sum": sum,
            "max": max,
            "min": min,
            "sorted": sorted
        }
    }

def sanitize_code(user_code):
    for mod in BLACKLISTED_MODULES:
        if f"import {mod}" in user_code or f"from {mod}" in user_code:
            raise ValueError(f"Importing {mod} is not allowed")
    
    for builtin in BLACKLISTED_BUILTINS:
        if f"{builtin}(" in user_code:
            raise ValueError(f"Using {builtin}() is forbidden")
    
    return user_code

def test_user_code(user_code, test_cases):
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        input_data = test_case["input"]
        expected_output = str(test_case["output"]).strip()
        
        # Redirect stdin to simulate input
        sys.stdin = StringIO(input_data)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            # Execute user code
            exec(user_code, {'__name__': '__main__'})
            
            # Get the output
            actual_output = mystdout.getvalue().strip()
            
            # Compare with expected output
            if actual_output == expected_output:
                results.append({
                    "test_case": i,
                    "status": "PASSED",
                    "input": input_data,
                    "expected": expected_output,
                    "actual": actual_output
                })
            else:
                results.append({
                    "test_case": i,
                    "status": "FAILED",
                    "input": input_data,
                    "expected": expected_output,
                    "actual": actual_output
                })
                
        except Exception as e:
            results.append({
                "test_case": i,
                "status": "ERROR",
                "input": input_data,
                "error": str(e)
            })
            
        finally:
            # Reset stdin/stdout
            sys.stdin = sys.__stdin__
            sys.stdout = old_stdout
    
    return results


@app.route("/api/test-code", methods=["POST"])
def local_test_code():
    data = request.get_json()
    if not data or 'user_code' not in data or 'test_cases' not in data:
        return jsonify({'error': 'Missing user_code or test_cases'}), 400

    try:
        results = test_user_code(data['user_code'], data['test_cases'])
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()