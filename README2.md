Original Project : Pawpal Starter
The orginal project was used to make tasks for a pet business.
The user would input their name and their pets name then assign what tasks they needed.
Then we were able to add another task and get the whole schedule. If there was a conflict in time the you would get a warning.

-----------New Project-------
Title : What animal is that?
Summary :
The feature added would identify the animal the user wants us to identify.
Architecture Overview:
The user adds the owners name and then they add their pet information. They get information about their pet if the pet is information the app has to get. If there is no information that has that exact pet then they get a generalized answer. They then add a task and if there is any interference they get a warning.
Running app :
To run the app first run the requirements.txt file to download streamlit.
Next run : -m streamlit run app.py
This will run the app and you can see it locally or on your browswer.
Sample Interactions:
I added an owner to it and a pet named Toby which is an Australian Shepherd, it gave some facts about the bread and a generalized message about feeding it and watering it.

Then I added another Owner with a different pet that was a Tortieshell cat and it gave the generalized message about the breed.
Lastly I added a puma and it gave a generized message since it was not a breed that the AI could retrive from RAG.

Design Decisions:
I made it to educate the owner on information about their pet they might not know. I also made it to build a task builder.
Testing Summary:
I tested it with different outputs with output for known breeds and unknown for generalized messages . The tests worked. I wanted to pull an API into the application but went against it because of time contraints.

Reflection:
I learned a lot about how Claude works and what I could expand as features on this project. Because of time contraints I was no able to apply an API pull into my project but in the future this will be a feature I would like to incorporate. I also learned that sometimes you have redifed the promps you ge the AI. This means being really specific about what instructions you give it to do. You do not have to agree to everything the AI does and outputs.
