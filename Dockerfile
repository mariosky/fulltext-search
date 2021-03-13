FROM python:3.9
ADD . /code
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 5000
RUN pip install -r requirements.txt
RUN chmod 644 app.py
