# Deck Take-Home Assignment

## Installing and Running the Project
1. Navigate to the root directory
2. Create a .env file at the root, add the following text and save the file
   
```
USERNAME=admin
PASSWORD=password123
MFACODE=123456
HEADLESS=False
```
3. Create and activate a virtual environment: ```python3 -m venv venv``` then ```source venv/bin/activate```
4. Install dependencies ```pip install -r requirements.txt```
5. Run the tests by running ```pytest ./src/tests -v```
6. The tests will run with ```headless=False``` to demonstrate the process
7. This may take a few secondsx
