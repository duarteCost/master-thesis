function get_default_payment_account(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_default_payment_account(){
    return $.ajax({
        url: "https://127.0.0.1:5003/aisp/payment/bank/account/default",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function get_current_account() {
    return $.ajax({
        url: "https://127.0.0.1:5001/user/account",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_current_account() {
    return $.ajax({
        url: "https://127.0.0.1:5001/user/account",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function get_transactions() {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/transactions",
        method: "GET",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

function delete_transactions() {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/transactions",
        method: "DELETE",
        data: true,
        beforeSend: function (xhr) {
            /* Authorization header */
            xhr.setRequestHeader("Authorization", getCookie("token"));
        }
    });
}

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

function  search_transactions(search_params) {
    return $.ajax({
        url: "https://127.0.0.1:5004/transactions_record/search",
        method: "POST",
        data: search_params,
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
    var transactions_rows = "";
    $.each(account_transactions, function( key, transaction ) {

        transactions_rows += "<div  class= \"transaction\">\n" +
            "            <div  class=\"description\">\n" +
            "                <p>"+transaction.description+"</p>\n" +
            "            </div>\n" +
            "            <div   class=\"amount\">\n" +
            "                <p>"+transaction.amount+"</p>\n" +
            "            </div>\n" +
            "            <div   class=\"status\">\n" +
            "                <p>"+transaction.status+"</p>\n" +
            "            </div>\n" +
            "            <div   class=\"merchant\">\n" +
            "                <p>"+transaction.merchant+"</p>\n" +
            "            </div>\n" +
            "            <div   class=\"date\">\n" +
            "                <p>"+formatDateTime(transaction.modifiedAt.$date)+"</p>\n" +
            "            </div>\n" +
            "            <hr>\n" +
            "        </div>";
        //$('#transactions_body').empty();
    });
    $('#transactions_body').empty();
    $('#transactions_body').append(transactions_rows);

}

function add_accounts_select_input(accounts) {
    $.each(accounts, function( key, account ) {
        $('#account_id_id').append($('<option>', {
            value: account.account_id,
            text : account.account_id
        }));
    });
}

function exportToFile(data){

    var hiddenElement = document.createElement('a');
    hiddenElement.href = 'data:text/json;filename=exportar.json;charset=utf-8,' + JSON.stringify(data, null, 4);
    hiddenElement.target = '_blank';
    hiddenElement.download = 'user_data.json';
    hiddenElement.click();
}

function search() {
    var account_id = $('#account_id_id').val();
    var begin_date = $('#begin_date_id').val();
    var end_date = $('#end_date_id').val();
    var search_params = {"account_id": account_id, "begin_date": begin_date, "end_date":end_date};
    search_transactions(search_params).done(function (data) {
        console.log(data);
        list_account_transactions(data.response);
    });
}

$(document).ready(function () {

    $.support.cors = true;
    if (verifyLogin() === true) {
        play_loader();
        get_bank_accounts().done(function (accounts) {
            add_accounts_select_input(accounts.response);
            stop_loader();
        });

        get_transactions().done(function(data) {
            var account_transactions = data.response;
            list_account_transactions(account_transactions);
        }).fail(function () {
            alert("Error getting account transactions!!");
            stop_loader();
        });


        $('#account_id_id').change(function () {
            search();
        });

        $('#begin_date_id').change(function () {
            search();
        });

        $('#end_date_id').change(function () {
            search();
        });

        $('#remove-user-data').click(function () {
            play_loader();
            delete_transactions().done(function () {
                delete_default_payment_account().done(function () {
                    delete_current_account().done(function () {
                        stop_loader();
                        Alert("Success", "User data deleted successfully.").done(function () {
                            location.replace('user-login.html');
                        });
                    });
                }).fail(function () {
                    stop_loader();
                    Alert("Error", "Error deleting user data.");
                });
            }).fail(function () {
                stop_loader();
                Alert("Error", "Error deleting user data.");
            }).fail(function () {
                stop_loader();
                Alert("Error", "Error deleting user data.");
            });
        });

        $('#export-user-data').click(function (e) {
            e.preventDefault();
            play_loader();
            var user_data = {};
            get_current_account().done(function (data) {
                delete data['obp_authorization'];
                user_data['user'] = data;
                get_default_payment_account().done(function (data) {
                    user_data['default_payment_account'] = data.response;
                    get_transactions().done(function (data) {
                        user_data['transactions'] = data.response;
                        exportToFile(user_data);
                        stop_loader();
                        Alert("Success", "User data exported successfully.");

                    }).fail(function () {
                        stop_loader();
                        Alert("Error", "Error exporting user data.");
                    });
                }).fail(function () {
                    stop_loader();
                    Alert("Error", "Error exporting user data.");
                });
            }).fail(function () {
                stop_loader();
                Alert("Error", "Error exporting user data.");
            });
        });


    }
    else
    {
        location.replace('user-login.html')
    }




});