FROM python:3.12

# initialise everything
RUN pip install pipenv
WORKDIR /app
COPY . .
RUN pipenv install --system

# compile SCSS files
RUN python build_scss.py

# run app using gunicorn
CMD gunicorn fulcrum:app -b 0.0.0.0:5000
