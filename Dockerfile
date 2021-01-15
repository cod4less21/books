FROM ubuntu:16.04

MAINTAINER Sagar Shetty "https://www.sagarshetty.me"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev
	
RUN pip install -r requirements.txt && \
	export FLASK_APP="application.py"  && \
 export DATABASE_URL="postgres://gmkygsmsnolwct:b16b7cd541586a34c15ebf5e04dd4b8b9d76d0b52f54f8a0e91988bb2ade8c5f@ec2-54-157-78-113.compute-1.amazonaws.com:5432/dd266p1rlj3bro"  && \

ENTRYPOINT ["flask"]

CMD ["run"]