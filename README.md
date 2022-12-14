# Tab_User_Provisioner
A standalone Python application that automates user provisioning and decomissioning for Tableau Cloud/Server. The scripts expects a list of "joiners" and "leavers" to be provided and will automatically provising users in the joiners list as unlicensed with [Grant License On Sign In](https://help.tableau.com/current/server/en-us/grant_role.htm) (GLSI) enabled and will unlicense/remove users in the leavers list. 

This implementation stores the "joiners" and "leavers" tables in Snowflake, but this can be overridden by writing your own function to populate the `user_list_to_provision` and `user_list_to_unlicense` lists which are simply a list of email addresses/usernames.
 
# Instructions
[Watch the overview video](https://drive.google.com/file/d/17oLhiwM8GdT2E_eRc8zEZ5FX2r7X5NkG/view?usp=sharing)

**Step 1**

Create 2 tables in your Snowflake Account, one containing the list of users you need to add to your Tableau Cloud/Server site and the other containing the list of users you want to remove. Both of these tables need a field called "Email Address" which will become their Tableau username. 
![image](https://user-images.githubusercontent.com/11485060/207670416-cda823d3-aec6-4458-b25c-16d5394919b3.png)

**Step 2**

Create a Group in Tableau Server/Cloud which will be used to set the minimum site role using the Grant role on sign in feature. The example below uses a group called `Grant_Role_On_Sign_In` which will automatically promote users from unlicenced to a viewer when they first sign in/
![image](https://user-images.githubusercontent.com/11485060/207670781-a0312b92-0882-4c37-a2cf-5d2e9bafaca4.png)

**Step 3**

Run the 

