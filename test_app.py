import os
import tempfile
import pytest
from app import app, db, User, File

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_upload_file(client):
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Create a temporary PDF file for testing
        temp_file.write(b"Test PDF content")
        temp_file.seek(0)

        # Simulate a logged-in user (you may need to adapt this part based on your authentication setup)
        user = User(username='test_user', password='test_password')
        db.session.add(user)
        db.session.commit()

        # Log in and obtain a JWT token (you should adapt this part based on your authentication setup)
        login_response = client.post('/login', json={'username': 'test_user', 'password': 'test_password'})
        jwt_token = login_response.json['access_token']

        # Upload the file using the JWT token
        upload_response = client.post(
            '/upload',
            headers={'Authorization': f'Bearer {jwt_token}'},
            data={'file': (temp_file, 'test.pdf')}
        )

        assert upload_response.status_code == 200
        assert upload_response.json['message'] == 'File uploaded successfully'
        assert 'file_path' in upload_response.json

def test_ask_question(client):
    # Create a test user and file
    user = User(username='test_user', password='test_password')
    db.session.add(user)
    db.session.commit()

    user_file = File(filename='test.pdf', user=user)
    db.session.add(user_file)
    db.session.commit()

    # Log in and obtain a JWT token
    login_response = client.post('/login', json={'username': 'test_user', 'password': 'test_password'})
    jwt_token = login_response.json['access_token']

    # Simulate an example prompt
    prompt_data = {'prompt': 'Test prompt'}

    # Send a POST request to /ask with the JWT token and prompt data
    ask_response = client.post(
        '/ask',
        headers={'Authorization': f'Bearer {jwt_token}'},
        data=prompt_data
    )

    assert ask_response.status_code == 200
    assert 'response' in ask_response.json

if __name__ == '__main__':
    pytest.main()
