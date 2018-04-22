function verify_login() {
        if (!verifyLogin()) {
            return false;
        }
        else
        {
            return true;
        }
}

$(document).ready(function () {
    $.support.cors = true;
    if(verify_login() === true) {
        $.ajax({
            method: "GET",
            url: "https://127.0.0.1:5001/user/account/obp/authorization",
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                location.replace('aisp.html');
            },
            error: function (data) {
                console.log(data);
                if (data.responseJSON != undefined) {
                    if (data.responseJSON.obp_authorization === "NULL") {
                        $('#associate_ob_account').css({"display": "block"});
                    }
                    else {
                        alert(data.responseJSON.response);
                        location.replace('index.html')
                    }
                }
                else {
                    alert("Our server is unavailable. Try access later!");
                    location.replace('index.html')
                }
            }
        });
    }
    else
    {
        location.replace('user-login.html')
    }


    //Register Form Handler
    $('#open-bank-register-form').submit(function signup(e){
        e.preventDefault();

        if(!validatePassword()){
            console.log("Account information invalid")
            $('#open_bank_error_message').html("Passwords does not match.");
            return;
        }
        $.ajax({
            method: "POST",
            url: "https://127.0.0.1:5001/user/obp/associate",
            data: $(this).serializeArray(),
            beforeSend: function (xhr) {
                /* Authorization header */
                xhr.setRequestHeader("Authorization", getCookie("token"));
            },
            success: function (data) {
                console.log('Submission was successful.');
                console.log(data);
                alert("Your Open Bank Account has been successfully associated with your Nearsoft Payment Provider account!");
                location.replace('open-bank-association.html')
            },
            error: function (data) {
                $('#open_bank_error_message').html(data.responseJSON.response);
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });
});