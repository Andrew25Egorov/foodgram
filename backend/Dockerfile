FROM python:3.9

WORKDIR /app

RUN python -m pip install --upgrade pip && pip install gunicorn==20.1.0 --no-cache-dir

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]
# CMD ["python", "manage.py", "runserver", "0:8000"]