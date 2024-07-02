FROM python:alpine
RUN mkdir /ldap2synapse
RUN mkdir /ldap2synapse/logs
WORKDIR /ldap2synapse
ADD ldap2synapse.py config.ini /ldap2synapse/
RUN pip install requests ldap3 python-dotenv pytz
CMD python ./ldap2synapse.py