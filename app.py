from flask import Flask, render_template, redirect, flash

app = Flask(__name__)
app.secret_key = '*T2<3>g;=E1Kc+N;^GP='

@app.route('/')
def home():
    contacts = [
    {
        'id' :'123213',
        'full_name': 'John C. Addams',
    },
    {
        'id' :'551232',
        'full_name': 'Kathleen Ann Williams',
    }]
    return render_template('contact_list.html', contacts=contacts)

if __name__ == '__main__':
    app.run(debug=True, port=5008)
