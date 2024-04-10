from app import create_app, socketio

# Create an app instance using the factory function
app = create_app()

if __name__ == '__main__':
    # Run the application with Socket.IO support
    socketio.run(app, debug=True)