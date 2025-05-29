FROM python:3.9

# Install dependencies required for mysqlclient
RUN apt-get update && apt-get install -y pkg-config default-libmysqlclient-dev

# Set initial working directory to /app
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire project into /app
COPY . .

# Change working directory to where manage.py is located
WORKDIR /app/payments_system

# Command to run the Django development server
CMD ["python", "payments_system/manage.py", "runserver", "0.0.0.0:8000"]