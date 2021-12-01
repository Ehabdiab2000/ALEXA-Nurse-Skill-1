from config import config
from ask_sdk_model.dialog import ElicitSlotDirective
from ask_sdk_model import (
    Intent, IntentConfirmationStatus, Slot, SlotConfirmationStatus)

from db import DynamoDBLayer
from datetime import date
import pytz
from datetime import datetime



class CommonFunctions:

    def initAttributes(self, handler_input):
        sessionAttributes = handler_input.attributes_manager.session_attributes
        if not sessionAttributes.keys():
            sessionAttributes['skill_state'] = 'INITIAL'
            sessionAttributes['user_name'] = ""
            sessionAttributes['complain'] = ""
            sessionAttributes['doctor_name'] = ""
            sessionAttributes['specialty'] = ""
        messages = config['MESSAGES']
        responseData = {
            "speechOutput": "",
            "reprompt": "",
            "endSession": False
        }
        output = {
            "responseData": responseData,
            "sessionAttributes": sessionAttributes,
            "messages": messages
        }
        return output

    def sendResponseToAlexa(self, handler_input, responseData, sessionAttributes):
        updateAttributes(self, handler_input, sessionAttributes)
        return (
            handler_input.response_builder.speak(responseData['speechOutput'])
            .set_should_end_session(responseData['endSession'])
            .ask(responseData['reprompt'])
            .response
        )
    
    def sendStopResponseToAlexa(self, handler_input, responseData, sessionAttributes):
        updateAttributes(self, handler_input, sessionAttributes)
        return (
            handler_input.response_builder.speak(responseData['speechOutput'])
            .set_should_end_session(True)
            .response
        )

    def sendElictSlotResponseToAlexa(self, handler_input, responseData, sessionAttributes):
        directive = ElicitSlotDirective(
        slot_to_elicit="name",
        updated_intent=Intent(
            name="NameIntent",
            confirmation_status=IntentConfirmationStatus.NONE,
            slots={
                    "name": Slot(
                        name="name",
                        confirmation_status=SlotConfirmationStatus.NONE)
                }
            )
        )
        return(
            handler_input.response_builder.speak(responseData['speechOutput'])
            .set_should_end_session(responseData['endSession'])
            .ask(responseData['reprompt'])
            .add_directive(directive)
            .response
        )

    def bookAppointment(sessionAttributes, doctor):
        userName = sessionAttributes['user_name']
        getDoctorAppointment = DynamoDBLayer.getDoctorAppointment(doctor)
        today = todayDate()
        if getDoctorAppointment['Count'] == 0:
            next_appointment = config['DOCTIOR_APPOINMENTS'][doctor][0]
        else:
            next_appointment = getDoctorAppointment['Items'][0]['next_appointment']
            last_updated = getDoctorAppointment['Items'][0]['last_updated']
            if int(next_appointment) == 0:
                if last_updated == today:
                    bookAppointment = {
                        'status' : False
                    }
                    return bookAppointment
                else:
                    next_appointment = config['DOCTIOR_APPOINMENTS'][doctor][0]         
        complain = sessionAttributes['complain'] 
        specialty = sessionAttributes['specialty']
        userName = sessionAttributes['user_name']
        appointment_time =  getAppointmentValidTime(int(next_appointment), doctor)
        if(appointment_time == 0 or appointment_time == '0'):
            bookAppointment = {
                'status' : False
            }
            return bookAppointment
        appointment_time_format = appointment_time + ":00"
        putAppointment = DynamoDBLayer.putAppointment(doctor, userName, specialty, complain, appointment_time_format)
        if int(appointment_time) + 1 in config['DOCTIOR_APPOINMENTS'][doctor]:
            next_appointment = int(appointment_time) + 1
            putAppointmentsInArray = DynamoDBLayer.putNextAppointment(doctor, next_appointment, today)
        else:
            putAppointmentsInArray = DynamoDBLayer.putNextAppointment(doctor, 0, today)
        bookAppointment = {
            'status' : True,
            'time' : appointment_time_format,
            'result' : putAppointment
        }
        return bookAppointment

  
def updateAttributes(self, handler_input, sessionAttributes):
    handler_input.attributes_manager.session_attributes = sessionAttributes
    # handler_input.attributes_manager.save_persistent_attributes()
    return

def todayDate():
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    return str(d1)

def getAppointmentValidTime(next_appointment, doctor):
    cureentTime = pytz.timezone('Asia/Dubai')
    cureentTimeFormat = datetime.now(cureentTime)
    currentHour = cureentTimeFormat.hour;
    if(next_appointment > currentHour):
        return str(next_appointment)
    else:
        if int(currentHour) + 1 in config['DOCTIOR_APPOINMENTS'][doctor]:
            return str(int(currentHour) + 1)
        else:
            return 0
    