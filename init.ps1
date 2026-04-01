mkdir persona-app
cd persona-app

# frontend
npm create vite@latest frontend -- --template vue
cd frontend
npm install
cd ..

# backend structure
mkdir backend
mkdir backend\app
mkdir backend\app\parser
mkdir backend\uploads
mkdir backend\outputs

ni backend\app\__init__.py -ItemType File
ni backend\app\schemas.py -ItemType File
ni backend\app\main.py -ItemType File
ni backend\app\parser\__init__.py -ItemType File
