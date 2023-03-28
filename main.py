from app import app, server

if __name__ == '__main__':
    #server.serve()
    app.run(host='0.0.0.0', port=80, debug=True)
