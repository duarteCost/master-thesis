
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


function purchase(token) {



    $.ajax({
        type: "GET",
        url:"http://127.0.0.1:5002/ob/payment/charge" ,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", token);
        }
    }).done(function (data) {
        console.log(data)
        alert("This transaction is subject to a fee of: "+data.response.charge);
        var data_serialized = {"amount": getCookie("amount"), "currency": getCookie("currency")}
        console.log(data_serialized)
        $.ajax({
            type:"POST",
            url: "http://127.0.0.1:5002/ob/payment/initiate-transaction-request",
            data:data_serialized,
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", token);
            }
        }).done(function (data) {
            console.log(data);
            if(data.response.status === "INITIATED"){
                alert("Your purchase is over 1000 €. Do you wish to continue?")
                var dataSerialized = {"challenge_query": data.response.challenge.id, "transaction_req_id": data.response.id.value}
                $.ajax({
                    type: "POST",
                    url: "http://127.0.0.1:5002/ob/payment/answer-challenge",
                    data: dataSerialized,
                    beforeSend: function (xhr) {
                        /* Authorization header */
                        xhr.setRequestHeader("Authorization", token);
                    }
                }).done(function (data) {
                    console.log(data)
                    if(data.response.status == "COMPLETED"){
                        alert("Purchase made successfully")
                    }
                    else
                    {
                        alert("Some error occurred")
                    }
                })

            }
            else if((data.response.status == "COMPLETED")) {
                alert("Purchase made successfully")
            }
        })
    })
}


//end of methods called form popup

$( document ).ready(function() {

    $(".productsForm").append('<button onclick="document.getElementById(\'id01\').style.display=\'block\'" type="submit" class = "buyNow" style="vertical-align:middle"><span>Buy Now</span></button>');


    $("head").append($("<link rel='stylesheet' href='css/style.css' type='text/css' media='screen' />"));




	$('.productsForm').submit(function (e) {
        e.preventDefault();
        var values = $(this).serializeArray();

        console.log(values);

        var amount = values[0].value;
        var currency = values[1].value;
        console.log(amount);
        console.log(currency);

        setCookie('amount', amount, 0.001);
        setCookie('currency', currency, 0.001);

    });


    $('#login-form').submit(function signup(e){
        e.preventDefault();
        $.ajax({
            method: "POST",
            url: "http://127.0.0.1:5001/user/login",
            data: $(this).serializeArray(),
            success: function (data) {
                console.log('Submission was successful.');
                console.log(data);
                $('#id01').css({"display":"none"})
                purchase(data.token)
            },
            error: function (data) {
                $('#error-message').html('O email e/ou password introduzidos estão incorrectos.');
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });






});