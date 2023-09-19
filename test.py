import unittest
import json
from app import app  # Import your Flask app

class TestYourFlaskApp(unittest.TestCase):

    def setUp(self):
        # Create a test client for the Flask app
        self.app = app.test_client()
        self.app.testing = True

    def test_ask_question(self):
        # Define the test data (JSON payload)
        test_data = {'prompt': 'what is the message for investors/stake holders'}

        # Send a POST request to the '/ask' route with the test data
        response = self.app.post('/ask', json=test_data)  # Use json parameter to send JSON data

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        data = json.loads(response.data)
        self.assertIn('response', data)  # Check if 'response' key is in the response JSON

        # You can add more specific assertions based on the expected response

if __name__ == '__main__':
    unittest.main()
