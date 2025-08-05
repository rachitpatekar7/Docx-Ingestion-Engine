# chatbot.py

import random

class Chatbot:
    def __init__(self):
        self.responses = {
            "greeting": ["Hello! How can I assist you today?", "Hi there! What do you need help with?", "Greetings! How may I help you?"],
            "farewell": ["Goodbye! Have a great day!", "See you later!", "Take care!"],
            "help": ["I can assist you with various tasks. What do you need help with?", "Feel free to ask me anything!"],
        }

    def get_response(self, intent):
        if intent in self.responses:
            return random.choice(self.responses[intent])
        else:
            return "I'm sorry, I didn't understand that."

    def chat(self):
        print("Chatbot is ready to assist you. Type 'exit' to end the chat.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            # Simple intent recognition
            if "hello" in user_input.lower() or "hi" in user_input.lower():
                print("Chatbot:", self.get_response("greeting"))
            elif "bye" in user_input.lower() or "goodbye" in user_input.lower():
                print("Chatbot:", self.get_response("farewell"))
                break
            elif "help" in user_input.lower():
                print("Chatbot:", self.get_response("help"))
            else:
                print("Chatbot: I'm sorry, I didn't understand that.")

if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.chat()