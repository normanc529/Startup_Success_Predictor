### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Intents Handlers ###
def approve_loan(intent_request):
    """
    Performs dialog management and fulfillment for approving a loan.
    """

    first_name = get_slots(intent_request)["firstName"]
    company_age = get_slots(intent_request)["companyAge"]
    last_funding = get_slots(intent_request)["lastFunding"]
    loan_amount = get_slots(intent_request)["loanAmount"]
    source = intent_request["invocationSource"]
    
    if source == "DialogCodeHook":
        slots = get_slots(intent_request)
        validation_result = validate_data(company_age, last_funding, intent_request)
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
                )
        output_session_attribute = intent_request["sessionAttributes"]
        return delegate(output_session_attribute, get_slots(intent_request))
    initial_recommendation = get_approval(loan_amount)
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} thank you for your information;
            based on the information you provided, our lending decision is as follows: {}
            """.format(
                first_name, initial_recommendation
            ),
        },
    )

def validate_data(company_age, last_funding, intent_request):
    if company_age is not None:
        company_age = parse_int(
            company_age
            )
        if company_age < 2:
            return build_validation_result(
                False,
                "companyAge",
                "Your startup must be established for a minimum of 2 years in order to qualify."
                )
        elif company_age >10:
            return build_validation_result(
                False,
                "companyAge",
                "Your startup cannot be older than 10 years."
                )
    if last_funding is not None:
        last_funding = parse_int(last_funding)
        if last_funding < 100000:
            return build_validation_result(
                False,
                "lastFunding",
                "You must have received a minimum of $100000 in your previous funding to qualify. "
            )
    return build_validation_result(True, None, None)

def get_approval(loan_amount):
    """
    Returns a lending decision based on the user input.
    """
    loan_amounts = {
        "under 50k": "Our minimum funding amount is $50k",
        "50-250k": "Congrats you're pre-approved! Our startup analyst will be contacting you within 24 hours to collect additional information.",
        "over 250k": "Our max funding amount is $250k",
    }
    
    return loan_amounts[loan_amount.lower()]


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "PredictSuccess":
        return approve_loan(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    return dispatch(event)