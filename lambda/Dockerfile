FROM public.ecr.aws/lambda/python:3.12

# Copy your app code
COPY . ${LAMBDA_TASK_ROOT}

# Not a good idea, but okay for quick testing. 
# Store your environment variables in AWS Secrets or 
# add them to your Lambda Config.
COPY .env ${LAMBDA_TASK_ROOT}

# Export your dependencies as a requirements.txt
# Use either `pip freeze > requirements.txt` after activate your python env,
# or poetry export --format requirements.txt --without-hashes --output requirements.txt
COPY requirements.txt .

# Install all dependencies to the Lambda task root folder.
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}" -U --no-cache-dir

# Start AWS Lambda Handler. This handler manages all communication 
# between Lambda and your code.
CMD [ "app.handler" ]