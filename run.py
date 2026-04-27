from app import create_app
from app.models import globalInit

app = create_app()

if __name__ == '__main__':
    globalInit()
    app.run(debug=True)
