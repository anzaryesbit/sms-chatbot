# sms-chatbot
SMS Chatbot that's connected with the Twilio API to get feedback through guided responses

Chatbot reads JSON data from Twilio API in order to interpret user feedback data. In order to return a message, a return statement formated in XML is given in the lambda function. However, for this data to reach the phone user and for the lambda function to be notified a user has messaged it, a REST API Gateway is created as a webhook. This API Gateway handles the passing of information to and from the user to the backend database.

For more information about setting up the API Gateway, the following article is helpful: https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python-amazon-lambda
