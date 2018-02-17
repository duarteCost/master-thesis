# PISP payment initiation service providers
This project is Payment Service Provider using PSD2

## Requirements

1. MongoDB
2. Python Flasks
3. Web browser 

## How to run
Below I will explain how to run the project
### BackEnd
1. Fill the configurations files of each one Service
    1. The default variables in all files is about the Services IP address, probably it is not necessary change
    2. In the OB_Service the OB variables is about Open Bank API it is not necessary change
2. Run MongoDB with the command **mongod --dbpath _YOURDESIREDPATH_**
3. **Run all of Services** (attention the default HTTP ports is defined in code)
### FrontEnd
1. Go to the Front_end/Payment-button/e-coomerce-website-test.html
2. Open it with web browser

## How to use
1. In the FrontEnd page, when **click in "Buy Now"** button will appear one login window
2. In this window **if the user does not have account** must Sign Up on "Sign Up her" link
3. Then the user must **fill the Sign Up form** and submit
4. After that will appear a login window, the **user must login with the Sign Up credentials**
5. When logged in the user will see one page that is possible associate yours Open Bank PSD2 SandBox Account 
    1. **Case the user does not have Open Bank PSD2 SandBox Account** must Sign Up here [Open Bank PSD2 SandBox - Sing Up](https://psd2-api.openbankproject.com/user_mgt/sign_up)
    2. After Signed Up the user must be **create one bank account** 
6. Now, the user must be **fill the association form** with Open Bank PSD SandBox credentials
7. In this moment the system have authorization to do payments for that user
8. Now, do it again the **first step** and fill the login form with the credentials of the **step 3** registry
9. Good shoppings :)

