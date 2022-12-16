# Tab_User_Provisioner
A standalone Python application that automates user provisioning and removal for Tableau Cloud/Server. The scripts expects a list of "joiners" and "leavers" to be provided and will automatically provision users in the joiners list as unlicensed with [Grant License On Sign In](https://help.tableau.com/current/server/en-us/grant_role.htm) (GLSI) enabled and will unlicense/remove users in the leavers list. 

This implementation expects the "joiners" and "leavers" to be sourced from tables in Snowflake, but this can be overridden by writing your own function to populate the `user_list_to_provision` and `user_list_to_unlicense` lists containing a list of email addresses/usernames.
 
# Instructions
[Watch the overview video](https://drive.google.com/file/d/17oLhiwM8GdT2E_eRc8zEZ5FX2r7X5NkG/view?usp=sharing)

**Step 1**

Create 2 tables in your Snowflake Account, one containing the list of users you need to add to your Tableau Cloud/Server site and the other containing the list of users you want to remove. Both of these tables need a field called "Email Address" which will become their Tableau username. 
![image](https://user-images.githubusercontent.com/11485060/207670416-cda823d3-aec6-4458-b25c-16d5394919b3.png)

**Step 2**

Create a Group in Tableau Server/Cloud which will be used to set the minimum site role using the Grant role on sign in feature. The example below uses a group called `Grant_Role_On_Sign_In` which will automatically promote users from unlicenced to a viewer when they first sign in.
![image](https://user-images.githubusercontent.com/11485060/207670781-a0312b92-0882-4c37-a2cf-5d2e9bafaca4.png)

**Step 3**

Ensure you have a working python 3.x installation with the following packages installed:

`pip install tableauserverclient`

`pip install pyyaml`

`pip install cryptoyaml`

`pip install snowflake-connector-python`

**Step 4**

Configure the `settings.yaml` file with the parameters for your environment including your Tableau Cloud/Server credentials, Snowflake credentials, app and email notification settings:
![image](https://user-images.githubusercontent.com/11485060/208118342-f8a23fd0-3921-40f3-b7c7-d416829b9730.png)

**Step 5**

Run the application using the command:

`python main.py`

A successfull run should result in a series of INFO messages being written to the console and a new log file being generated in the `./logs` directory:
![image](https://user-images.githubusercontent.com/11485060/208119293-1dedeb9d-164f-488d-be9f-3a13092b1064.png)

**Step 6**

Review the log file to identify any `ERROR` entries corresponding to users who were not succesfully added/unlicensed/removed from Tableau Cloud/Server. Note that log files are retained for the period defined by the `LOG RETENTION` variable in the `settings.yaml` configuration file.
![image](https://user-images.githubusercontent.com/11485060/208119863-4eeb283a-fb6f-4850-94c0-064693cf5407.png)


**Step 7**

If `EMAIL_NOTIFICATIONS` is set to `True` in the `settings.yaml` configuration file then in the event of an error an email will be automatically be sent with the log file attached for review to the email address(es) listed in the `EMAIL_TO` variable:
![image](https://user-images.githubusercontent.com/11485060/208120691-e9d13abb-3f83-4e15-9975-f9bd2712779a.png)


**Step 8 (Optional)**

In order to securely encrypt the credentials stored in the `settings.yaml` file you can optionally generate an encrypted version by running the command:

`python encrypt_yaml.py`

This will generate the files:

`settings.yaml.aes`: encrypted copy of `settings.yaml`

`key`: the key file to decrypt `settings.yaml.aes`

You can now delete/move `settings.yaml` and run the application. 

To store the key file in an alternative location you will need to set the `CRYPTOYAML_SECRET` environment variable as per the cryptoyaml documentation [here](https://pypi.org/project/cryptoyaml/)
![image](https://user-images.githubusercontent.com/11485060/208121700-c4e2bbcb-1d78-429b-89b8-5786e52e9df3.png)







