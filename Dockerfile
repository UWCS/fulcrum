FROM python:3.12

# initialise everything
RUN pip install uv
WORKDIR /app
COPY . .

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync --locked --no-dev

# compile SCSS files
RUN python ./scripts/build_scss.py

# run app using gunicorn
CMD ["gunicorn", "fulcrum:app", "-b", "0.0.0.0:5000"]
