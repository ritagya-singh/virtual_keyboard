from flask import Flask, render_template
import os

app = Flask(__name__, template_folder='.')

@app.route('/')
def keyboard():
    # This renders your HTML file correctly
    return render_template('keyboard.html')

if __name__ == '__main__':
    # We run with 'adhoc' SSL so the eye-tracking camera works
    app.run(port=5000, ssl_context='adhoc')