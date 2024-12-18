from waitress import serve

from PR2CD_UI.wsgi import application
# documentation: https://docs.pylonsproject.org/projects/waitress/en/stable/api.html

if __name__ == '__main__':
    print("Starting server on http://localhost:8080 with 8 threads...")
    serve(application, host = 'localhost', port='8080',threads=8)