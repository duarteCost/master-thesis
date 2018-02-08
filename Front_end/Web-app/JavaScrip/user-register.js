$(document).ready(function(){
    $.support.cors = true;

    //Register Form Handler
    $('#register-form').submit(function signup(e){
        e.preventDefault();
        if(!validateEmail() || !validatePassword()){
            console.log("Account information invalid")
            return;
        }
        $.ajax({
            method: "POST",
            url: "http://127.0.0.1:5001/user/register",
            data: $(this).serializeArray(),
            success: function (data) {
                console.log('Submission was successful.');
                console.log(data);
                location.replace('user-login.html')
            },
            error: function (data) {
                $('#error-message').html(data.response);
                console.log('An error occurred.');
                console.log(data);
            }
        })
    });
});

