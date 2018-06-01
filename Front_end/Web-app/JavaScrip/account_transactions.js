function play_loader(){
    $('.loader_container').css({ display: "block" });
    $('body').css({"background-color":"rgba(230,230,230,0.8)"});
}

function stop_loader(){
    $('.loader_container').css({ display: "none" });
    $('body').css({"background-color":"white"});
}

var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

// function  get_account_transactions(bank_id, account_id) {
//     return $.ajax({
//         url: "https://127.0.0.1:5003/aisp/bank/"+bank_id+"/account/"+account_id+"/transactions",
//         method: "GET",
//         data: true,
//         beforeSend: function (xhr) {
//             /* Authorization header */
//             xhr.setRequestHeader("Authorization", getCookie("token"));
//         }
//     });
// }
function  get_account_transactions(bank_id, account_id) {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/bank/"+bank_id+"/account/"+account_id+"/transactions",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function formatDateTime(seconds){
    var date_time = new Date();
    date_time.setTime(seconds);
    return date_time.toUTCString();;
};

function list_account_transactions(account_transactions) {
    $.each(account_transactions, function( key, transaction ) {

       var transaction = "<div class= \"transaction\">\n" +
           "            <div  class=\"description\">\n" +
           "                <p><b>"+transaction.description+"</b></p>\n" +
           "            </div>\n" +
           "            <div   class=\"amount\">\n" +
           "                <p><b>"+transaction.amount+"</b></p>\n" +
           "            </div>\n" +
           "            <div   class=\"status\">\n" +
           "                <p><b>"+transaction.status+"</b></p>\n" +
           "            </div>\n" +
           "            <div   class=\"date\">\n" +
           "                <p><b>"+formatDateTime(transaction.modifiedAt.$date)+"</b></p>\n" +
           "            </div>\n" +
           "            <hr>\n" +
           "        </div>";

        $('#transactions').append(transaction);


    });

}



$(document).ready(function () {
    $("head").append('<link rel="stylesheet" href="../Css/loader.css">');
    $("body").append('<div class="loader_container" style="display: none">');
    $('.loader_container').append('<div class="loader"></div>');

    $.support.cors = true;
    if (verifyLogin() === true) {
        console.log('true')
        var bank_id = getUrlParameter('bank_id');
        var account_id = getUrlParameter('account_id');
        play_loader();
        get_account_transactions(bank_id, account_id).done(function(data) {
            var account_transactions = data.response;
            stop_loader();
            console.log(account_transactions);
            list_account_transactions(account_transactions);
        }).fail(function () {
            alert("Error getting account transactions!!");
            stop_loader();
        })
    }
    else
    {
        console.log('false')
        location.replace('user-login.html')
    }

});
