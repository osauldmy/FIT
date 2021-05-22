.. role:: red
	  :class: red

************
Installation
************

Apixy Backend
================

Local development
------------------
In order to start development right away:

 1. git clone git@gitlab.fit.cvut.cz:apixy/apixy-be
 2. cd apixy-be
 3. python -m venv venv
 4. source venv/bin/activate
 5. pip install -r requirements.txt
 6. pip install pre-commit
 7. pre-commit install
 8. git checkout your_branch # optional step
 9. pre-commit run --all-files # optional step to create cache

Running the web server locally
-------------------------------
Copy the .env.sample file and edit the values:
 cp .env.sample .env

Run the db and migrate containers:
 docker-compose up --build db migrate

Run the api component locally (--reload for autoreload on file change):
 uvicorn apixy.app:app --reload

Running the entire app in docker
---------------------------------
Copy the .env.sample file and edit the values:
 cp .env.sample .env

Run the app:
 docker-compose up --build


Apixy Frontend
===============

Local development
------------------
In order to start development right away:

 1. git clone git@gitlab.fit.cvut.cz:apixy/apixy-fe
 2. cd apixy-fe
 3. sudo apt install nodejs
 4. sudo apt install npm
 5. npm install
 6. npm install @material-ui/icons
 7. npm install @types/react-sidebar
 8. npm install styled-components
 9. git checkout your_branch # git checkout -b your_branch (in case you want to create a new branch)

Running the web server locally
-------------------------------
 1. cd apixy-fe
 2. npm install
 3. npm start

**NOTE:** Server will run on port 3000 by default

Specify API url in case of need with ENV var :red:`REACT_APP_APIXY_API`

 1. export REACT_APP_APIXY_API="http://foo.bar:port/api/v42"
 2. npm start

Creating optimised development build
------------------------------------
 1. npm install -g serve
 2. cd apixy-fe
 3. npm run build
 4. serve -s build

**NOTE:** Server will run on port 5000 by default
