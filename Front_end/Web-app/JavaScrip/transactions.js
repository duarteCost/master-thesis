function get_bank_accounts(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/bank/accounts",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}


function play_loader(){
    $('.loader_container').css({ display: "block" });
    $('body').css({"background-color":"rgba(230,230,230,0.8)"});
}

function stop_loader(){
    $('.loader_container').css({ display: "none" });
    $('body').css({"background-color":"white"});
}


function list_bank_accounts(accounts) {

    console.log(accounts)
    var form_id = 0;
    $('#bank_accounts').empty();
    $("#bank_accounts").append("<h3><label>Choose one of the following bank accounts to see the transactions!</label></h3>");
    $("#bank_accounts").append("<br>");
    $("#bank_accounts").append("<br>");
    $.each(accounts, function( key, account ) {
        form_id ++;
        $("#bank_accounts").append("<li style='background-color: #333; color:rgb(246,255,255);'><label>Account</label></li>");
        $("#bank_accounts").append("<li><label>Bank_id:<span class='span-customized'>"+' '+account.bank_id+"</span></label></li>");
        $("#bank_accounts").append("<li><label>Account_id:<span class='span-customized'>"+' '+account.account_id+"</span></label></li>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<form id = '"+form_id+"' class='update_default_payment_account'>");
        $("#"+form_id).append("<input class='bank_id' type='hidden' name='bank_id' value='"+account.bank_id+"'>");
        $("#"+form_id).append("<input class='account_id' type='hidden' name='account_id' value='"+account.account_id+"'>");
        $("#"+form_id).append("<button type='submit' class='btn choose_account' type='button'>Choose</button>")
        $("#bank_accounts").append("</form>");
        $("#bank_accounts").append("<br>");
        $("#bank_accounts").append("<br>");

    });

}


$(document).ready(function () {
    $("head").append('<link rel="stylesheet" href="../Css/loader.css">');
    $("body").append('<div class="loader_container" style="display: none">')
    $('.loader_container').append('<div class="loader"></div>')

    $.support.cors = true;
    if (verifyLogin() === true) {
        console.log('true')
        play_loader();
        get_bank_accounts().done(function(data) {
            var accounts = data.response;
            stop_loader();
            list_bank_accounts(accounts);
        }).fail(function () {
            alert("Error getting bank accounts!!")
            stop_loader();
        })
    }
    else
    {
        console.log('false')
        location.replace('user-login.html')
    }

    $('#bank_accounts').on('submit', '.update_default_payment_account', function (e) {
        e.preventDefault();
        var bank_id = $('.bank_id', this).val();
        var account_id = $('.account_id', this).val();
        location.replace('account_transactions.html?bank_id='+bank_id+'&account_id='+account_id)
    })
});

