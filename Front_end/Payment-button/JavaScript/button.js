
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

//Get default payment accont
function get_default_payment_account(token) {
    return $.ajax({
        method: "GET",
        url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        },
    });
}
function get_all_possible_payment_accounts(token) {
    return $.ajax({
        method: "GET",
        url: "https://127.0.0.1:5003/aisp/payment/bank/accounts?amount="+getCookie("amount"),
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        },
    });
}


// Get the transaction charge
function get_charge(token, bank_id, account_id) {
    return $.ajax({
        url: "https://127.0.0.1:5002/pisp/bank/"+bank_id+"/account/"+account_id+"/charge",
        type: "GET",
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization",token);
        }
    })
}

//The transaction is initiated and the result can be the concluded status or initiated all depends the transaction amount
function initiate_transaction(token, bank_id, account_id) {
    var data_serialized = {"amount": getCookie("amount"), "currency": getCookie("currency")};
    console.log(data_serialized);
    return $.ajax({
        type:"POST",
        url: "https://127.0.0.1:5002/pisp/bank/"+bank_id+"/account/"+account_id+"/initiate-transaction-request",
        data:data_serialized,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    })
}

//In case of transaction status is initiated its necessary answer one challenge
function answer_challenge(token, data_serialized, bank_id, account_id) {
    return $.ajax({
        type: "POST",
        url: "https://127.0.0.1:5002/pisp/bank/"+bank_id+"/account/"+account_id+"/answer-challenge",
        data: data_serialized,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    })
}

function account_amount_verification(accounts, bank_id_default , account_id_default) {
    var result = false;
    $.each(accounts, function (key, account) {
        if (bank_id_default === account.bank_id && account_id_default === account.account_id) {
            console.log("entrou");
            result = true;
            return false;
        }
    });
    return result;
}

function purchase(token) {


    get_default_payment_account(token).done(function (data) { //get default payment account
        console.log(data);
        var bank_id = data.response.bank_id;  //bank_id _default
        var account_id = data.response.account_id; //account_id _default
        get_all_possible_payment_accounts(token).done(function (data) { //get all user accounts with enough amount for pay the product
            console.log(data);
            var accounts = data.response;
            if(accounts.length !== 0){  //Check if there is at least one account with money for the purchase
                if(!account_amount_verification(accounts, bank_id, account_id))
                {
                    bank_id = accounts[0].bank_id;
                    account_id = accounts[0].account_id;
                    console.log("não tem dinheiro")
                    var continue_operation =confirm("You do not have enough money in this account to complete the purchase!\n" +
                        "Do you want to pay with the account "+account_id+" of bank "+bank_id+"?");
                    if(!continue_operation) {
                        alert("Purchase was canceled.")
                        return false
                    }
                }
                console.log("passoou")
                get_charge(token, bank_id, account_id).done(function (data) {
                    console.log(data);
                    var continue_operation =confirm("This transaction is subject to a charge of "+data.response.charge+". Do you want to proceed with payment?");
                    if(continue_operation){
                        //initialize the transaction and wait for result
                        initiate_transaction(token, bank_id, account_id).done(function (data) {
                            console.log(data);
                            //If status is initiated is necessary answer the challenge
                            if(data.response.status === "INITIATED"){
                                var continue_operation =confirm("Your purchase is over 1000 €.  Do you want to proceed with payment?");
                                if(continue_operation)
                                {
                                    var data_serialized = {"challenge_query": data.response.challenge.id, "transaction_req_id": data.response.id.value};
                                    answer_challenge(token, data_serialized, bank_id, account_id).done(function (data) {
                                        console.log(data)
                                        if(data.response.status === "COMPLETED"){
                                            alert("Purchase made successfully!")
                                        }
                                        else
                                        {
                                            alert("Some error occurred.")
                                        }
                                    })
                                }
                                else
                                {
                                    alert("Purchase was canceled.");
                                }


                            }
                            //if the transaction status is completed the its done
                            else if(data.response.status === "COMPLETED") {
                                alert("Purchase made successfully!")
                            }
                        })
                    }
                    else
                    {
                        alert("Purchase was canceled.");
                    }

                })
            }
            else
            {
                alert("No account has enough money to purchase in any account.");
            }

        });

    })

}


//end of methods called form popup

$( document ).ready(function() {

    //add button and button css
    $(".productsForm").append('<button onclick="document.getElementById(\'id01\').style.display=\'block\'" type="submit" class = "buyNow" style="vertical-align:middle"><span>Buy Now</span></button>');
    $("head").append($("<link rel='stylesheet' href='css/style.css' type='text/css' media='screen' />"));




    //When user click buy now
	$('.productsForm').submit(function (e) {
        e.preventDefault();
        var values = $(this).serializeArray();

        console.log(values);

        var amount = values[0].value;
        var currency = values[1].value;
        console.log(amount);
        console.log(currency);

        //Save the form values to verify first the user login
        setCookie('amount', amount, 0.01);
        setCookie('currency', currency, 0.01);

    });


    //When the user login
    $('#login-form').submit(function signup(e){
        e.preventDefault();
        $.ajax({
            method: "POST",
            url: "https://127.0.0.1:5001/user/login",
            data: $(this).serializeArray(),
            success: function (data) {
                console.log('Submission was successful.');
                console.log(data);
                $('#id01').css({"display":"none"})
                var continue_operation = confirm("Login successfully. Do you want to proceed with payment?");
                if(continue_operation)
                {
                    purchase(data.response.token); //Success operation, proceed with the payment
                    console.log(data.response.token)
                }
                else
                {
                    alert("Purchase was canceled.");
                }

            },
            error: function (data) {
                $('#error-message').html('O email e/ou password introduzidos estão incorrectos.');
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });

    $('#sing_up').click(function () {
        window.open("./../Web-app/Pages/user-register.html"); //Go to the register form
    });






});