import os
import boto3
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from commons import CommonFunctions
from config import config

ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')

ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        responseData['speechOutput'] = messagesData['WELCOME']
        responseData['reprompt'] = messagesData['WELCOME_REPROMPT']
        sessionAttributes['skill_state'] = "GET_NAME"
        return CommonFunctions.sendElictSlotResponseToAlexa(self, handler_input, responseData, sessionAttributes)


class CaptureNameIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("NameIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        if sessionAttributes['skill_state'] != 'GET_NAME':
            responseData['speechOutput'] = messagesData['WELCOME_WITH_NAME']
            responseData['reprompt'] = messagesData['WELCOME_REPROMPT']
            return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        slots = handler_input.request_envelope.request.intent.slots
        name = slots["name"].value
        sessionAttributes['skill_state'] = "ASK_FOR_DOCTOR"
        sessionAttributes['user_name'] = name
        responseData['speechOutput'] = messagesData['WELCOME_WITH_NAME'].replace(
                '#NAME#', name)
        responseData['reprompt'] = messagesData['WELCOME_WITH_NAME_REPROMPT']
        return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        if sessionAttributes['skill_state'] != 'ASK_FOR_DOCTOR':
            responseData['speechOutput'] = messagesData['FALLBACK_MESSAGE']
            responseData['reprompt'] = messagesData['ASK_FOR_WHICH_DOCTOR_REPROMPT']
            return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        responseData['speechOutput'] = messagesData['ASK_FOR_WHICH_DOCTOR']
        responseData['reprompt'] = messagesData['ASK_FOR_WHICH_DOCTOR_REPROMPT']
        return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        if sessionAttributes['skill_state'] != 'ASK_FOR_DOCTOR':
            responseData['speechOutput'] = messagesData['FALLBACK_MESSAGE']
            responseData['reprompt'] = messagesData['ASK_FOR_COMPLAIN_REPROMPT']
            return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        responseData['speechOutput'] = messagesData['ASK_FOR_COMPLAIN']
        responseData['reprompt'] = messagesData['ASK_FOR_COMPLAIN_REPROMPT']
        return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class ComplainIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ComplainIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        slots = handler_input.request_envelope.request.intent.slots
        complain = slots["complain"].value
        doctor = config['COMPLAIN'][complain]
        sessionAttributes['complain'] = complain
        bookAppointment = CommonFunctions.bookAppointment(sessionAttributes, doctor)
        if bookAppointment['status'] == True:
            responseData['speechOutput'] = messagesData['BOOK_APPOINTMENT'].replace(
                '#TIME#', bookAppointment['time']).replace(
                '#DOCTOR_NAME#', doctor  
                )
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        else:
            responseData['speechOutput'] = messagesData['DOCTOR_NOTAVAILABLE']
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class DoctorIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("DoctorIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        slots = handler_input.request_envelope.request.intent.slots
        doctor = slots["doctor"].value
        doctor = doctor.upper()
        bookAppointment = CommonFunctions.bookAppointment(sessionAttributes, doctor)
        if bookAppointment['status'] == True:
            responseData['speechOutput'] = messagesData['BOOK_APPOINTMENT'].replace(
                '#TIME#', bookAppointment['time']).replace(
                '#DOCTOR_NAME#', doctor  
                )
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        else:
            responseData['speechOutput'] = messagesData['DOCTOR_NOTAVAILABLE']
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class SpecialityIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SpecialityIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        slots = handler_input.request_envelope.request.intent.slots
        speciality = slots["speciality"].value
        doctor = config['SPECIALITY'][speciality]
        sessionAttributes['specialty'] = speciality
        bookAppointment = CommonFunctions.bookAppointment(sessionAttributes, doctor)
        if bookAppointment['status'] == True:
            responseData['speechOutput'] = messagesData['BOOK_APPOINTMENT'].replace(
                '#TIME#', bookAppointment['time']).replace(
                '#DOCTOR_NAME#', doctor  
                )
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)
        else:
            responseData['speechOutput'] = messagesData['DOCTOR_NOTAVAILABLE']
            return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        responseData['speechOutput'] = messagesData['HELP']
        responseData['reprompt'] = messagesData['HELP_REPROMPT']
        return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        responseData['speechOutput'] = messagesData['STOP']
        responseData['endSession'] = True
        return CommonFunctions.sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        initJson = CommonFunctions.initAttributes(self, handler_input)
        responseData = initJson['responseData']
        sessionAttributes = initJson['sessionAttributes']
        messagesData = initJson['messages']
        responseData['speechOutput'] = messagesData['FALLBACK_MESSAGE']
        responseData['reprompt'] = messagesData['FALLBACK_MESSAGE']
        return CommonFunctions.sendResponseToAlexa(self, handler_input, responseData, sessionAttributes)

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):   
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


sb = sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CaptureNameIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(DoctorIntentHandler())
sb.add_request_handler(ComplainIntentHandler())
sb.add_request_handler(SpecialityIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) 

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()