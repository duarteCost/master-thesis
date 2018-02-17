
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

// Get the transaction charge
function getCharge(token) {
    return $.ajax({
        type: "GET",
        url:"https://127.0.0.1:5002/ob/payment/charge" ,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    })
}

//The transaction is initiated and the result can be the concluded status or initiated all depends the transaction amount
function initiate_transaction(token) {
    var data_serialized = {"amount": getCookie("amount"), "currency": getCookie("currency")};
    console.log(data_serialized);
    return $.ajax({
        type:"POST",
        url: "https://127.0.0.1:5002/ob/payment/initiate-transaction-request",
        data:data_serialized,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    })
}

//In case of transaction status is initiated its necessary answer one challenge
function answer_challenge(token, data_serialized) {
    return $.ajax({
        type: "POST",
        url: "https://127.0.0.1:5002/ob/payment/answer-challenge",
        data: data_serialized,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    })
}

function purchase(token) {

    //first get charge and wait for the conclusion of operatio
    getCharge(token).done(function (data) {
        console.log(data);
        var continue_operation =confirm("This transaction is subject to a charge of "+data.response.charge+". Do you want to proceed with payment?");
        if(continue_operation){
            //initialize the transaction and wait for result
            initiate_transaction(token).done(function (data) {
                console.log(data);
                //If status is initiated is necessary answer the challenge
                if(data.response.status === "INITIATED"){
                    var continue_operation =confirm("Your purchase is over 1000 €.  Do you want to proceed with payment?");
                    if(continue_operation)
                    {
                        var data_serialized = {"challenge_query": data.response.challenge.id, "transaction_req_id": data.response.id.value};
                        answer_challenge(token, data_serialized ).done(function (data) {
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
                    purchase(data.token); //Success operation, proceed with the payment
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