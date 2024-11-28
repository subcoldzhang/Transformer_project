import logging
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from openai import OpenAI

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = OpenAI(api_key='Your api key')

@app.route("/voice", methods=['POST'])
def voice():
    logger.info("New call received.")
    response = VoiceResponse()
    gather = Gather(input='speech', action='/process_speech', method='POST', timeout=10)
    gather.say('Please say your question, I will transfer it to the intelligent assistant.')
    response.append(gather)
    response.say("I didn't hear anything. Please try again.")
    return str(response)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    speech_text = request.form.get('SpeechResult')
    if speech_text:
        logger.info(f"User speech: {speech_text}")

        if "end" in speech_text.lower():
            twilio_response = VoiceResponse()
            twilio_response.say("Thank you for using our service. Goodbye!")
            twilio_response.hangup()
            logger.info("Call ended by user.")
            return str(twilio_response)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": speech_text}
                ]
            )
            reply_text = response.choices[0].message.content.strip()
            logger.info(f"ChatGPT response: {reply_text}")

            twilio_response = VoiceResponse()
            twilio_response.say(reply_text)

            gather = Gather(input='speech', action='/process_speech', method='POST', timeout=10)
            gather.say('You can ask another question or say "end" to finish the call.')
            twilio_response.append(gather)

            twilio_response.say("If you don't have another question, you can say 'end' to finish the call.")

            return str(twilio_response)
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")
            return str(VoiceResponse().say("An error occurred while processing your request. Please try again."))
    else:
        logger.warning("No speech text received.")
        response = VoiceResponse()
        response.say("Sorry, I didn't hear your question. Please try again.")
        
        gather = Gather(input='speech', action='/process_speech', method='POST', timeout=10)
        gather.say('Please say your question, I will transfer it to the intelligent assistant.')
        response.append(gather)

        response.say("If you don't respond, the call will end automatically. Thank you.")
        
        return str(response)

if __name__ == "__main__":
    logger.info("Starting Flask server...")
    app.run(debug=True, use_reloader=False)

